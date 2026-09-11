import React, { useRef } from 'react';
import { motion, useInView, useAnimationFrame, useMotionValue, useMotionTemplate } from 'framer-motion';

const protocols = ['BGPv4', 'OSPFv2', 'IS-IS', 'EIGRP', 'RIPv2', 'MP-BGP', 'BGP-LS', 'OSPFv3'];
const keyTypes = ['SSH-RSA', 'ED25519', 'ECDSA', 'DSA'];
const keyLengths = ['4096-BIT', 'SHA256', 'SECP256R1', '2048-BIT'];

// Generate 40 rows to ensure it covers the screen nicely
const data = Array.from({ length: 40 }).map((_, i) => ({
  protocol: protocols[i % protocols.length],
  key1: keyTypes[i % keyTypes.length],
  key2: keyLengths[i % keyLengths.length],
  ip: `10.${Math.floor(i / 255)}.${i % 255}.${(i * 7) % 254 + 1}`
}));

const Row = ({ protocol, key1, key2, ip }) => {
  const ref = useRef(null);
  // Trigger exactly in the vertical center of the window
  const isInView = useInView(ref, { margin: "-50% 0px -50% 0px" });

  const xLeft = useMotionValue(0);
  const xRight = useMotionValue(0);
  const bgGap = useMotionValue(0);
  const borderGap = useMotionValue(0);
  const borderFade = useMotionValue(0);

  // Perfect circle radius. Both horizontal and vertical bounds are 110px.
  const R_zone = 110; 
  const baseMargin = 12; // Static base margin for precise math
  const R_ring = 65; // The radius of the central dial

  useAnimationFrame(() => {
    if (!ref.current) return;
    
    // Dynamically calculate distance from viewport center for pixel-perfect accuracy
    const rect = ref.current.getBoundingClientRect();
    const rowCenter = rect.top + rect.height / 2;
    const viewportCenter = window.innerHeight / 2;
    
    const y = rowCenter - viewportCenter;
    
    // 1. Perfectly circular text displacement
    if (Math.abs(y) >= R_zone) {
      xLeft.set(0);
      xRight.set(0);
      bgGap.set(0);
    } else {
      // Circle formula: x = sqrt(1 - y^2)
      const y_norm = y / R_zone;
      const x_norm = Math.sqrt(1 - y_norm * y_norm);
      
      const requiredDist = R_zone * x_norm;
      let shift = requiredDist - baseMargin;
      if (shift < 0) shift = 0;

      xLeft.set(-shift);
      xRight.set(shift);
      
      // Active background gap matches the exact text position
      bgGap.set(shift > 0 ? requiredDist : baseMargin);
    }

    // 2. Smoothly vanish the horizontal line when it is near the ring
    if (Math.abs(y) >= R_ring) {
      borderGap.set(0);
      borderFade.set(-1); // Clamps out-of-order gradient stops to make it perfectly solid
    } else {
      const intersect = Math.sqrt(R_ring * R_ring - y * y);
      borderGap.set(intersect);
      borderFade.set(40); // 40px fade transition (the "blur" vanishing effect)
    }
  });

  // Dynamic gradients
  const borderGradient = useMotionTemplate`linear-gradient(to right, rgba(64,64,64,0.3) 0%, rgba(64,64,64,0.3) calc(50% - ${borderGap}px - ${borderFade}px), transparent calc(50% - ${borderGap}px), transparent calc(50% + ${borderGap}px), rgba(64,64,64,0.3) calc(50% + ${borderGap}px + ${borderFade}px), rgba(64,64,64,0.3) 100%)`;
  const activeBgGradient = useMotionTemplate`linear-gradient(to right, #EA5814 0%, #EA5814 calc(50% - ${bgGap}px), transparent calc(50% - ${bgGap}px), transparent calc(50% + ${bgGap}px), #EA5814 calc(50% + ${bgGap}px), #EA5814 100%)`;

  return (
    <motion.div 
      ref={ref}
      className={`relative flex items-center w-full h-[32px] transition-colors duration-200 overflow-hidden ${
        isInView ? 'text-white' : 'text-neutral-500 hover:text-neutral-400 bg-transparent'
      }`}
      style={{
        background: isInView ? activeBgGradient : 'transparent'
      }}
    >
      {/* Dynamic horizontal line that fades out smoothly ("vanishes") near the center dial */}
      <motion.div 
        className="absolute bottom-0 left-0 w-full h-[1px]"
        style={{ background: borderGradient }}
      />
      {/* Extreme Left */}
      <div className="absolute left-4 md:left-8 font-mono text-[8px] md:text-[9px] font-bold uppercase tracking-widest text-left z-10">
        {protocol}
      </div>

      {/* Middle Left (Pushed dynamically by perfectly round physical curve) */}
      <motion.div
        style={{ x: xLeft }}
        className="absolute right-[50%] mr-[12px] font-mono text-[8px] md:text-[9px] font-bold uppercase tracking-widest text-right z-10"
      >
        {key1}
      </motion.div>

      {/* Middle Right (Pushed dynamically by perfectly round physical curve) */}
      <motion.div
        style={{ x: xRight }}
        className="absolute left-[50%] ml-[12px] font-mono text-[8px] md:text-[9px] font-bold uppercase tracking-widest text-left z-10"
      >
        {key2}
      </motion.div>

      {/* Extreme Right */}
      <div className="absolute right-4 md:right-8 font-mono text-[8px] md:text-[9px] font-bold uppercase tracking-widest text-right z-10">
        {ip}
      </div>
    </motion.div>
  );
};

