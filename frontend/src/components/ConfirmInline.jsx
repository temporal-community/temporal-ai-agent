import React from "react";

export default function ConfirmInline({ data, confirmed, onConfirm }) {
  const { args, tool } = data || {};

  if (confirmed) {
    // Once confirmed, show "Running..." state in the same container
    return (
      <div className="mt-2 p-2 border border-gray-400 dark:border-gray-600 rounded bg-gray-50 dark:bg-gray-800">
        <div className="text-sm text-gray-600 dark:text-gray-300">
          <div>
            <strong>Tool:</strong> {tool ?? "Unknown"}
          </div>
          {args && (
            <div className="mt-1">
              <strong>Args:</strong>
              <pre className="bg-gray-100 dark:bg-gray-700 p-1 rounded text-sm whitespace-pre-wrap">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          )}
        </div>
        <div className="mt-2 text-green-600 dark:text-green-400 font-medium">
          Running {tool}...
        </div>
      </div>
    );
  }

  // Not confirmed yet → show confirmation UI
  return (
    <div className="mt-2 p-2 border border-gray-400 dark:border-gray-600 rounded bg-gray-50 dark:bg-gray-800">
      <div className="text-gray-600 dark:text-gray-300">
        <div>
          <strong>Tool:</strong> {tool ?? "Unknown"}
        </div>
        {args && (
          <div className="mt-1">
            <strong>Args:</strong>
            <pre className="bg-gray-100 dark:bg-gray-700 p-1 rounded text-sm whitespace-pre-wrap">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
        )}
      </div>
      <div className="text-right mt-2">
        <button
          onClick={onConfirm}
          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded"
        >
          Confirm
        </button>
      </div>
    </div>
  );
}
