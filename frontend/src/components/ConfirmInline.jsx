import React, { memo, useState } from "react";

/** Inline SVG icons so we don’t need an extra library */
const PlayIcon = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
    aria-hidden="true"
  >
    <path d="M5 3.868v16.264c0 1.04 1.12 1.675 2.025 1.16l13.11-8.132a1.33 1.33 0 000-2.256L7.025 2.773C6.12 2.259 5 2.894 5 3.934z" />
  </svg>
);

const SpinnerIcon = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={`animate-spin ${className}`}
    aria-hidden="true"
  >
    <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
    <path d="M22 12a10 10 0 00-10-10" />
  </svg>
);

/**
 * User‑friendly confirmation card that surfaces tool invocation details
 * without developer jargon.  Tweaks include:
 *  • Left green accent‑border + compact heading (visual hierarchy)
 *  • Collapsible arg list & array support (argument‑list UX)
 *  • Mobile‑first, pulsing confirm button (button affordance)
 */
const ConfirmInline = memo(({ data, confirmed, onConfirm }) => {
  const { args = {}, tool } = data || {};

  // Collapsible argument list if we have more than 4 root keys
  const [showAll, setShowAll] = useState(false);
  const argEntries = Object.entries(args);
  const shouldCollapse = argEntries.length > 4 && !showAll;

  /** Recursively pretty‑print argument values (objects & arrays). */
  const RenderValue = ({ value }) => {
    if (value === null || value === undefined) return <span className="italic">‑</span>;

    if (Array.isArray(value)) {
      return (
        <ol className="pl-4 list-decimal space-y-0.5">
          {value.map((v, i) => (
            <li key={i} className="flex gap-1">
              <RenderValue value={v} />
            </li>
          ))}
        </ol>
      );
    }

    if (typeof value === "object") {
      return (
        <ul className="pl-4 space-y-0.5 list-disc marker:text-green-500 dark:marker:text-green-400">
          {Object.entries(value).map(([k, v]) => (
            <li key={k} className="flex gap-1">
              <span className="capitalize text-gray-600 dark:text-gray-300">{k}:&nbsp;</span>
              <RenderValue value={v} />
            </li>
          ))}
        </ul>
      );
    }

    return <span className="font-medium text-gray-800 dark:text-gray-100">{String(value)}</span>;
  };

  const cardBase =
    "mt-2 p-3 rounded-lg border-l-4 border-green-500 bg-gray-100/60 dark:bg-gray-800/60 shadow-sm";

  // ===== Running state =====
  if (confirmed) {
    return (
      <div className={`${cardBase} flex items-center gap-3`} role="status">
        <SpinnerIcon className="text-green-600 dark:text-green-400 w-4 h-4" />
        <span className="text-sm text-gray-700 dark:text-gray-200">
          Running <strong className="font-semibold">{tool ?? "Unknown"}</strong> …
        </span>
      </div>
    );
  }

  // ===== Confirmation state =====
  return (
    <div className={`${cardBase} space-y-2`} role="group">
      {/* Heading */}
      <div className="flex items-center gap-2">
        <PlayIcon className="text-green-600 dark:text-green-400 w-5 h-5 shrink-0" />
        <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
          Ready to run <strong>{tool ?? "Unknown"}</strong>
        </p>
      </div>

      {/* Dynamic argument list */}
      {argEntries.length > 0 && (
        <div className="text-sm text-gray-700 dark:text-gray-300">
          {argEntries
            .slice(0, shouldCollapse ? 4 : argEntries.length)
            .map(([k, v]) => (
              <div key={k} className="flex gap-1">
                <span className="capitalize">{k}:&nbsp;</span>
                <RenderValue value={v} />
              </div>
            ))}
          {shouldCollapse && (
            <button
              onClick={() => setShowAll(true)}
              className="mt-1 text-green-600 dark:text-green-400 text-xs underline hover:no-underline"
            >
              …show all
            </button>
          )}
          {showAll && argEntries.length > 4 && (
            <button
              onClick={() => setShowAll(false)}
              className="mt-1 block text-green-600 dark:text-green-400 text-xs underline hover:no-underline"
            >
              show less
            </button>
          )}
        </div>
      )}

      {/* Confirm button */}
      <div className="text-right">
        <button
          onClick={onConfirm}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onConfirm()}
          className="w-full sm:w-auto bg-green-600 hover:bg-green-700 text-white text-sm px-3 py-1.5 rounded-md shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 animate-pulse sm:animate-none"
          aria-label={`Confirm running ${tool}`}
        >
          Confirm
        </button>
      </div>
    </div>
  );
});

ConfirmInline.displayName = "ConfirmInline";

export default ConfirmInline;
