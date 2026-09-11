import React from 'react';
import { AlertCircle } from 'lucide-react';

export function ErrorAlert({ message }) {
  if (!message) return null;
  return (
    <div className="mb-6 p-4 border border-red-900/50 bg-red-900/10 text-red-400 text-sm font-mono flex items-center gap-3 rounded-sm shadow-[0_0_15px_rgba(237,119,112,0.1)]">
      <AlertCircle size={18} />
      {message}
    </div>
  );
}
