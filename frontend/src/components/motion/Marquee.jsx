import React from 'react';
import { useReducedMotion } from 'framer-motion';

export function Marquee({ items = [] }) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return (
      <div className="w-full bg-brand-orange text-black py-4 overflow-hidden border-y border-brand-orange/50">
        <div className="flex justify-center gap-16 font-extrabold tracking-widest text-sm text-center">
          {items.map((item, i) => (
            <div key={i} className="flex flex-col items-center leading-tight">
              <span>{item[0]}</span>
              <span>{item[1]}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Duplicate items to ensure we have exactly two identical halves that fill the screen
  const marqueeGroup = [...items, ...items, ...items];

  return (
    <div className="w-full bg-transparent text-white/80 py-4 overflow-hidden flex">
      <style>{`
        @keyframes marquee-scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee-smooth {
          animation: marquee-scroll 50s linear infinite;
        }
      `}</style>
      <div className="flex animate-marquee-smooth w-max">
        {/* First Half */}
        <div className="flex gap-24 font-extrabold tracking-widest text-sm pr-24">
          {marqueeGroup.map((item, i) => (
            <div key={`a-${i}`} className="flex flex-col items-center leading-tight whitespace-nowrap opacity-80">
              <span>{item[0]}</span>
              <span>{item[1]}</span>
            </div>
          ))}
        </div>
        {/* Second Half (Exact Duplicate) */}
        <div className="flex gap-24 font-extrabold tracking-widest text-sm pr-24">
          {marqueeGroup.map((item, i) => (
            <div key={`b-${i}`} className="flex flex-col items-center leading-tight whitespace-nowrap opacity-80">
              <span>{item[0]}</span>
              <span>{item[1]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
