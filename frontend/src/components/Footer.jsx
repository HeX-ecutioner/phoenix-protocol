import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="w-full relative bg-obsidian overflow-hidden min-h-screen flex flex-col justify-between pt-32 border-t border-neutral-900">
      {/* Background Geometric Arcs (Brutalist White on Dark) */}
      <div className="absolute inset-0 z-0 flex items-center justify-center pointer-events-none opacity-[0.03]">
        <svg viewBox="0 0 1000 500" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" className="absolute top-0 w-full h-full">
          {/* Top Left Arc */}
          <path d="M 0,0 A 300,300 0 0,0 300,300 L 400,300 A 400,400 0 0,1 0,-100 Z" fill="white" />
          {/* Top Right Arc */}
          <path d="M 1000,0 A 300,300 0 0,1 700,300 L 600,300 A 400,400 0 0,0 1000,-100 Z" fill="white" />
          {/* Bottom Center Arc */}
          <path d="M 300,500 A 200,200 0 0,1 700,500 L 800,500 A 300,300 0 0,0 200,500 Z" fill="white" />
        </svg>
      </div>

      <div className="relative z-10 flex-1 flex flex-col items-center justify-center">
        {/* Contact Info (Brutalist Typography) */}
        <div className="text-center space-y-6 pb-24">
          <div>
            <p className="text-[10px] text-neutral-500 uppercase tracking-widest font-mono mb-1">Address</p>
            <p className="text-sm md:text-base text-white font-bold uppercase tracking-wider">
              KOLKATA, WEST BENGAL<br/>INDIA
            </p>
          </div>
          <div>
            <p className="text-[10px] text-neutral-500 uppercase tracking-widest font-mono mb-1">Phone Number</p>
            <p className="text-sm md:text-base text-white font-bold uppercase tracking-wider">
              (IN) +91 98765 43210<br/>(EU) +44 20 7946 0958
            </p>
          </div>
          <div>
            <p className="text-[10px] text-neutral-500 uppercase tracking-widest font-mono mb-1">Email</p>
            <p className="text-sm md:text-base text-white font-bold uppercase tracking-wider">
              SECURE@PHOENIX-PROTOCOL.COM
            </p>
          </div>
          <div className="pt-4">
            <p className="text-[10px] text-neutral-600 font-mono tracking-widest uppercase">
              © 2026 PHOENIX PROTOCOL. ALL RIGHTS RESERVED.
            </p>
          </div>
        </div>
      </div>

      {/* Pill Button from Image 2 (Positioned bottom right above sub-footer) */}
      <div className="absolute bottom-24 right-6 md:right-12 z-20 hidden md:block">
        <Link to="/contact">
          <motion.button 
            className="flex items-center gap-6 px-8 py-4 bg-[#e24423] rounded-full text-white hover:bg-[#ff4d26] transition-colors shadow-2xl group border border-white/10"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <span className="font-mono text-sm font-bold uppercase tracking-[0.25em] pl-2">WORK WITH US</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="w-5 h-5 group-hover:translate-x-1 transition-transform">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </motion.button>
        </Link>
      </div>

      {/* Sub Footer (Black Bar) */}
      <div className="w-full bg-black py-6 px-6 md:px-12 flex flex-col md:flex-row items-center justify-between text-[9px] md:text-[10px] font-mono text-neutral-500 tracking-[0.2em] uppercase z-10 border-t border-neutral-900">
        <div>
          CRAFTED BY PHOENIX TEAM
        </div>
        <div className="flex gap-4 md:gap-8 my-4 md:my-0">
          <a href="#" className="hover:text-white transition-colors">COOKIE POLICY</a>
          <span>/</span>
          <a href="#" className="hover:text-white transition-colors">TERMS OF USE</a>
          <span>/</span>
          <a href="#" className="hover:text-white transition-colors">PRIVACY POLICY</a>
        </div>
        <div className="flex gap-4">
          <a href="#" className="hover:text-white transition-colors">LINKEDIN</a>
          <span>/</span>
          <a href="#" className="hover:text-white transition-colors">GITHUB</a>
        </div>
      </div>
    </footer>
  );
}
