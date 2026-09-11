import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { PageTransition } from '../components/motion/PageTransition';
import { 
  ShieldCheck, 
  Terminal, 
  Lock, 
  Cpu, 
  FileCode, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight,
  Radio,
  Server,
  Fingerprint,
  Zap
} from 'lucide-react';

export function AboutPage() {
  React.useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, []);

  const pillars = [
    {
      code: "ARCH_01",
      title: "AIR-GAPPED & ZERO-TOUCH",
      badge: "NON-INVASIVE",
      description: "Phoenix Protocol strictly analyzes exported, offline configuration snapshots. It requires zero live SSH credentials, SNMP write strings, or production network access.",
      highlight: "Guarantees 0% outage risk across mission-critical networks."
    },
    {
      code: "ARCH_02",
      title: "DETERMINISTIC EVALUATION",
      badge: "ZERO AMBIGUITY",
      description: "No hallucinated policy interpretations. Every security check is verified against strict, mathematical AST parsing and vendor-specific syntax grammars.",
      highlight: "Every pass or fail is 100% reproducible and verifiable."
    },
    {
      code: "ARCH_03",
      title: "EVIDENCE-FIRST AUDIT TRAILS",
      badge: "EXACT CITATIONS",
      description: "Unlike opaque scanners that return vague ratings, Phoenix Protocol extracts the exact line numbers, configuration blocks, and context tokens proving each finding.",
      highlight: "Audit-ready reports suitable for SOC2, ISO 27001, and CIS benchmarks."
    },
    {
      code: "ARCH_04",
      title: "MULTI-VENDOR SYNTAX ENGINE",
      badge: "UNIFIED SCHEMA",
      description: "Normalizes heterogeneous configurations across Cisco IOS, IOS-XE, NX-OS, Arista EOS, and Juniper Junos into a clean, canonical compliance data model.",
      highlight: "Unified posture analysis across hybrid network fleets."
    }
  ];

  const ruleCatalog = [
    { id: "NET-SEC-001", control: "Telnet Service Disabled", severity: "CRITICAL", cat: "TRANSPORT" },
    { id: "NET-SEC-002", control: "SSH v2 Strict Enforcement", severity: "HIGH", cat: "AUTHENTICATION" },
    { id: "NET-SEC-003", control: "Type 7 / Plaintext Secret Ban", severity: "CRITICAL", cat: "CREDENTIALS" },
    { id: "NET-SEC-004", control: "VTY Line Access Class (ACL)", severity: "HIGH", cat: "ACCESS_CONTROL" },
    { id: "NET-SEC-005", control: "Centralized Remote Syslog", severity: "MEDIUM", cat: "TELEMETRY" },
    { id: "NET-SEC-006", control: "NTP Synchronization & Auth", severity: "MEDIUM", cat: "CLOCK_SYNC" }
  ];

  const techSpecs = [
    { label: "ENGINE_CORE", value: "Phoenix Deterministic AST v2.4" },
    { label: "EXECUTION_MODE", value: "Read-Only / Air-Gapped / Static" },
    { label: "SUPPORTED_TARGETS", value: "Cisco IOS/NX-OS, Arista EOS, Junos" },
    { label: "OUTPUT_FORMATS", value: "JSON AST, Executive SARIF, Human Matrix" },
    { label: "INTEGRITY_CHECK", value: "SHA-256 Digest Per Device Config" },
    { label: "DEPLOYMENT", value: "Stateless / Zero Data Persistence" }
  ];

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian text-white relative selection:bg-brand-orange selection:text-white">
        
        {/* Ambient brutalist background grid & glowing glass backdrops */}
        <div className="fixed inset-0 pointer-events-none z-0">
          <div className="absolute inset-0 bg-grid opacity-60" />
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-radial-glow pointer-events-none blur-3xl opacity-80" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-brand-orange/5 rounded-full blur-[140px] pointer-events-none" />
        </div>

        {/* Top Navbar */}
        <div className="sticky top-0 w-full z-50">
          <Navbar />
        </div>

        <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-12 md:py-20 relative z-10 flex flex-col gap-16 md:gap-24">
          
          {/* Section 1: Brutalist Glassmorphic Hero */}
          <section className="flex flex-col gap-6">
            <div className="flex flex-wrap items-center gap-3">
              <span className="px-3 py-1 bg-brand-orange/10 border border-brand-orange/40 text-brand-orange font-mono text-[11px] font-black uppercase tracking-widest rounded-none">
                PROTOCOL SPEC // SYS_DOC_01
              </span>
              <span className="px-3 py-1 backdrop-blur-md bg-white/5 border border-white/10 text-neutral-400 font-mono text-[11px] uppercase tracking-wider">
                STATUS: READ_ONLY_ENFORCED
              </span>
              <span className="hidden sm:inline-flex px-3 py-1 backdrop-blur-md bg-white/5 border border-white/10 text-emerald-400 font-mono text-[11px] uppercase tracking-wider items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> AIR-GAP VERIFIED
              </span>
            </div>

            {/* Brutalist Hero Title with Glassmorphic Accent */}
            <div className="relative">
              <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black uppercase tracking-tighter leading-[0.95] text-white">
                SAFE, EVIDENCE-FIRST <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-orange via-orange-400 to-amber-200">
                  NETWORK COMPLIANCE
                </span>
              </h1>
              <p className="mt-6 max-w-3xl text-neutral-400 font-sans text-base sm:text-lg md:text-xl font-normal leading-relaxed">
                Phoenix Protocol is an autonomous configuration compliance engine crafted for small teams and enterprise auditors. By decoupling security rule evaluation from active device infrastructure, it provides cryptographic assurance with <strong className="text-white font-bold">absolute zero production downtime risk</strong>.
              </p>
            </div>

            {/* Glassmorphic Metrics Quickbar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
              {[
                { label: "PRODUCTION_TOUCH", val: "0.00%", sub: "Zero write calls" },
                { label: "RULE_CERTAINTY", val: "100%", sub: "Deterministic AST" },
                { label: "PARSER_LATENCY", val: "< 18ms", sub: "Instant tokenization" },
                { label: "EVIDENCE_PRECISION", val: "EXACT", sub: "Line-by-line proof" }
              ].map((m, idx) => (
                <div 
                  key={idx} 
                  className="backdrop-blur-xl bg-neutral-900/40 border border-neutral-800/80 hover:border-brand-orange/40 transition-all duration-300 p-5 relative overflow-hidden group shadow-lg"
                >
                  <div className="absolute -top-12 -right-12 w-24 h-24 bg-brand-orange/10 rounded-full blur-xl group-hover:bg-brand-orange/20 transition-all" />
                  <span className="font-mono text-[10px] text-neutral-500 tracking-widest block font-bold uppercase">{m.label}</span>
                  <span className="text-2xl sm:text-3xl font-mono font-black text-white mt-1 block tracking-tight">{m.val}</span>
                  <span className="text-xs text-neutral-400 mt-1 block font-mono">{m.sub}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Section 2: The Read-Only Philosophy (Brutalist Callout Box) */}
          <section className="relative">
            <div className="backdrop-blur-2xl bg-neutral-950/60 border-2 border-neutral-800 p-8 md:p-12 relative overflow-hidden shadow-2xl">
              <div className="absolute top-0 left-0 w-2 h-full bg-brand-orange" />
              
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-neutral-800/80">
                <div>
                  <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">PHILOSOPHY & INTEGRITY</span>
                  <h2 className="text-2xl sm:text-3xl md:text-4xl font-black uppercase tracking-tight text-white mt-1">
                    WHY "READ-ONLY" IS A CORE SECURITY FEATURE
                  </h2>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-neutral-900 border border-neutral-800 font-mono text-xs text-neutral-300 self-start md:self-auto">
                  <Lock className="w-4 h-4 text-brand-orange" />
                  <span>IMMUTABLE AIR-GAP</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8 text-neutral-300 font-sans text-sm sm:text-base leading-relaxed">
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-white font-mono font-bold uppercase text-sm">
                    <span className="text-brand-orange font-mono">01 //</span> NO ACTIVE CONNECTIONS
                  </div>
                  <p className="text-neutral-400">
                    Legacy scanners log into production switches via SSH or SNMP. A single malformed command or session stall can trigger control-plane crash loops. Phoenix Protocol never touches live hardware.
                  </p>
                </div>

                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-white font-mono font-bold uppercase text-sm">
                    <span className="text-brand-orange font-mono">02 //</span> NO CREDENTIAL STORAGE
                  </div>
                  <p className="text-neutral-400">
                    Eliminates the catastrophic vulnerability of maintaining centralized administrative credentials, enable passwords, or private SSH keys on an auditing server.
                  </p>
                </div>

                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-white font-mono font-bold uppercase text-sm">
                    <span className="text-brand-orange font-mono">03 //</span> SAFE FOR JUNIOR ENGINEERS
                  </div>
                  <p className="text-neutral-400">
                    Anyone on your team can upload router configurations or CI pipeline exports to evaluate compliance without authorization anxiety or risk of network disruption.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Architecture Pillars (Glassmorphic Cards) */}
          <section className="flex flex-col gap-8">
            <div className="flex flex-col gap-2">
              <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">ENGINE SPECIFICATIONS</span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-black uppercase tracking-tight text-white">
                CORE SYSTEM ARCHITECTURE
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {pillars.map((p, idx) => (
                <div 
                  key={idx}
                  className="backdrop-blur-xl bg-neutral-900/30 border border-neutral-800/80 hover:border-neutral-600 transition-all duration-300 p-8 flex flex-col justify-between group shadow-xl relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 w-32 h-32 bg-brand-orange/5 rounded-full blur-2xl group-hover:bg-brand-orange/15 transition-all" />
                  
                  <div>
                    <div className="flex items-center justify-between gap-4 mb-4">
                      <span className="font-mono text-xs font-black text-neutral-500 tracking-widest">{p.code}</span>
                      <span className="px-2.5 py-0.5 bg-white/5 border border-white/10 font-mono text-[10px] font-bold text-neutral-300 uppercase">
                        {p.badge}
                      </span>
                    </div>

                    <h3 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-white group-hover:text-brand-orange transition-colors">
                      {p.title}
                    </h3>

                    <p className="mt-4 text-neutral-400 text-sm sm:text-base leading-relaxed">
                      {p.description}
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-neutral-800/80 font-mono text-xs text-brand-orange flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>{p.highlight}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section 4: Technical Rules Matrix & System Specs */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* Left Column: Rules Catalog */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">BASELINE COVERAGE</span>
                <h3 className="text-2xl sm:text-3xl font-black uppercase tracking-tight text-white">
                  BUILT-IN SECURITY CONTROLS
                </h3>
              </div>

              <div className="backdrop-blur-xl bg-neutral-950/40 border border-neutral-800 overflow-hidden shadow-xl">
                <div className="grid grid-cols-12 px-4 py-3 bg-neutral-900/80 border-b border-neutral-800 font-mono text-[10px] font-bold text-neutral-400 uppercase tracking-widest">
                  <span className="col-span-4">RULE_ID</span>
                  <span className="col-span-5">CONTROL_NAME</span>
                  <span className="col-span-3 text-right">SEVERITY</span>
                </div>

                <div className="divide-y divide-neutral-800/60">
                  {ruleCatalog.map((r, i) => (
                    <div key={i} className="grid grid-cols-12 px-4 py-3.5 items-center hover:bg-white/[0.02] transition-colors font-mono text-xs">
                      <span className="col-span-4 text-neutral-400 font-bold">{r.id}</span>
                      <span className="col-span-5 text-white font-sans text-sm font-medium truncate pr-2">{r.control}</span>
                      <div className="col-span-3 text-right">
                        <span className={`inline-block px-2 py-0.5 text-[10px] font-black uppercase tracking-wider ${
                          r.severity === 'CRITICAL' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                          r.severity === 'HIGH' ? 'bg-orange-500/10 text-brand-orange border border-orange-500/30' :
                          'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}>
                          {r.severity}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Hardware / System Specs (Raw Brutalist Spec) */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">SYSTEM TELEMETRY</span>
                <h3 className="text-2xl sm:text-3xl font-black uppercase tracking-tight text-white">
                  RUNTIME MANIFEST
                </h3>
              </div>

              <div className="backdrop-blur-xl bg-neutral-900/30 border border-neutral-800 p-6 flex flex-col gap-4 font-mono text-xs shadow-xl">
                {techSpecs.map((spec, i) => (
                  <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-neutral-800/60 last:border-0 last:pb-0 gap-1 sm:gap-4">
                    <span className="text-neutral-500 font-bold tracking-widest">{spec.label}</span>
                    <span className="text-white font-medium text-right">{spec.value}</span>
                  </div>
                ))}

                <div className="mt-4 p-4 bg-black/60 border border-neutral-800 rounded flex items-center gap-3">
                  <Fingerprint className="w-6 h-6 text-brand-orange shrink-0" />
                  <div className="text-[11px] text-neutral-400 font-sans">
                    Every uploaded configuration generates an immutable cryptographic signature for end-to-end evidence auditing.
                  </div>
                </div>
              </div>
            </div>

          </section>

          {/* Section 5: Final Call To Action */}
          <section className="mt-4 backdrop-blur-2xl bg-gradient-to-r from-neutral-900/80 via-black/90 to-neutral-900/80 border-2 border-neutral-800 p-8 sm:p-12 md:p-16 flex flex-col sm:flex-row items-center justify-between gap-8 relative overflow-hidden shadow-2xl">
            <div className="absolute top-0 right-0 w-96 h-96 bg-brand-orange/10 rounded-full blur-3xl pointer-events-none" />
            
            <div className="flex flex-col gap-2 max-w-xl text-center sm:text-left">
              <span className="font-mono text-xs font-bold text-brand-orange tracking-widest uppercase">READY TO AUDIT</span>
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-black uppercase tracking-tight text-white">
                LAUNCH CONFIGURATION SCANNER
              </h2>
              <p className="text-neutral-400 font-sans text-sm sm:text-base mt-2">
                Paste or drag-and-drop any network device configuration to test against the Phoenix Protocol security baseline in seconds.
              </p>
            </div>

            <Link 
              to="/#upload-section"
              state={{ scrollToUpload: true }}
              className="px-8 py-4 bg-brand-orange hover:bg-orange-500 text-white font-mono font-black text-sm uppercase tracking-widest flex items-center gap-3 transition-all duration-300 hover:scale-105 shadow-[0_0_30px_rgba(234,88,20,0.4)] shrink-0"
            >
              <span>RETURN TO SCANNER</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </section>

        </main>

        <Footer />
      </div>
    </PageTransition>
  );
}
export default AboutPage;
