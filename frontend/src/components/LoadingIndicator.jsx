import React from "react";

export default function LoadingIndicator() {
  return (
    <div className="flex items-center justify-center space-x-2 pb-4">
      <div className="w-2 h-2 rounded-full bg-blue-600 animate-ping"></div>
      <div className="w-2 h-2 rounded-full bg-blue-600 animate-ping delay-100"></div>
      <div className="w-2 h-2 rounded-full bg-blue-600 animate-ping delay-200"></div>
    </div>
  );
}
