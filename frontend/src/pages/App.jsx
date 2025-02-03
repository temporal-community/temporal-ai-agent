import React, { useEffect, useState, useRef, useCallback } from "react";
import NavBar from "../components/NavBar";
import ChatWindow from "../components/ChatWindow";
import { apiService } from "../services/api";

const POLL_INTERVAL = 500; // 0.5 seconds
const INITIAL_ERROR_STATE = { visible: false, message: '' };
const DEBOUNCE_DELAY = 300; // 300ms debounce for user input

function useDebounce(value, delay) {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}

export default function App() {
    const containerRef = useRef(null);
    const inputRef = useRef(null);
    const pollingRef = useRef(null);
    const scrollTimeoutRef = useRef(null);
    
    const [conversation, setConversation] = useState([]);
    const [lastMessage, setLastMessage] = useState(null);
    const [userInput, setUserInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(INITIAL_ERROR_STATE);
    const [done, setDone] = useState(true);

    const debouncedUserInput = useDebounce(userInput, DEBOUNCE_DELAY);

    // Error handling utility with auto-dismiss
    const handleError = useCallback((error, context) => {
        console.error(`${context}:`, error);
        const errorMessage = error.status === 400 
            ? error.message 
            : `Error ${context.toLowerCase()}. Please try again.`;
            
        setError({
            visible: true,
            message: errorMessage
        });
        
        const timer = setTimeout(() => setError(INITIAL_ERROR_STATE), 3000);
        return () => clearTimeout(timer);
    }, []);

    const fetchConversationHistory = useCallback(async () => {
        try {
            const data = await apiService.getConversationHistory();
            const newConversation = data.messages || [];
            
            setConversation(prevConversation => {
                // Only update if there are actual changes
                if (JSON.stringify(prevConversation) !== JSON.stringify(newConversation)) {
                    return newConversation;
                }
                return prevConversation;
            });

            if (newConversation.length > 0) {
                const lastMsg = newConversation[newConversation.length - 1];
                const isAgentMessage = lastMsg.actor === "agent";
                
                setLoading(!isAgentMessage);
                setDone(lastMsg.response.next === "done");

                setLastMessage(prevLastMessage => {
                    if (!prevLastMessage || lastMsg.response.response !== prevLastMessage.response.response) {
                        return lastMsg;
                    }
                    return prevLastMessage;
                });
            } else {
                setLoading(false);
                setDone(true);
                setLastMessage(null);
            }
        } catch (err) {
            handleError(err, "fetching conversation");
        }
    }, [handleError]);

    // Setup polling with cleanup
    useEffect(() => {
        pollingRef.current = setInterval(fetchConversationHistory, POLL_INTERVAL);
        
        return () => {
            if (pollingRef.current) {
                clearInterval(pollingRef.current);
            }
        };
    }, [fetchConversationHistory]);

    const scrollToBottom = useCallback(() => {
        if (containerRef.current) {
            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
            }
            
            scrollTimeoutRef.current = setTimeout(() => {
                const element = containerRef.current;
                element.scrollTop = element.scrollHeight;
                scrollTimeoutRef.current = null;
            }, 100);
        }
    }, []);

    const handleContentChange = useCallback(() => {
        scrollToBottom();
    }, [scrollToBottom]);

    useEffect(() => {
        if (lastMessage) {
            scrollToBottom();
        }
    }, [lastMessage, scrollToBottom]);

    useEffect(() => {
        if (inputRef.current && !loading && !done) {
            inputRef.current.focus();
        }
        
        return () => {
            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
            }
        };
    }, [loading, done]);

    const handleSendMessage = async () => {
        const trimmedInput = userInput.trim();
        if (!trimmedInput) return;
        
        try {
            setLoading(true);
            setError(INITIAL_ERROR_STATE);
            await apiService.sendMessage(trimmedInput);
            setUserInput("");
        } catch (err) {
            handleError(err, "sending message");
            setLoading(false);
        }
    };

    const handleConfirm = async () => {
        try {
            setLoading(true);
            setError(INITIAL_ERROR_STATE);
            await apiService.confirm();
        } catch (err) {
            handleError(err, "confirming action");
            setLoading(false);
        }
    };

    const handleStartNewChat = async () => {
        try {
            setError(INITIAL_ERROR_STATE);
            setLoading(true);
            await apiService.startWorkflow();
            setConversation([]);
            setLastMessage(null);
        } catch (err) {
            handleError(err, "starting new chat");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen">
            <NavBar title="Temporal AI Agent 🤖" />

            {error.visible && (
                <div className="fixed top-16 left-1/2 transform -translate-x-1/2 
                    bg-red-500 text-white px-4 py-2 rounded shadow-lg z-50 
                    transition-opacity duration-300">
                    {error.message}
                </div>
            )}

            <div className="flex-grow flex justify-center px-4 py-2 overflow-hidden">
                <div className="w-full max-w-lg bg-white dark:bg-gray-900 p-8 px-3 rounded shadow-md 
                    flex flex-col overflow-hidden">
                    <div ref={containerRef} 
                        className="flex-grow overflow-y-auto pb-20 pt-10 scroll-smooth">
                        <ChatWindow
                            conversation={conversation}
                            loading={loading}
                            onConfirm={handleConfirm}
                            onContentChange={handleContentChange}
                        />
                        {done && (
                            <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4 
                                animate-fade-in">
                                Chat ended
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="fixed bottom-0 left-1/2 transform -translate-x-1/2 
                w-full max-w-lg bg-white dark:bg-gray-900 p-4
                border-t border-gray-300 dark:border-gray-700 shadow-lg
                transition-all duration-200"
                style={{ zIndex: 10 }}>
                <form onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                }} className="flex items-center">
                    <input
                        ref={inputRef}
                        type="text"
                        className={`flex-grow rounded-l px-3 py-2 border border-gray-300
                            dark:bg-gray-700 dark:border-gray-600 focus:outline-none
                            transition-opacity duration-200
                            ${loading || done ? "opacity-50 cursor-not-allowed" : ""}`}
                        placeholder="Type your message..."
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        disabled={loading || done}
                        aria-label="Type your message"
                    />
                    <button
                        type="submit"
                        className={`bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-r 
                            transition-all duration-200
                            ${loading || done ? "opacity-50 cursor-not-allowed" : ""}`}
                        disabled={loading || done}
                        aria-label="Send message"
                    >
                        Send
                    </button>
                </form>
                
                <div className="text-right mt-3">
                    <button
                        onClick={handleStartNewChat}
                        className={`text-sm underline text-gray-600 dark:text-gray-400 
                            hover:text-gray-800 dark:hover:text-gray-200 
                            transition-all duration-200
                            ${!done ? "opacity-0 cursor-not-allowed" : ""}`}
                        disabled={!done}
                        aria-label="Start new chat"
                    >
                        Start New Chat
                    </button>
                </div>
            </div>
        </div>
    );
}
