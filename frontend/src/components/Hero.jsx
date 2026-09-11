import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useReducedMotion } from 'framer-motion';
import { Marquee } from './motion/Marquee';

export function Hero({ onLoadComplete }) {
  const shouldReduceMotion = useReducedMotion();
  const [loadingStage, setLoadingStage] = useState('drawing');

  useEffect(() => {
    if (shouldReduceMotion) {
      setLoadingStage('complete');
      if (onLoadComplete) onLoadComplete();
      return;
    }

    const timer1 = setTimeout(() => setLoadingStage('glowing'), 2000);
    const timer2 = setTimeout(() => {
      setLoadingStage('complete');
      if (onLoadComplete) onLoadComplete();
    }, 2500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldReduceMotion]);

  const scrollToScan = () => {
    document.getElementById('scanner-console')?.scrollIntoView({ behavior: 'smooth' });
  };

  const lineTransition = { duration: 2, ease: [0.22, 1, 0.36, 1] };

  // Data for the infinite scroll Marquee
  const protocolItems = [
    ['CISCO', 'IOS'],
    ['JUNIPER', 'JUNOS'],
    ['ARISTA', 'EOS'],
    ['PALO ALTO', 'PAN-OS'],
    ['FORTINET', 'FORTIOS'],
    ['F5', 'BIG-IP'],
    ['CISCO', 'NX-OS'],
    ['CHECK', 'POINT']
  ];

  return (
    <section className="relative w-full min-h-screen flex flex-col items-center justify-center text-center overflow-hidden bg-obsidian">
      
      {/* 1. Geometric Background Lines & Circles (Always present) */}
      <div 
        className="absolute inset-0 z-0 pointer-events-none"
        style={{
          WebkitMaskImage: 'radial-gradient(circle at center, white 30%, transparent 80%)',
          maskImage: 'radial-gradient(circle at center, white 30%, transparent 80%)'
        }}
      >
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          {/* 12 rays passing through the center */}
          {[0, 30, 60, 90, 120, 150].map((angle, i) => (
            <motion.line
              key={i}
              x1="-50%" y1="50%" x2="150%" y2="50%"
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="1"
              style={{ transformOrigin: '50% 50%', transform: `rotate(${angle}deg)` }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 2, delay: 0.5 }}
            />
          ))}
          
          {/* Center Circle (Increased by 20%) */}
          <motion.circle 
            cx="50%" cy="50%" r="30vmin" 
            fill="none" stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
          <motion.circle 
            cx="50%" cy="50%" r="30vmin" 
            fill="none" stroke="url(#centerGlow)" strokeWidth="2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            transition={{ duration: 2, delay: 1 }}
          />
          {/* Left Circle */}
          <motion.circle 
            cx="calc(50% - 25vmin)" cy="50%" r="25vmin" 
            fill="none" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" 
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 2, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
          />
          {/* Right Circle */}
          <motion.circle 
            cx="calc(50% + 25vmin)" cy="50%" r="25vmin" 
            fill="none" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" 
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ ...lineTransition, delay: 0.4 }}
          />
        </svg>
      </div>

      {/* 2. The Glowing Ring */}
      <motion.div 
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full z-0 pointer-events-none"
        style={{
          width: '50vmin',
          height: '50vmin',
          boxShadow: '0 0 100px 20px rgba(255, 68, 0, 0.4), inset 0 0 80px 10px rgba(0, 255, 255, 0.2)',
          border: '2px solid rgba(255, 68, 0, 0.5)'
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: loadingStage !== 'drawing' ? 0.8 : 0 }}
        transition={{ duration: 1 }}
      />
      
      {/* 2b. Initial Loading Logo */}
      <AnimatePresence>
        {loadingStage === 'drawing' && (
          <motion.div 
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30 flex items-center justify-center pointer-events-none"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.2 }}
            transition={{ duration: 0.5 }}
          >
            <svg width="60" height="60" viewBox="0 0 100 100" fill="none" stroke="white" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
              <motion.path 
                d="M 50,10 Q 50,50 10,50 Q 50,50 50,90 Q 50,50 90,50 Q 50,50 50,10" 
                initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.5, ease: "easeInOut" }} 
              />
            </svg>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 3. Massive Typography (Revealed on complete) */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-full px-4 flex flex-col items-center justify-center h-full pointer-events-none">
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: loadingStage === 'complete' ? 1 : 0, y: loadingStage === 'complete' ? 0 : 20 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-[12vw] md:text-[8.5vw] font-sans font-black tracking-tight text-white uppercase leading-none z-20 mix-blend-plus-lighter -translate-y-[10%]"
        >
          NETWORK SECURITY.
        </motion.h1>
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: loadingStage === 'complete' ? 1 : 0, y: loadingStage === 'complete' ? 0 : 20 }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="text-[12vw] md:text-[8.5vw] font-sans font-black tracking-tight text-neutral-500 uppercase leading-none z-10 translate-y-[10%]"
        >
          CLEARLY VERIFIED
        </motion.h1>
      </div>

      {/* 4. Bottom Content (Description, Clean Button, Infinite Scroll) */}
      <motion.div 
        className="absolute bottom-0 w-full flex flex-col z-20"
        initial={{ opacity: 0 }}
        animate={{ opacity: loadingStage === 'complete' ? 1 : 0 }}
        transition={{ delay: 0.3, duration: 1 }}
      >
        <div className="flex flex-col items-center pb-8 bg-gradient-to-t from-obsidian via-obsidian/80 to-transparent pt-24">
          <p className="text-neutral-500 text-xs md:text-sm max-w-lg text-center mb-6 font-medium px-6 leading-relaxed">
            From strict STIG benchmarks to immediate compliance reporting, zero-trust configuration analysis delivered by the read-only engine.
          </p>
          
          {/* Scroll Button (No Bounding Box) */}
          <button 
            onClick={scrollToScan}
            className="text-brand-orange text-xs font-bold tracking-[0.2em] uppercase hover:text-white transition-colors flex flex-col items-center gap-2 group"
          >
            Scroll to begin analysis
          </button>
        </div>

        {/* 5. Infinite Scroll Marquee at Absolute Bottom */}
        <Marquee items={protocolItems} />
      </motion.div>
    </section>
  );
}
