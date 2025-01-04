import React from "react";
import LLMResponse from "./LLMResponse";
import MessageBubble from "./MessageBubble";
import LoadingIndicator from "./LoadingIndicator";

function safeParse(str) {
  try {
    return JSON.parse(str);
  } catch (err) {
    console.error("safeParse error:", err, "Original string:", str);
    return {};
  }
}

export default function ChatWindow({ conversation, loading, onConfirm }) {
  if (!Array.isArray(conversation)) {
    console.error("ChatWindow expected conversation to be an array, got:", conversation);
    return null;
  }

  const filtered = conversation.filter((msg) => {
    const { actor, response } = msg;

    if (actor === "user") {
      return true;
    }
    if (actor === "agent") {
      const parsed = typeof response === "string" ? safeParse(response) : response;
      return true; // Adjust this logic based on your "next" field.
    }
    return false;
  });

  return (
    <div className="flex-grow flex flex-col">
      {/* Main message container */}
      <div className="flex-grow flex flex-col justify-end overflow-y-auto space-y-3">
        {filtered.map((msg, idx) => {
          const { actor, response } = msg;
  
          if (actor === "user") {
            return <MessageBubble key={idx} message={{ response }} isUser />;
          } else if (actor === "agent") {
            const data =
              typeof response === "string" ? safeParse(response) : response;
            const isLastMessage = idx === filtered.length - 1;
            return (
              <LLMResponse
                key={idx}
                data={data}
                onConfirm={onConfirm}
                isLastMessage={isLastMessage}
              />
            );
          }
          return null; // Fallback for unsupported actors.
        })}
        {/* Loading indicator */}
        {loading && (
          <div className="pt-2 flex justify-center">
            <LoadingIndicator />
          </div>
        )}
      </div>
    </div>
  );
  
}
