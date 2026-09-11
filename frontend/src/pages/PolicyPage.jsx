import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, FileText, Lock, Cookie, Terminal } from 'lucide-react';
import { PageTransition } from '../components/motion/PageTransition';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';

const POLICIES = {
  cookies: {
    docId: "POL_COOKIE_v2.1",
    tag: "TELEMETRY & COOKIE DIRECTIVE",
    title: "COOKIE POLICY",
    subtitle: "STRICT MINIMALISM & ZERO THIRD-PARTY TRACKING ASSURANCE",
    lastUpdated: "SEPTEMBER 2026",
    sections: [
      {
        index: "01 // PHILOSOPHY",
        title: "ZERO TRACKING INVENTORY",
        content: "Phoenix Protocol rejects behavioral trackers, ad-network cookies, and surveillance pixels. We operate strictly as an evidence-first, read-only network compliance tool. The application is architected to perform entirely without non-essential cookies."
      },
      {
        index: "02 // STRICTLY ESSENTIAL CACHE",
        title: "EPHEMERAL SESSION STORAGE",
        content: "The application utilizes browser LocalStorage and SessionStorage solely for active parser session continuity (e.g., maintaining parsed device metadata while navigating between dashboard tabs). No configuration data or network topology ever leaves your client browser without explicit submission."
      },
      {
        index: "03 // OPT-OUT & CONTROL",
        title: "FULL CLIENT CONTROL",
        content: "Users may clear their browser cache, disable localStorage, or execute an incognito/private session at any time. Phoenix Protocol will continue to process uploaded configuration files identically without state persistence."
      }
    ]
  },
  terms: {
    docId: "POL_TERMS_v4.0",
    tag: "AIR-GAPPED COMPLIANCE AGREEMENT",
    title: "TERMS OF USE",
    subtitle: "LEGAL SPECIFICATIONS GOVERNING STATIC CONFIGURATION AUDITING",
    lastUpdated: "SEPTEMBER 2026",
    sections: [
      {
        index: "01 // READ-ONLY GUARANTEE",
        title: "NON-INTRUSIVE STATIC PARSING",
        content: "Phoenix Protocol is provided strictly for offline, read-only configuration verification. The system does not initiate active network discovery, does not issue live operational commands, and possesses no mechanism to push configuration changes to production network equipment."
      },
      {
        index: "02 // USER AUTHORIZATION",
        title: "INPUT DATA RESPONSIBILITY",
        content: "Users affirm that they possess lawful authorization to review and evaluate any network device configuration files submitted to the system. You agree not to upload maliciously corrupted binaries or malicious payloads designed to subvert parser integrity."
      },
      {
        index: "03 // NO WARRANTY & PRODUCTION RISK",
        title: "DETERMINISTIC BEST-EFFORT COMPLIANCE",
        content: "Rule assessments are conducted strictly against transparent, deterministic baseline rule definitions. While Phoenix Protocol strives for 100% syntactic precision across vendor configurations, compliance scores represent automated advisory evaluations and do not replace certified architectural review."
      }
    ]
  },
  privacy: {
    docId: "POL_PRIVACY_v3.2",
    tag: "ZERO-PERSISTENCE SECURITY POLICY",
    title: "PRIVACY POLICY",
    subtitle: "HOW PHOENIX PROTOCOL PROTECTS NETWORK CONFIGURATION SECRETS",
    lastUpdated: "SEPTEMBER 2026",
    sections: [
      {
        index: "01 // AIR-GAPPED PRIVACY",
        title: "SECRET SANITIZATION & REDACTION",
        content: "Phoenix Protocol automatically sanitizes and redacts plaintext passwords, Type 7 encrypted strings, MD5/SHA-256 hashes, and SNMP community strings during the initial lexical tokenization phase. Secrets are scrubbed prior to rule engine evaluation."
      },
      {
        index: "02 // DATA RETENTION STANDARD",
        title: "ZERO PERMANENT ARCHIVAL",
        content: "Exported network device configurations are processed ephemerally in volatile memory. Configuration blocks are retained only for the active audit session to generate the compliance findings report and are discarded immediately upon session termination."
      },
      {
        index: "03 // THIRD-PARTY EXCLUSION",
        title: "NO TELEMETRY EXFILTRATION",
        content: "Under no circumstances are uploaded topology maps, device hostnames, IP address allocations, or vulnerability findings transmitted to third-party advertisers, cloud telemetry brokers, or outside vendors."
      }
    ]
  }
};

