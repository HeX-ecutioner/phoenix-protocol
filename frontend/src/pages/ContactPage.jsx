import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, 
  Send, 
  Mail, 
  Phone, 
  MapPin, 
  ShieldAlert, 
  CheckCircle2, 
  Copy, 
  Terminal,
  Cpu,
  Lock
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { PageTransition } from '../components/motion/PageTransition';

export function ContactPage() {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    organization: '',
    networkScale: '50-500 Nodes',
    message: ''
  });

  React.useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, []);

  const handleCopyEmail = () => {
    navigator.clipboard.writeText('SECURE@PHOENIX-PROTOCOL.COM');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian text-white relative selection:bg-brand-orange selection:text-white">
        
        {/* Ambient background grid & glow */}
        <div className="fixed inset-0 pointer-events-none z-0">
          <div className="absolute inset-0 bg-grid opacity-50" />
          <div className="absolute top-1/4 right-1/4 w-[600px] h-[600px] bg-radial-glow pointer-events-none blur-3xl opacity-70" />
        </div>

        {/* Top Navbar */}
        <div className="sticky top-0 w-full z-50">
          <Navbar />
        </div>

        <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-12 md:py-20 relative z-10 flex flex-col gap-16">
          
          {/* Top navigation row with Brutalist Back Button */}
          <div className="flex items-center justify-between">
            <button 
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-3 px-5 py-2.5 bg-neutral-900 border border-neutral-800 hover:border-brand-orange text-neutral-300 hover:text-white font-mono text-xs font-bold tracking-widest uppercase transition-all duration-200 group"
            >
              <ArrowLeft className="w-4 h-4 text-brand-orange group-hover:-translate-x-1 transition-transform" />
              <span>RETURN TO PREVIOUS VIEW</span>
            </button>

            <Link 
              to="/"
              className="font-mono text-xs text-neutral-500 hover:text-brand-orange transition-colors uppercase tracking-widest hidden sm:inline-block"
            >
              LAUNCH SCANNER →
            </Link>
          </div>

          {/* Header Section */}
          <section className="flex flex-col gap-6 border-b border-neutral-800 pb-12">
            <div className="flex flex-wrap items-center gap-3">
              <span className="px-3 py-1 bg-brand-orange/10 border border-brand-orange/30 text-brand-orange font-mono text-[11px] font-black uppercase tracking-widest">
                DISPATCH // COMMS_CHANNEL_01
              </span>
              <span className="px-3 py-1 bg-white/5 border border-white/10 text-neutral-400 font-mono text-[11px] uppercase tracking-wider">
                STATUS: DIRECT_ENGAGEMENT
              </span>
              <span className="px-3 py-1 bg-white/5 border border-white/10 text-emerald-400 font-mono text-[11px] uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> SQUAD READY
              </span>
            </div>

            <h1 className="text-4xl sm:text-6xl md:text-7xl font-black uppercase tracking-tighter text-white">
              WORK WITH US <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-orange via-orange-400 to-amber-200">
                THE COASTAL ASSASINS
              </span>
            </h1>

            <p className="font-sans text-base sm:text-lg text-neutral-400 max-w-3xl leading-relaxed">
              Whether you need customized compliance rules for proprietary network gear, air-gapped enterprise deployments, or full infrastructure config auditing, our protocol engineering squad is ready for deployment.
            </p>
          </section>

          {/* Form & Direct Comms Grid */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            
            {/* Left: Direct Dispatch Form (Brutalist + Glassmorphic) */}
            <div className="lg:col-span-7">
              <div className="backdrop-blur-xl bg-neutral-950/60 border-2 border-neutral-800 p-8 md:p-10 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-2 h-full bg-brand-orange" />
                
                <div className="flex items-center justify-between pb-6 mb-6 border-b border-neutral-800/80">
                  <div>
                    <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">ENCRYPTED INQUIRY</span>
                    <h2 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-white mt-0.5">
                      TRANSMIT MISSION BRIEF
                    </h2>
                  </div>
                  <Terminal className="w-5 h-5 text-neutral-600" />
                </div>

                <AnimatePresence mode="wait">
                  {submitted ? (
                    <motion.div 
                      key="success"
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="py-12 flex flex-col items-center justify-center text-center gap-4"
                    >
                      <div className="w-16 h-16 rounded-full bg-brand-orange/10 border border-brand-orange/40 flex items-center justify-center text-brand-orange">
                        <CheckCircle2 className="w-8 h-8" />
                      </div>
                      <h3 className="text-2xl font-black uppercase tracking-tight text-white">
                        TRANSMISSION LOGGED // RECEIVED
                      </h3>
                      <p className="font-mono text-xs text-neutral-400 max-w-md">
                        Your inquiry has been assigned ticket <span className="text-brand-orange">#PX-{(Math.random() * 9000 + 1000).toFixed(0)}</span>. A Coastal Assasins security engineer will respond within 2 hours.
                      </p>
                      <button 
                        onClick={() => setSubmitted(false)}
                        className="mt-4 px-6 py-2.5 bg-neutral-900 border border-neutral-800 hover:border-brand-orange text-xs font-mono font-bold uppercase tracking-widest text-neutral-300"
                      >
                        TRANSMIT ANOTHER BRIEF
                      </button>
                    </motion.div>
                  ) : (
                    <form key="form" onSubmit={handleSubmit} className="flex flex-col gap-5">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="flex flex-col gap-2">
                          <label className="font-mono text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                            CALLSIGN / FULL NAME *
                          </label>
                          <input 
                            type="text" 
                            required
                            placeholder="Alex Mercer"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full bg-black/60 border border-neutral-800 focus:border-brand-orange px-4 py-3 text-sm text-white font-mono placeholder:text-neutral-700 outline-none transition-colors"
                          />
                        </div>

                        <div className="flex flex-col gap-2">
                          <label className="font-mono text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                            DIRECT EMAIL *
                          </label>
                          <input 
                            type="email" 
                            required
                            placeholder="alex@enterprise.corp"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            className="w-full bg-black/60 border border-neutral-800 focus:border-brand-orange px-4 py-3 text-sm text-white font-mono placeholder:text-neutral-700 outline-none transition-colors"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="flex flex-col gap-2">
                          <label className="font-mono text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                            ORGANIZATION / DOMAIN
                          </label>
                          <input 
                            type="text" 
                            placeholder="Cyberdyne Networks"
                            value={formData.organization}
                            onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                            className="w-full bg-black/60 border border-neutral-800 focus:border-brand-orange px-4 py-3 text-sm text-white font-mono placeholder:text-neutral-700 outline-none transition-colors"
                          />
                        </div>

                        <div className="flex flex-col gap-2">
                          <label className="font-mono text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                            NETWORK FLEET SCALE
                          </label>
                          <select 
                            value={formData.networkScale}
                            onChange={(e) => setFormData({ ...formData, networkScale: e.target.value })}
                            className="w-full bg-black/60 border border-neutral-800 focus:border-brand-orange px-4 py-3 text-sm text-white font-mono outline-none transition-colors"
                          >
                            <option value="< 50 Nodes">&lt; 50 NODES (SMB FLEET)</option>
                            <option value="50-500 Nodes">50 - 500 NODES (MID MARKET)</option>
                            <option value="500-5000 Nodes">500 - 5,000 NODES (ENTERPRISE)</option>
                            <option value="5000+ Nodes">5,000+ NODES (CARRIER / TELCO)</option>
                          </select>
                        </div>
                      </div>

                      <div className="flex flex-col gap-2">
                        <label className="font-mono text-[10px] font-bold uppercase tracking-widest text-neutral-400">
                          MISSION BRIEF / AUDIT REQUIREMENTS *
                        </label>
                        <textarea 
                          rows={4}
                          required
                          placeholder="Describe target vendor architectures (Cisco, Arista, Juniper), specific CIS benchmarks needed, or custom compliance rule requests..."
                          value={formData.message}
                          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                          className="w-full bg-black/60 border border-neutral-800 focus:border-brand-orange p-4 text-sm text-white font-mono placeholder:text-neutral-700 outline-none transition-colors resize-none"
                        />
                      </div>

                      <button 
                        type="submit"
                        className="mt-2 w-full py-4 bg-brand-orange hover:bg-orange-500 text-white font-mono font-black text-xs uppercase tracking-[0.25em] flex items-center justify-center gap-3 transition-all duration-300 shadow-[0_0_20px_rgba(234,88,20,0.3)]"
                      >
                        <span>TRANSMIT INQUIRY TO SQUAD</span>
                        <Send className="w-4 h-4" />
                      </button>
                    </form>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Right: Telemetry & Direct Channels */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              
              {/* Direct Email Card with One-Click Copy */}
              <div className="backdrop-blur-xl bg-neutral-900/40 border border-neutral-800 p-6 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">DIRECT CONTACT</span>
                  <Mail className="w-4 h-4 text-neutral-500" />
                </div>

                <div>
                  <span className="font-mono text-[10px] text-neutral-500 uppercase tracking-widest block">SECURE DISPATCH INBOX</span>
                  <div className="flex items-center justify-between mt-1 bg-black/60 border border-neutral-800/80 px-4 py-3">
                    <span className="font-mono text-sm font-bold text-white tracking-wider">
                      SECURE@PHOENIX-PROTOCOL.COM
                    </span>
                    <button 
                      onClick={handleCopyEmail}
                      title="Copy email to clipboard"
                      className="text-neutral-400 hover:text-brand-orange transition-colors p-1"
                    >
                      {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="bg-black/40 border border-neutral-800/60 p-3 font-mono text-[11px]">
                    <span className="text-neutral-500 block">INDIA HQ</span>
                    <span className="text-neutral-200 font-bold mt-0.5 block">+91 98765 43210</span>
                  </div>
                  <div className="bg-black/40 border border-neutral-800/60 p-3 font-mono text-[11px]">
                    <span className="text-neutral-500 block">EUROPE DESK</span>
                    <span className="text-neutral-200 font-bold mt-0.5 block">+44 20 7946 0958</span>
                  </div>
                </div>
              </div>

              {/* Physical Lab Node */}
              <div className="backdrop-blur-xl bg-neutral-900/40 border border-neutral-800 p-6 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">OPERATIONAL BASE</span>
                  <MapPin className="w-4 h-4 text-neutral-500" />
                </div>

                <div className="font-mono text-xs text-neutral-300 leading-relaxed">
                  <strong className="text-white block text-sm font-bold mb-1">THE COASTAL ASSASINS LAB</strong>
                  KOLKATA, WEST BENGAL<br />
                  INDIA — PIN 700091
                </div>

                <div className="p-3 bg-white/[0.02] border border-neutral-800 text-[11px] font-mono text-neutral-400 flex items-center gap-2">
                  <Lock className="w-4 h-4 text-brand-orange shrink-0" />
                  <span>Physical visits by prior cryptographic appointment only.</span>
                </div>
              </div>

              {/* Squad Creed */}
              <div className="backdrop-blur-xl bg-gradient-to-br from-neutral-900/40 to-neutral-950/60 border border-neutral-800 p-6 flex flex-col gap-2">
                <span className="font-mono text-[10px] text-brand-orange font-bold uppercase tracking-widest">SQUAD DIRECTIVE</span>
                <p className="font-sans text-xs text-neutral-400 leading-relaxed">
                  "Evidence-first analysis. Zero production risk. We engineer tools that give infrastructure teams total certainty without compromise."
                </p>
              </div>

            </div>

          </section>

        </main>

        <Footer />
      </div>
    </PageTransition>
  );
}

export default ContactPage;
