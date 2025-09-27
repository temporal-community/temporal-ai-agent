#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-api.anthropic.com}"
ANCHOR_NAME="anthropic"
ANCHOR_FILE="/etc/pf.anchors/${ANCHOR_NAME}"
PF_CONF="/etc/pf.conf"

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Please run with sudo." >&2
    exit 1
  fi
}

backup_once() {
  local file="$1"
  if [ -f "$file" ] && [ ! -f "${file}.bak" ]; then
    cp -p "$file" "${file}.bak"
  fi
}

ensure_anchors_dir() {
  if [ ! -d "/etc/pf.anchors" ]; then
    mkdir -p /etc/pf.anchors
    chmod 755 /etc/pf.anchors
  fi
}

ensure_anchor_hook() {
  if ! grep -qE '^\s*anchor\s+"'"${ANCHOR_NAME}"'"' "$PF_CONF"; then
    echo "Wiring anchor into ${PF_CONF}..."
    backup_once "$PF_CONF"
    {
      echo ''
      echo '# --- Begin anthropic anchor hook ---'
      echo 'anchor "'"${ANCHOR_NAME}"'"'
      echo 'load anchor "'"${ANCHOR_NAME}"'" from "/etc/pf.anchors/'"${ANCHOR_NAME}"'"'
      echo '# --- End anthropic anchor hook ---'
    } >> "$PF_CONF"
  fi
}

default_iface() {
  route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}'
}

resolve_ips() {
  (dig +short A "$HOST"; dig +short AAAA "$HOST") 2>/dev/null \
    | awk 'NF' | sort -u
}

write_anchor_allow() {
  local iface="$1"; shift
  local ips=("$@")

  local table_entries=""
  if [ "${#ips[@]}" -gt 0 ]; then
    for ip in "${ips[@]}"; do
      if [ -n "$ip" ]; then
        if [ -z "$table_entries" ]; then
          table_entries="$ip"
        else
          table_entries="$table_entries, $ip"
        fi
      fi
    done
  fi

  backup_once "$ANCHOR_FILE"
  {
    echo "# ${ANCHOR_FILE}"
    echo "# Auto-generated: $(date)"
    echo "# Host: ${HOST}"
    echo "table <anthropic> persist { ${table_entries} }"
    echo ""
    echo "# Allow outbound traffic to Anthropic"
    echo "pass out quick on ${iface} to <anthropic>"
  } > "$ANCHOR_FILE"
}

enable_pf() {
  pfctl -E >/dev/null 2>&1 || true
}

reload_pf() {
  if ! pfctl -nf "$PF_CONF" >/dev/null 2>&1; then
    echo "pf.conf validation failed. Aborting." >&2
    exit 1
  fi
  pfctl -f "$PF_CONF" >/dev/null
}

main() {
  require_root
  ensure_anchors_dir

  local iface
  iface="$(default_iface || true)"
  if [ -z "${iface:-}" ]; then
    echo "Could not determine default network interface." >&2
    exit 1
  fi

  ensure_anchor_hook

  ips=()
  while IFS= read -r ip; do
    ips+=("$ip")
  done < <(resolve_ips)

  if [ "${#ips[@]}" -eq 0 ]; then
    echo "Warning: No IPs resolved for ${HOST}. The table will be empty." >&2
  fi

  write_anchor_allow "$iface" "${ips[@]}"
  enable_pf
  reload_pf

  echo "✅ Anthropic API is now ALLOWED via pf on interface ${iface}."
  echo "Anchor file: ${ANCHOR_FILE}"
}

main "$@"
