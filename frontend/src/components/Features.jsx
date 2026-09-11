import React from 'react';
import { Code2, ShieldAlert, Cpu, Lock, FastForward } from 'lucide-react';
import { ScrollReveal } from './motion/ScrollReveal';

export function Features() {
  const features = [
    {
      icon: <Code2 className="text-brand-orange" size={32} />,
      title: "Stateless Parser",
      desc: "Instantaneous analysis without persisting sensitive configurations to disk."
    },
    {
      icon: <ShieldAlert className="text-brand-orange" size={32} />,
      title: "Deterministic Rules",
      desc: "Authoritative rule evaluation (NET-001..NET-010). AI provides advisory guidance."
    },
    {
      icon: <Cpu className="text-brand-orange" size={32} />,
      title: "Extensible Architecture",
      desc: "Currently supports Cisco IOS configurations, with an extensible architecture for additional vendors."
    },
    {
      icon: <Lock className="text-brand-orange" size={32} />,
      title: "Read-Only",
      desc: "Zero chance of accidental network disruption or downtime."
    },
    {
      icon: <FastForward className="text-brand-orange" size={32} />,
      title: "Automated Reporting",
      desc: "Generates CSV compliance artifacts for security audits instantly."
    }
  ];

  return (
    <section className="w-full py-24 px-6 border-b border-neutral-900 bg-obsidian">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-xs font-bold uppercase tracking-widest text-neutral-500 mb-12 flex items-center gap-4">
            <div className="w-12 h-px bg-neutral-800"></div>
            Core Capabilities
          </div>
        </ScrollReveal>
        
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-8">
          {features.map((feature, i) => (
            <ScrollReveal key={i} delay={i * 0.1} className="group">
              <div className="mb-6 p-4 inline-flex items-center justify-center bg-neutral-900/50 rounded-sm border border-neutral-800 group-hover:border-brand-orange/30 group-hover:bg-brand-orange/5 transition-colors">
                {feature.icon}
              </div>
              <h3 className="text-white font-bold tracking-tight mb-2 uppercase">{feature.title}</h3>
              <p className="text-neutral-500 text-sm leading-relaxed">{feature.desc}</p>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
