import React from 'react';
import { motion } from 'framer-motion';
import { twMerge } from 'tailwind-merge';

export function KineticButton({ children, onClick, disabled, className, ...props }) {
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      className={twMerge(
        "relative overflow-hidden px-8 py-4 bg-brand-orange text-white font-extrabold uppercase tracking-widest text-sm rounded-full disabled:opacity-50 disabled:cursor-not-allowed border-none outline-none focus:outline-none focus:ring-0",
        className
      )}
      whileHover={!disabled ? "hover" : ""}
      whileTap={!disabled ? "tap" : ""}
      variants={{
        hover: { backgroundColor: "#ff5500" },
        tap: { scale: 0.98 }
      }}
      {...props}
    >
      <motion.div
        className="relative z-10 flex items-center justify-center gap-2"
        variants={{
          hover: { y: "-150%", transition: { duration: 0.3, ease: [0.76, 0, 0.24, 1] } }
        }}
      >
        {children}
      </motion.div>
      <motion.div
        className="absolute inset-0 z-10 flex items-center justify-center gap-2"
        initial={{ y: "150%" }}
        variants={{
          hover: { y: "0%", transition: { duration: 0.3, ease: [0.76, 0, 0.24, 1] } }
        }}
      >
        {children}
      </motion.div>
    </motion.button>
  );
}
