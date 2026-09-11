import React from 'react';
import { ScrollReveal } from './motion/ScrollReveal';

export function ScanNotes() {
  return (
    <section className="w-full py-24 px-6 bg-[#040506]">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-start">
          <ScrollReveal>
            <h2 className="text-3xl md:text-5xl font-sans font-extrabold tracking-tighter text-white uppercase leading-tight mb-6">
              Precision auditing<br />without the risk.
            </h2>
            <p className="text-neutral-400 text-lg leading-relaxed mb-8">
              Phoenix Protocol isolates the analytical process from the operational network. By consuming static text configurations, it provides deterministic security grading without touching live equipment.
            </p>
          </ScrollReveal>
          
          <div className="space-y-4">
            <ScrollReveal delay={0.1}>
              <div className="p-6 border-l-2 border-brand-orange bg-neutral-900/40 backdrop-blur-sm rounded-r-sm">
                <div className="text-xs font-bold uppercase tracking-widest text-brand-orange mb-2">Insight</div>
                <p className="text-neutral-300 text-sm">Most misconfigurations are syntactic, not architectural. Analyzing raw config text catches 90% of vulnerability vectors before deployment.</p>
              </div>
            </ScrollReveal>
            <ScrollReveal delay={0.2}>
              <div className="p-6 border-l-2 border-cyan-400 bg-neutral-900/40 backdrop-blur-sm rounded-r-sm">
                <div className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">Observation</div>
                <p className="text-neutral-300 text-sm">Network environments rarely maintain 100% compliance. The goal is identifying "High Severity" drift in protocols like SNMP and SSH.</p>
              </div>
            </ScrollReveal>
            <ScrollReveal delay={0.3}>
              <div className="p-6 border-l-2 border-neutral-600 bg-neutral-900/40 backdrop-blur-sm rounded-r-sm">
                <div className="text-xs font-bold uppercase tracking-widest text-neutral-500 mb-2">Compliance</div>
                <p className="text-neutral-300 text-sm">Designed specifically to align with Zero Trust and strict enterprise demarcation requirements.</p>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </div>
    </section>
  );
}
