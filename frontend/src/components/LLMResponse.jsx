import React, { useState } from "react";
import MessageBubble from "./MessageBubble";
import ConfirmInline from "./ConfirmInline";

export default function LLMResponse({ data, onConfirm, isLastMessage }) {
  const [isConfirmed, setIsConfirmed] = useState(false);

  const handleConfirm = async () => {
    if (onConfirm) await onConfirm();
    setIsConfirmed(true);
  };

  // Only requires confirm if data.next === "confirm" AND it's the last message
  const requiresConfirm = data.next === "confirm" && isLastMessage;

  if (typeof data.response === "object") {
    data.response = data.response.response;
  }

  let displayText = (data.response || "").trim();
  if (!displayText && requiresConfirm) {
    displayText = `Agent is ready to run "${data.tool}". Please confirm.`;
  }

  return (
    <div className="space-y-2">
      <MessageBubble message={{ response: displayText }} />
      {requiresConfirm && (
        <ConfirmInline
          data={data}
          confirmed={isConfirmed}
          onConfirm={handleConfirm}
        />
      )}
    </div>
  );
}
