import React from 'react';

export function SummaryCard({ label, value }) {
  return (
    <div className="bg-neutral-900/40 p-6 border border-neutral-800 hover:border-neutral-700 transition-colors rounded-sm flex flex-col justify-between">
      <div className="text-4xl font-sans font-extrabold tracking-tighter text-white mb-2">
        {value}
      </div>
      <div className="text-[0.75rem] font-bold tracking-widest text-neutral-400 uppercase">
        {label}
      </div>
    </div>
  );
}
