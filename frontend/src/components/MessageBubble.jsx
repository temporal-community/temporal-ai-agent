import React from "react";

export default function MessageBubble({ message, fallback = "", isUser = false }) {
  const bubbleStyle = isUser
    ? "bg-blue-600 text-white self-end"
    : "bg-gray-300 text-gray-900 dark:bg-gray-600 dark:text-gray-100";

  const displayText = message.response?.trim() ? message.response : fallback;

  if (displayText.startsWith("###")) {
    return null;
  }

  // Function to detect and render URLs as links
  const renderTextWithLinks = (text) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);

    return parts.map((part, index) => {
      if (urlRegex.test(part)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 underline"
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };

  return (
    <div
      className={`inline-block px-4 py-2 mb-1 rounded-lg ${
        isUser ? "ml-auto bg-blue-100" : "mr-auto bg-gray-200"
      } break-words`}
      style={{
        whiteSpace: "pre-wrap",
        maxWidth: "75%", // or '80%'
      }}
    >
      {renderTextWithLinks(displayText)}
    </div>
  );
}
