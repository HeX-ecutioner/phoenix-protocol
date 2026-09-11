import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export function Navbar() {
  const location = useLocation();
  const isAbout = location.pathname === '/about';

  return (
    <nav className="w-full flex items-center justify-between px-6 py-4 bg-obsidian/80 backdrop-blur-md sticky top-0 z-50">
      {/* Left: Minimalist futuristic logo */}
      <Link to="/" className="flex items-center gap-2 md:gap-3 group z-50">
        <div className="w-6 h-6 md:w-8 md:h-8 flex items-center justify-center text-white group-hover:text-brand-orange transition-colors duration-300 relative">
          <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="6" className="absolute inset-0 w-full h-full">
            <path d="M 50,0 Q 40,50 0,50 Q 40,50 50,100 Q 60,50 100,50 Q 60,50 50,0" />
            <line x1="50" y1="0" x2="50" y2="100" strokeWidth="2" stroke="currentColor" opacity="0.3" />
          </svg>
        </div>
        <span className="font-sans font-black tracking-widest text-white text-sm md:text-base uppercase group-hover:text-neutral-300 transition-colors">
          PHOENIX
        </span>
      </Link>

      {/* Center: Clean navigation links */}
      <div className="absolute left-1/2 -translate-x-1/2 hidden md:flex items-center gap-8">
        <Link 
          to="/about" 
          className={`transition-colors text-xs font-bold tracking-widest uppercase ${
            isAbout ? 'text-brand-orange' : 'text-neutral-400 hover:text-brand-orange'
          }`}
        >
          ABOUT SPEC
        </Link>
        <Link 
          to="/#global-topology" 
          className="text-neutral-400 hover:text-brand-orange transition-colors text-xs font-bold tracking-widest uppercase"
        >
          GLOBAL TOPOLOGY
        </Link>
      </div>

      {/* Right: Action button navigating to About Page */}
      <div className="flex items-center">
        <Link 
          to={isAbout ? "/" : "/about"} 
          className={`flex items-center gap-4 pl-5 pr-1 py-1 rounded-full border transition-all duration-300 group ${
            isAbout 
              ? 'border-brand-orange/60 bg-brand-orange/10 shadow-[0_0_20px_rgba(234,88,20,0.2)]' 
              : 'border-neutral-800 hover:border-neutral-600 bg-black/40 hover:bg-neutral-900/60'
          }`}
        >
          <span className={`text-xs font-bold tracking-[0.2em] uppercase transition-colors ${
            isAbout ? 'text-brand-orange' : 'text-white'
          }`}>
            {isAbout ? 'BACK TO SCANNER' : 'READ-ONLY MODE'}
          </span>
          <div className="w-8 h-8 rounded-full bg-brand-orange flex items-center justify-center group-hover:scale-105 transition-transform">
            {isAbout ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" className="w-4 h-4 ml-0.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            )}
          </div>
        </Link>
      </div>
    </nav>
  );
}
