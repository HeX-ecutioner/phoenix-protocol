import React from 'react';
import { AlertTriangle } from 'lucide-react';

export function SafetyNotice() {
  return (
    <div className="w-full bg-neutral-900/60 border-l-2 border-warning text-neutral-400 p-4 mb-8 text-sm flex items-start gap-3 rounded-r-sm">
      <AlertTriangle size={16} className="text-warning flex-shrink-0 mt-0.5" />
      <p className="leading-relaxed">
        <strong className="text-white">Read-only prototype.</strong> Use only sanitized or synthetic configuration files. Phoenix Protocol does not modify network devices. Do not upload production secrets or passwords.
      </p>
    </div>
  );
}
