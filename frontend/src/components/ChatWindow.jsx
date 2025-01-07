import React, { memo, useCallback } from "react";
import LLMResponse from "./LLMResponse";
import MessageBubble from "./MessageBubble";
import LoadingIndicator from "./LoadingIndicator";

class ChatErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("ChatWindow error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="text-red-500 p-4 text-center">
                    Something went wrong. Please refresh the page.
                </div>
            );
        }
        return this.props.children;
    }
}

const safeParse = (str) => {
    try {
        return typeof str === 'string' ? JSON.parse(str) : str;
    } catch (err) {
        console.error("safeParse error:", err, "Original string:", str);
        return str;
    }
};

const Message = memo(({ msg, idx, isLastMessage, onConfirm, onContentChange }) => {
    const { actor, response } = msg;
    
    if (actor === "user") {
        return <MessageBubble message={{ response }} isUser />;
    }
    
    if (actor === "agent") {
        const data = safeParse(response);
        return (
            <LLMResponse
                data={data}
                onConfirm={onConfirm}
                isLastMessage={isLastMessage}
                onHeightChange={onContentChange}
            />
        );
    }
    
    return null;
});

Message.displayName = 'Message';

const ChatWindow = memo(({ conversation, loading, onConfirm, onContentChange }) => {
    const validateConversation = useCallback((conv) => {
        if (!Array.isArray(conv)) {
            console.error("ChatWindow expected conversation to be an array, got:", conv);
            return [];
        }
        return conv;
    }, []);

    const filtered = validateConversation(conversation).filter((msg) => {
        const { actor } = msg;
        return actor === "user" || actor === "agent";
    });

    return (
        <ChatErrorBoundary>
            <div className="flex-grow flex flex-col">
                <div className="flex-grow flex flex-col justify-end overflow-y-auto space-y-3">
                    {filtered.map((msg, idx) => (
                        <Message
                            key={`${msg.actor}-${idx}-${typeof msg.response === 'string' ? msg.response : msg.response?.response}`}
                            msg={msg}
                            idx={idx}
                            isLastMessage={idx === filtered.length - 1}
                            onConfirm={onConfirm}
                            onContentChange={onContentChange}
                        />
                    ))}
                    {loading && (
                        <div className="pt-2 flex justify-center">
                            <LoadingIndicator />
                        </div>
                    )}
                </div>
            </div>
        </ChatErrorBoundary>
    );
});

ChatWindow.displayName = 'ChatWindow';

export default ChatWindow;
