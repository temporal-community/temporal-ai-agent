import React, { useEffect, useState } from "react";
import NavBar from "../components/NavBar";
import ChatWindow from "../components/ChatWindow";

const POLL_INTERVAL = 500; // 0.5 seconds

export default function App() {
    const [conversation, setConversation] = useState([]);
    const [userInput, setUserInput] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Poll /get-conversation-history once per second
        const intervalId = setInterval(async () => {
            try {
                const res = await fetch("http://127.0.0.1:8000/get-conversation-history");
                if (res.ok) {
                    const data = await res.json();
                    // data is now an object like { messages: [ ... ] }

                    if (data.messages && data.messages.some(msg => msg.actor === "response" || msg.actor === "tool_result")) {
                        setLoading(false);
                    }
                    setConversation(data.messages || []);
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
            setLoading(true); // <--- Mark as loading
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
            await fetch("http://127.0.0.1:8000/end-chat", { method: "POST" });
            // sleep for a bit to allow the server to process the end-chat request
            await new Promise((resolve) => setTimeout(resolve, 4000)); // todo make less dodgy
            await fetch(
                `http://127.0.0.1:8000/send-prompt?prompt=${encodeURIComponent("I'd like to travel to an event.")}`,
                { method: "POST" }
            );
            setConversation([]); // clear local state
        } catch (err) {
            console.error("Error ending chat:", err);
        }
    };

    return (
        <div className="flex flex-col min-h-screen">
            <NavBar title="Temporal AI Agent" />
            <div className="flex-grow flex justify-center px-4 py-6">
                <div className="w-full max-w-lg bg-white dark:bg-gray-900 p-4 rounded shadow-md flex flex-col">
                    {/* Pass down the array of messages to ChatWindow */}
                    <ChatWindow
                        conversation={conversation}
                        loading={loading}
                        onConfirm={handleConfirm}
                    />

                    <div className="flex items-center mt-4">
                        <input
                            type="text"
                            className="flex-grow rounded-l px-3 py-2 border border-gray-300
                                dark:bg-gray-700 dark:border-gray-600 focus:outline-none"
                            placeholder="Type your message..."
                            value={userInput}
                            onChange={(e) => setUserInput(e.target.value)}
                        />
                        <button
                            onClick={handleSendMessage}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-r"
                        >
                            Send
                        </button>
                    </div>
                    <div className="text-right mt-3">
                        <button
                            onClick={handleStartNewChat}
                            className="text-sm underline text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                        >
                            Start New Chat
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
