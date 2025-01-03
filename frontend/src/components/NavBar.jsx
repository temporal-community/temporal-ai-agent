import React from "react";

export default function NavBar({ title }) {
  return (
    <div className="bg-gray-200 dark:bg-gray-700 p-4 shadow-sm">
      <h1 className="text-xl font-bold">{title}</h1>
    </div>
  );
}