export function InventoryScroll() {
  return (
    <section id="global-topology" className="w-full bg-obsidian relative scroll-mt-20">
      
      {/* Header */}
      <div className="text-center pt-32 pb-[15vh]">
        <h2 className="text-[8vw] md:text-[5vw] font-sans font-black tracking-tighter text-white uppercase leading-none mb-6">
          PRESENT IN OVER 300<br/>NETWORKS WORLDWIDE.
        </h2>
        <p className="text-neutral-400 text-sm max-w-xl mx-auto font-medium px-4">
          Teams on the ground in 300+ networks allow us to connect decisions, movement, and protection across regions without losing local context.
        </p>
      </div>

      <div className="relative w-full">
        
        {/* The sticky target reticle wrapper */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none z-20">
          <div className="sticky top-1/2 w-full flex justify-center h-0">
            {/* The ring container */}
            <div className="w-24 h-24 md:w-[130px] md:h-[130px] rounded-full flex items-center justify-center relative -translate-y-1/2">
              
              {/* Radial Ticks (Compass/Dial) rotating continuously */}
              <div className="absolute inset-0 flex items-center justify-center animate-[spin_30s_linear_infinite] z-10">
                <svg viewBox="0 0 100 100" className="w-full h-full text-neutral-500 opacity-60 pointer-events-none">
                  {Array.from({ length: 72 }).map((_, i) => (
                    <line 
                      key={i} 
                      x1="50" y1="2" x2="50" y2="10" 
                      stroke="currentColor" 
                      strokeWidth={i % 2 === 0 ? "1.5" : "0.5"} 
                      transform={`rotate(${i * 5} 50 50)`} 
                    />
                  ))}
                </svg>
              </div>

              {/* Separated Logo - remains small in the center */}
              <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="8" strokeLinecap="round" className="w-10 h-10 md:w-12 md:h-12 text-brand-orange relative z-20">
                <path d="M 45,15 Q 35,35 15,45" />
                <path d="M 85,45 Q 65,35 55,15" />
                <path d="M 15,55 Q 35,65 45,85" />
                <path d="M 55,85 Q 65,65 85,55" />
              </svg>
            </div>
          </div>
        </div>

        {/* Scrollable list data */}
        <div className="w-full flex flex-col relative z-10">
          <div className="w-full flex flex-col pt-[30vh] pb-[30vh]">
            {data.map((item, index) => (
              <Row 
                key={index} 
                protocol={item.protocol} 
                key1={item.key1} 
                key2={item.key2} 
                ip={item.ip} 
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
