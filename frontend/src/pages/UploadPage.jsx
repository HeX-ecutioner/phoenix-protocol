import React from 'react';
import { useLocation } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Hero } from '../components/Hero';
import { ScannerConsole } from '../components/ScannerConsole';
import { Features } from '../components/Features';
import { ScanNotes } from '../components/ScanNotes';
import { Footer } from '../components/Footer';
import { PageTransition } from '../components/motion/PageTransition';
import { LoadingScreen } from '../components/motion/LoadingScreen';
import { Marquee } from '../components/motion/Marquee';
import { InventoryScroll } from '../components/InventoryScroll';

export function UploadPage() {
  const location = useLocation();
  // Always start with the loading animation on page refresh or initial mount
  const [showLoader, setShowLoader] = React.useState(true);
  const [isHeroLoaded, setIsHeroLoaded] = React.useState(false);
  const [heroKey, setHeroKey] = React.useState(1);

  React.useEffect(() => {
    if (location.state?.showLoader) {
      window.scrollTo(0, 0);
      setShowLoader(true);
      setIsHeroLoaded(false);
      setHeroKey(prev => prev + 1);
    } else {
      window.scrollTo(0, 0);
    }
  }, [location]);

  const handleLoadingComplete = () => {
    setShowLoader(false);
    setIsHeroLoaded(true);
  };

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian">
        {showLoader && (
          <LoadingScreen 
            onComplete={handleLoadingComplete} 
            duration={1800} 
            message="INITIALIZING SECURE SCANNER CONSOLE"
          />
        )}

        <div className={`fixed top-0 w-full z-50 transition-opacity duration-1000 ${isHeroLoaded && !showLoader ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
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
