import React from 'react';
import { Navbar } from '../components/Navbar';
import { Hero } from '../components/Hero';
import { ScannerConsole } from '../components/ScannerConsole';
import { Features } from '../components/Features';
import { ScanNotes } from '../components/ScanNotes';
import { Footer } from '../components/Footer';
import { PageTransition } from '../components/motion/PageTransition';
import { Marquee } from '../components/motion/Marquee';
import { InventoryScroll } from '../components/InventoryScroll';

export function UploadPage() {
  const [isHeroLoaded, setIsHeroLoaded] = React.useState(false);

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian">
        <div className={`fixed top-0 w-full z-50 transition-opacity duration-1000 ${isHeroLoaded ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
          <Navbar />
        </div>
        
        <main className="flex-1 w-full relative z-10">
          <Hero onLoadComplete={() => setIsHeroLoaded(true)} />
          
          <div className="min-h-screen flex items-center justify-center">
            <ScannerConsole />
          </div>

          <InventoryScroll />
          
          <Features />
          <ScanNotes />
        </main>

        <Footer />
      </div>
    </PageTransition>
  );
}
