import React, { memo, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import ConfirmInline from "./ConfirmInline";

const LLMResponse = memo(({ data, onConfirm, isLastMessage, onHeightChange }) => {
    const [isConfirmed, setIsConfirmed] = React.useState(false);
    const responseRef = React.useRef(null);

    // Notify parent of height changes when confirm UI appears/changes
    useEffect(() => {
        if (isLastMessage && responseRef.current && onHeightChange) {
            onHeightChange();
        }
    }, [isLastMessage, isConfirmed, onHeightChange]);

    const handleConfirm = async () => {
        try {
            if (onConfirm) await onConfirm();
            setIsConfirmed(true);
        } catch (error) {
            console.error('Error confirming action:', error);
        }
    };

    const response = typeof data?.response === 'object' 
        ? data.response.response 
        : data?.response;

    const displayText = (response || '').trim();
    const requiresConfirm = data.next === "confirm" && isLastMessage;
    const defaultText = requiresConfirm 
        ? `Agent is ready to run "${data.tool}". Please confirm.` 
        : '';

    return (
        <div ref={responseRef} className="space-y-2">
            <MessageBubble 
                message={{ response: displayText || defaultText }} 
            />
            {requiresConfirm && (
                <ConfirmInline
                    data={data}
                    confirmed={isConfirmed}
                    onConfirm={handleConfirm}
                />
            )}
            {!requiresConfirm && data.tool && data.next === "confirm" && (
                <div className="text-sm text-center text-green-600 dark:text-green-400">
                    <div>
                        Agent chose tool: <strong>{data.tool ?? "Unknown"}</strong>
                    </div>
                </div>
            )}
        </div>
    );
});

LLMResponse.displayName = 'LLMResponse';

export default LLMResponse;
