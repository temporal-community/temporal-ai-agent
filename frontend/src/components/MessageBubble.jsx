import React, { memo } from "react";

const MessageBubble = memo(({ message, fallback = "", isUser = false }) => {
    const displayText = message.response?.trim() ? message.response : fallback;

    if (displayText.startsWith("###")) {
        return null;
    }

    const renderTextWithLinks = (text) => {
        // First handle image markdown: ![alt text](url)
        const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        
        // Split by image markdown first
        const imageParts = text.split(imageRegex);
        
        return imageParts.map((part, index) => {
            // Every third element (starting from index 2) is an image URL
            if (index > 0 && (index - 2) % 3 === 0) {
                const altText = imageParts[index - 1];
                const imageUrl = part;
                return (
                    <img
                        key={index}
                        src={imageUrl}
                        alt={altText}
                        className="max-w-full h-auto rounded mt-2 mb-2 mx-auto block border border-gray-300 dark:border-gray-600"
                        style={{ maxHeight: '200px' }}
                        loading="lazy"
                    />
                );
            }
            // Skip alt text parts (every second element after first)
            if (index > 0 && (index - 1) % 3 === 0) {
                return null;
            }
            
            // Handle regular text and links
            const linkParts = part.split(urlRegex);
            return linkParts.map((linkPart, linkIndex) => {
                if (urlRegex.test(linkPart)) {
                    return (
                        <a
                            key={`${index}-${linkIndex}`}
                            href={linkPart}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:text-blue-600 underline"
                            aria-label={`External link to ${linkPart}`}
                        >
                            {linkPart}
                        </a>
                    );
                }
                return linkPart;
            });
        }).filter(Boolean);
    };

    return (
        <div
            className={`
                inline-block px-4 py-2 mb-1 rounded-lg
                ${isUser 
                    ? "ml-auto bg-blue-100 dark:bg-blue-900 dark:text-white" 
                    : "mr-auto bg-gray-200 dark:bg-gray-700 dark:text-white"
                }
                break-words max-w-[75%] transition-colors duration-200
            `}
            role="article"
            aria-label={`${isUser ? 'User' : 'Agent'} message`}
        >
            {renderTextWithLinks(displayText)}
        </div>
    );
});

MessageBubble.displayName = 'MessageBubble';

export default MessageBubble;
