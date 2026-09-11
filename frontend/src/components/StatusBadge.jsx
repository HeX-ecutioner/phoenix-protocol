import React from 'react';

export function StatusBadge({ status }) {
  const normalized = (status || '').toLowerCase();
  
  const styles = {
    pass: 'text-lime-400 bg-lime-400/10 border-lime-400/30',
    fail: 'text-red-400 bg-red-400/10 border-red-400/30',
    warning: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
    error: 'text-white bg-red-500 border-red-600',
    'not applicable': 'text-neutral-400 bg-neutral-400/10 border-neutral-400/30',
    default: 'text-neutral-300 bg-neutral-800 border-neutral-700'
  };

  const currentStyle = styles[normalized] || styles.default;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-sm border text-[0.7rem] font-bold tracking-widest uppercase ${currentStyle}`}>
      {status}
    </span>
  );
}
