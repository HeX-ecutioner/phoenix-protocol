import React from 'react';

export function SeverityBadge({ severity }) {
  const normalized = (severity || '').toLowerCase();
  
  const styles = {
    high: 'text-red-400 font-extrabold',
    medium: 'text-yellow-400 font-bold',
    low: 'text-neutral-400 font-medium',
    default: 'text-neutral-500 font-medium'
  };

  const currentStyle = styles[normalized] || styles.default;

  return (
    <span className={`text-xs tracking-widest uppercase ${currentStyle}`}>
      {severity}
    </span>
  );
}
