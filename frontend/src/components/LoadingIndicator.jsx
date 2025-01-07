import React, { memo } from "react";

const LoadingIndicator = memo(() => {
    return (
        <div 
            className="flex items-center justify-center space-x-2 pb-4"
            role="status"
            aria-label="Loading"
        >
            {[0, 1, 2].map((i) => (
                <div
                    key={i}
                    className={`w-2 h-2 rounded-full bg-blue-600 animate-ping
                        ${i > 0 ? `delay-${i}00` : ''}`}
                />
            ))}
            <span className="sr-only">Loading...</span>
        </div>
    );
});

LoadingIndicator.displayName = 'LoadingIndicator';

export default LoadingIndicator;
