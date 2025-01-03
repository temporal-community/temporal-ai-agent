import React, { useState } from "react";
import MessageBubble from "./MessageBubble";
import ConfirmInline from "./ConfirmInline";

export default function LLMResponse({ data, onConfirm }) {
  const [isConfirmed, setIsConfirmed] = useState(false);

  const handleConfirm = async () => {
    if (onConfirm) {
      await onConfirm();
    }
    setIsConfirmed(true); // Update state after confirmation
  };

  const requiresConfirm = data.next === "confirm";

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
