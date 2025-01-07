import React, { memo } from "react";

const ConfirmInline = memo(({ data, confirmed, onConfirm }) => {
    const { args, tool } = data || {};

    const renderArgs = () => {
        if (!args) return null;
        
        return (
            <div className="mt-1">
                <strong>Args:</strong>
                <pre className="bg-gray-100 dark:bg-gray-700 p-1 rounded text-sm whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(args, null, 2)}
                </pre>
            </div>
        );
    };

    if (confirmed) {
        return (
            <div className="mt-2 p-2 border border-gray-400 dark:border-gray-600 rounded 
                bg-gray-50 dark:bg-gray-800 transition-colors duration-200">
                <div className="text-sm text-gray-600 dark:text-gray-300">
                    <div>
                        <strong>Tool:</strong> {tool ?? "Unknown"}
                    </div>
                    {renderArgs()}
                </div>
                <div className="mt-2 text-green-600 dark:text-green-400 font-medium">
                    Running {tool}...
                </div>
            </div>
        );
    }

    return (
        <div className="mt-2 p-2 border border-gray-400 dark:border-gray-600 rounded 
            bg-gray-50 dark:bg-gray-800 transition-colors duration-200">
            <div className="text-gray-600 dark:text-gray-300">
                <div>
                    Agent is ready to run the tool: <strong>{tool ?? "Unknown"}</strong>
                </div>
                {renderArgs()}
                <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Please confirm to proceed.
                </div>
            </div>
            <div className="text-right mt-2">
                <button
                    onClick={onConfirm}
                    className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded
                        transition-colors duration-200 focus:outline-none focus:ring-2 
                        focus:ring-green-500 focus:ring-opacity-50"
                    aria-label={`Confirm running ${tool}`}
                >
                    Confirm
                </button>
            </div>
        </div>
    );
});

ConfirmInline.displayName = 'ConfirmInline';

export default ConfirmInline;
