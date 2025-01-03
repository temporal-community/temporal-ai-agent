import React from "react";

export default function MessageBubble({ message, fallback = "", isUser = false }) {
  // Use isUser directly instead of message.user
  const bubbleStyle = isUser
    ? "bg-blue-600 text-white self-end"
    : "bg-gray-300 text-gray-900 dark:bg-gray-600 dark:text-gray-100";

  // If message.response is empty or whitespace, use fallback text
  const displayText = message.response?.trim() ? message.response : fallback;

  // Skip display entirely if text starts with ###
  if (displayText.startsWith("###")) {
    return null;
  }

  return (
    <div
      className={`max-w-xs md:max-w-sm px-4 py-2 mb-1 rounded-lg ${
        isUser ? "ml-auto" : "mr-auto"
      } ${bubbleStyle}`}
      style={{ whiteSpace: "pre-wrap" }}
    >
      {displayText}
    </div>
  );
}
