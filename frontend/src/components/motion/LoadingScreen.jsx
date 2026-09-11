import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useReducedMotion } from 'framer-motion';

export function LoadingScreen({ onComplete, duration = 1800, message = "INITIALIZING SECURE SCANNER CONSOLE" }) {
  const shouldReduceMotion = useReducedMotion();
  const [stage, setStage] = useState('drawing');

  useEffect(() => {
    if (shouldReduceMotion) {
      if (onComplete) onComplete();
      return;
    }

    const t1 = duration * 0.45;
    const t2 = duration * 0.8;
    const t3 = duration;

    const timer1 = setTimeout(() => setStage('glowing'), t1);
    const timer2 = setTimeout(() => setStage('exit'), t2);
    const timer3 = setTimeout(() => {
      if (onComplete) onComplete();
    }, t3);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [onComplete, duration, shouldReduceMotion]);

  const circleTransition = { duration: duration * 0.0006, ease: "easeInOut" };
  const lineTransition = { duration: duration * 0.00045, ease: "easeInOut" };

  return (
    <AnimatePresence>
      {stage !== 'exit' && (
        <motion.div 
          className="fixed inset-0 z-[100] bg-obsidian flex items-center justify-center overflow-hidden"
          exit={{ opacity: 0, transition: { duration: 1, ease: "easeInOut" } }}
        >
          {/* Animated SVG Lines and Circles */}
          <div className="absolute inset-0 z-0 pointer-events-none">
            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
              {/* Diagonal Crosshairs */}
              <motion.line 
                x1="0" y1="0" x2="100%" y2="100%" 
                stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1" 
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={lineTransition}
              />
              <motion.line 
                x1="100%" y1="0" x2="0" y2="100%" 
                stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={lineTransition}
              />
              
              {/* Vertical & Horizontal Center Lines */}
              <motion.line 
                x1="50%" y1="0" x2="50%" y2="100%" 
                stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1" 
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={lineTransition}
              />
              <motion.line 
                x1="0" y1="50%" x2="100%" y2="50%" 
                stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1" 
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={lineTransition}
              />

              {/* The 3 Intersecting Circles */}
              {/* Center Circle */}
              <motion.circle 
                cx="50%" cy="50%" r="20%" 
                fill="none" stroke="rgba(255, 68, 0, 0.5)" strokeWidth="1" 
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={circleTransition}
              />
              {/* Left Circle (Offset by radius = 20%) */}
              <motion.circle 
                cx="30%" cy="50%" r="20%" 
                fill="none" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" 
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ ...circleTransition, delay: 0.2 }}
              />
              {/* Right Circle (Offset by radius = 20%) */}
              <motion.circle 
                cx="70%" cy="50%" r="20%" 
                fill="none" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" 
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ ...circleTransition, delay: 0.4 }}
              />
            </svg>
          </div>

          {/* The Glowing Ring - fades in after drawing */}
          <motion.div 
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40vw] h-[40vw] rounded-full z-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: stage === 'glowing' ? 0.8 : 0 }}
            transition={{ duration: 1 }}
            style={{
              boxShadow: '0 0 100px 20px rgba(255, 68, 0, 0.4), inset 0 0 80px 10px rgba(0, 255, 255, 0.2)',
              border: '2px solid rgba(255, 68, 0, 0.5)'
            }}
          />

          {/* Loading Text Overlay */}
          <div className="relative z-10 flex flex-col items-center justify-center">
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: stage !== 'exit' ? 1 : 0, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="text-white font-mono text-xs tracking-[0.3em] uppercase text-center px-4"
            >
              {message}
            </motion.div>
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: "140px" }}
              transition={{ delay: 0.2, duration: duration * 0.0007, ease: "linear" }}
              className="h-[2px] bg-brand-orange mt-4 shadow-[0_0_12px_rgba(234,88,20,0.8)]"
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