export function PolicyPage({ type = 'cookies' }) {
  const navigate = useNavigate();
  const policy = POLICIES[type] || POLICIES.cookies;

  React.useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [type]);

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian text-white relative selection:bg-brand-orange selection:text-white">
        
        {/* Ambient Brutalist Background Grid */}
        <div className="fixed inset-0 pointer-events-none z-0">
          <div className="absolute inset-0 bg-grid opacity-50" />
          <div className="absolute top-0 right-0 w-96 h-96 bg-brand-orange/5 rounded-full blur-[140px] pointer-events-none" />
        </div>

        {/* Top Navbar */}
        <div className="sticky top-0 w-full z-50">
          <Navbar />
        </div>

        <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-12 md:py-20 relative z-10 flex flex-col gap-12">
          
          {/* Brutalist Back Button */}
          <div className="flex items-center justify-between">
            <button 
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-3 px-5 py-2.5 bg-neutral-900 border border-neutral-800 hover:border-brand-orange text-neutral-300 hover:text-white font-mono text-xs font-bold tracking-widest uppercase transition-all duration-200 group"
            >
              <ArrowLeft className="w-4 h-4 text-brand-orange group-hover:-translate-x-1 transition-transform" />
              <span>RETURN TO PREVIOUS VIEW</span>
            </button>

            <Link 
              to="/#upload-section"
              className="font-mono text-xs text-neutral-500 hover:text-brand-orange transition-colors uppercase tracking-widest hidden sm:inline-block"
            >
              LAUNCH SCANNER →
            </Link>
          </div>

          {/* Header Block */}
          <section className="flex flex-col gap-4 border-b border-neutral-800 pb-10">
            <div className="flex flex-wrap items-center gap-3">
              <span className="px-3 py-1 bg-brand-orange/10 border border-brand-orange/30 text-brand-orange font-mono text-[11px] font-black uppercase tracking-widest">
                {policy.docId}
              </span>
              <span className="px-3 py-1 bg-white/5 border border-white/10 text-neutral-400 font-mono text-[11px] uppercase tracking-wider">
                {policy.tag}
              </span>
              <span className="px-3 py-1 bg-white/5 border border-white/10 text-neutral-500 font-mono text-[11px] uppercase tracking-wider ml-auto">
                REVISION // {policy.lastUpdated}
              </span>
            </div>

            <h1 className="text-4xl sm:text-6xl md:text-7xl font-black uppercase tracking-tighter text-white mt-2">
              {policy.title}
            </h1>
            
            <p className="font-mono text-xs sm:text-sm text-neutral-400 tracking-wider uppercase max-w-3xl">
              {policy.subtitle}
            </p>
          </section>

          {/* Policy Content Sections (Brutalist Minimalist Stack) */}
          <section className="flex flex-col gap-8">
            {policy.sections.map((sec, idx) => (
              <div 
                key={idx}
                className="border-2 border-neutral-900 bg-black/40 hover:border-neutral-800 p-8 md:p-10 transition-colors relative"
              >
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-900 font-mono text-xs">
                  <span className="text-brand-orange font-black tracking-widest">{sec.index}</span>
                  <span className="text-neutral-600 uppercase">ENFORCED // PASSIVE</span>
                </div>

                <h2 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-white mb-4">
                  {sec.title}
                </h2>

                <p className="text-neutral-400 font-sans text-sm sm:text-base leading-relaxed">
                  {sec.content}
                </p>
              </div>
            ))}
          </section>

          {/* Bottom Navigation Call to Action */}
          <section className="mt-8 pt-10 border-t border-neutral-800 flex flex-col sm:flex-row items-center justify-between gap-6">
            <button 
              onClick={() => navigate('/')}
              className="inline-flex items-center gap-3 px-6 py-3.5 bg-black border border-neutral-800 hover:border-white text-neutral-400 hover:text-white font-mono text-xs font-bold tracking-widest uppercase transition-colors"
            >
              <ArrowLeft className="w-4 h-4 text-brand-orange" />
              <span>BACK TO MAIN DASHBOARD</span>
            </button>

            <Link 
              to="/"
              state={{ showLoader: true }}
              className="inline-flex items-center gap-3 px-6 py-3.5 bg-brand-orange hover:bg-orange-500 text-white font-mono text-xs font-black tracking-widest uppercase transition-colors shadow-lg"
            >
              <span>RETURN TO SCANNER</span>
              <Terminal className="w-4 h-4" />
            </Link>
          </section>

        </main>

        <Footer />
      </div>
    </PageTransition>
  );
}

export default PolicyPage;
