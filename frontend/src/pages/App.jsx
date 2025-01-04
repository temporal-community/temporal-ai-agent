import React, { useEffect, useState, useRef } from "react";
import NavBar from "../components/NavBar";
import ChatWindow from "../components/ChatWindow";

const POLL_INTERVAL = 500; // 0.5 seconds

export default function App() {
    const containerRef = useRef(null);
    const [conversation, setConversation] = useState([]);
    const [userInput, setUserInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [done, setDone] = useState(true); // New `done` state

    useEffect(() => {
        // Poll /get-conversation-history every 0.5 seconds
        const intervalId = setInterval(async () => {
            try {
                const res = await fetch("http://127.0.0.1:8000/get-conversation-history");
                if (res.ok) {
                    const data = await res.json();
                    // Update conversation
                    setConversation(data.messages || []);

                    if (data.messages && data.messages.length > 0) {
                        const lastMessage = data.messages[data.messages.length - 1];
                        setLoading(lastMessage.actor !== "agent");
                        setDone(lastMessage.response.next === "done");
                    } else {
                        setLoading(false);
                        setDone(true); // Default to `done` if no messages
                    }
                }
            } catch (err) {
                console.error("Error fetching conversation history:", err);
            }
        }, POLL_INTERVAL);

        return () => clearInterval(intervalId);
    }, []);

    const handleSendMessage = async () => {
        if (!userInput.trim()) return;
        try {
            setLoading(true); // Mark as loading
            await fetch(
                `http://127.0.0.1:8000/send-prompt?prompt=${encodeURIComponent(userInput)}`,
                { method: "POST" }
            );
            setUserInput("");
        } catch (err) {
            console.error("Error sending prompt:", err);
            setLoading(false);
        }
    };

    const handleConfirm = async () => {
        try {
            setLoading(true);
            await fetch("http://127.0.0.1:8000/confirm", { method: "POST" });
        } catch (err) {
            console.error("Confirm error:", err);
            setLoading(false);
        }
    };

    const handleStartNewChat = async () => {
        try {
            await fetch(
                `http://127.0.0.1:8000/send-prompt?prompt=${encodeURIComponent("I'd like to travel for an event.")}`,
                { method: "POST" }
            );
            setConversation([]); // Clear local state
        } catch (err) {
            console.error("Error ending chat:", err);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === "Enter") {
            handleSendMessage();
        }
    };

    useEffect(() => {
        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      }, [conversation, loading, done]);
    

    return (
        <div className="flex flex-col h-screen">
          <NavBar title="Temporal AI Agent" />
      
          {/* Centered content, but no manual bottom margin */}
          <div className="flex-grow flex justify-center px-4 py-2 overflow-hidden">
            <div className="w-full max-w-lg bg-white dark:bg-gray-900 p-8 px-3 rounded shadow-md 
                            flex flex-col overflow-hidden">
              {/* Scrollable chat area */}
              <div ref={containerRef} className="flex-grow overflow-y-auto pb-20 pt-10">
                        <ChatWindow
                            conversation={conversation}
                            loading={loading}
                            onConfirm={handleConfirm}
                        />
          {done && (
            <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
              Chat ended
            </div>
          )}
        </div>
      </div>
    </div>

            {/* Floating Input Section */}
    {/* Fixed bottom input */}
    <div
      className="fixed bottom-0 left-1/2 transform -translate-x-1/2 
                 w-full max-w-lg bg-white dark:bg-gray-900 p-4
                 border-t border-gray-300 dark:border-gray-700"
      style={{ zIndex: 10 }}
    >
                <div className="flex items-center">
                    <input
                        type="text"
                        className={`flex-grow rounded-l px-3 py-2 border border-gray-300
                    dark:bg-gray-700 dark:border-gray-600 focus:outline-none
                    ${loading || done ? "opacity-50 cursor-not-allowed" : ""}`}
                        placeholder="Type your message..."
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        disabled={loading || done}
                    />
                    <button
                        onClick={handleSendMessage}
                        className={`bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-r 
                    ${loading || done ? "opacity-50 cursor-not-allowed" : ""}`}
                        disabled={loading || done}
                    >
                        Send
                    </button>
                </div>
                <div className="text-right mt-3">
                    <button
                        onClick={handleStartNewChat}
                        className={`text-sm underline text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 
                    ${!done ? "opacity-0 cursor-not-allowed" : ""}`}
                        disabled={!done}
                    >
                        Start New Chat
                    </button>
                </div>
            </div>
        </div>
    );
}