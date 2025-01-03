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
      // Keep if next is "question", "confirm", or "user_confirmed_tool_run".
      // Only skip if next is "done" (or something else).
      // return !["done"].includes(parsed.next);
      return true;
    }
    return false;
  });

  return (
    <div className="flex-grow overflow-y-auto space-y-4">
      {filtered.map((msg, idx) => {

        const { actor, response } = msg;

        if (actor === "user") {
          return (
            <MessageBubble key={idx} message={{ response }} isUser />
          );
        } else if (actor === "agent") {
          const data =
            typeof response === "string" ? safeParse(response) : response;
          return <LLMResponse key={idx} data={data} onConfirm={onConfirm} />;
        }
        return null;
      })}

      {/* If loading = true, show the spinner at the bottom */}
      {loading && (
        <div className="flex justify-center">
          <LoadingIndicator />
        </div>
      )}
    </div>
  );
}
