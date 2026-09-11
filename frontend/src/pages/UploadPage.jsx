import React from 'react';
import { useLocation } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Hero } from '../components/Hero';
import { ScannerConsole } from '../components/ScannerConsole';
import { Features } from '../components/Features';
import { ScanNotes } from '../components/ScanNotes';
import { Footer } from '../components/Footer';
import { PageTransition } from '../components/motion/PageTransition';
import { InventoryScroll } from '../components/InventoryScroll';

export function UploadPage() {
  const location = useLocation();
  const [isHeroLoaded, setIsHeroLoaded] = React.useState(false);
  const [heroKey, setHeroKey] = React.useState(1);

  React.useEffect(() => {
    window.scrollTo(0, 0);
    setIsHeroLoaded(false);
    setHeroKey(prev => prev + 1);
  }, [location]);

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian">
        <div className={`fixed top-0 w-full z-50 transition-opacity duration-1000 ${isHeroLoaded ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
          <Navbar />
        </div>
        
        <main className="flex-1 w-full relative z-10">
          <Hero key={heroKey} onLoadComplete={() => setIsHeroLoaded(true)} />
          
          <div id="upload-section" className="min-h-screen flex items-center justify-center">
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
