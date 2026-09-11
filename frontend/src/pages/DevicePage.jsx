import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { getDevice } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { SeverityBadge } from '../components/SeverityBadge';
import { ErrorAlert } from '../components/ErrorAlert';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { ArrowLeft, Filter, AlertTriangle, ShieldCheck } from 'lucide-react';
import { PageTransition } from '../components/motion/PageTransition';

export function DevicePage() {
  const { scanId, deviceId } = useParams();
  const [deviceData, setDeviceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [expandedRule, setExpandedRule] = useState(null);

  useEffect(() => {
    async function loadDevice() {
      try {
        const response = await getDevice(scanId, deviceId);
        setDeviceData(response.data?.device || response.data);
      } catch (err) {
        setError(err.message || 'Failed to load device details.');
      } finally {
        setLoading(false);
      }
    }
    loadDevice();
  }, [scanId, deviceId]);

  if (loading) return (
    <PageTransition>
      <div className="min-h-screen bg-obsidian flex items-center justify-center font-mono uppercase tracking-widest text-sm text-neutral-500">
        <motion.div animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 1.5 }}>
          Loading device profile...
        </motion.div>
      </div>
    </PageTransition>
  );
  
  if (error) return (
    <PageTransition>
      <div className="min-h-screen bg-obsidian flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-lg">
          <Link to={`/scans/${scanId}`} className="inline-flex items-center gap-2 mb-6 text-xs text-neutral-500 font-bold uppercase tracking-widest hover:text-brand-orange transition-colors group">
            <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" /> Back to dashboard
          </Link>
          <ErrorAlert message={error} />
        </div>
      </div>
    </PageTransition>
  );
  
  if (!deviceData) return (
    <PageTransition>
      <div className="min-h-screen bg-obsidian flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-lg text-center font-mono text-neutral-500">
          <p className="mb-4">Device not found for ID "{deviceId}".</p>
          <Link to={`/scans/${scanId}`} className="inline-flex items-center gap-2 text-xs text-brand-orange font-bold uppercase tracking-widest hover:text-white transition-colors">
            <ArrowLeft size={14} /> Back to dashboard
          </Link>
        </div>
      </div>
    </PageTransition>
  );

  const filteredResults = (deviceData.results || []).filter(result => {
    if (statusFilter !== 'all' && result.status !== statusFilter) return false;
    if (severityFilter !== 'all' && result.severity !== severityFilter) return false;
    return true;
  });

  filteredResults.sort((a, b) => {
    const score = (r) => {
      let s = 0;
      if (r.severity === 'high') s += 100;
      if (r.severity === 'medium') s += 50;
      if (r.status === 'fail') s += 10;
      if (r.status === 'error') s += 10;
      if (r.status === 'warning') s += 5;
      return s;
    };
    return score(b) - score(a);
  });

  const toggleExpand = (ruleId) => {
    setExpandedRule(expandedRule === ruleId ? null : ruleId);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian">
        <Navbar />
        
        <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-12">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-12">
            <Link to={`/scans/${scanId}`} className="inline-flex items-center gap-2 mb-6 text-xs text-neutral-500 font-bold uppercase tracking-widest hover:text-brand-orange transition-colors group">
              <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" /> Back to dashboard
            </Link>
            
            <h1 className="text-4xl font-mono font-bold tracking-tight text-white mb-4 uppercase">{deviceData.display_name}</h1>
            <div className="flex flex-wrap items-center gap-6 text-sm font-mono text-neutral-400">
              <span className="flex items-center gap-2"><span className="text-neutral-600 font-sans text-xs tracking-widest font-bold uppercase">Vendor:</span> <span className="text-white">{deviceData.vendor}</span></span>
              <span className="flex items-center gap-2"><span className="text-neutral-600 font-sans text-xs tracking-widest font-bold uppercase">Type:</span> <span className="text-white">{deviceData.device_type}</span></span>
              <span className="flex items-center gap-2"><span className="text-neutral-600 font-sans text-xs tracking-widest font-bold uppercase">Parser Status:</span> <StatusBadge status={deviceData.parse_status} /></span>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="mb-8 glass-card p-4 flex flex-wrap items-center gap-4 border-l-2 border-l-brand-orange">
            <Filter size={16} className="text-neutral-500 flex-shrink-0" />
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)} 
              className="bg-neutral-900 border border-neutral-700 text-white text-xs tracking-widest font-bold uppercase p-3 rounded-sm outline-none focus:border-brand-orange/50 appearance-none min-w-[140px]"
            >
              <option value="all">All Statuses</option>
              <option value="pass">Pass</option>
              <option value="fail">Fail</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
            <select 
              value={severityFilter} 
              onChange={(e) => setSeverityFilter(e.target.value)} 
              className="bg-neutral-900 border border-neutral-700 text-white text-xs tracking-widest font-bold uppercase p-3 rounded-sm outline-none focus:border-brand-orange/50 appearance-none min-w-[140px]"
            >
              <option value="all">All Severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <button 
              onClick={() => { setStatusFilter('all'); setSeverityFilter('all'); }} 
              className="text-neutral-500 hover:text-white text-xs font-bold tracking-widest uppercase ml-auto transition-colors"
            >
              Reset Filters
            </button>
          </motion.div>

          {filteredResults.length === 0 ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-8 glass-card flex flex-col items-center justify-center text-neutral-500 font-mono text-sm gap-4">
              <ShieldCheck size={32} className="text-neutral-700" />
              No rules match the active filters.
            </motion.div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="glass-card overflow-x-auto overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-neutral-800 bg-neutral-900/30">
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Rule ID</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Title</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Status</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Severity</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Message</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Action</th>
                  </tr>
                </thead>
                <motion.tbody variants={containerVariants} initial="hidden" animate="show" className="divide-y divide-neutral-800/80">
                  {filteredResults.map((result) => (
                    <React.Fragment key={result.rule_id}>
                      <motion.tr variants={itemVariants} className="hover:bg-neutral-800/30 transition-colors group">
                        <td className="px-6 py-4 font-mono text-xs text-neutral-400">{result.rule_id}</td>
                        <td className="px-6 py-4 font-medium text-sm text-neutral-200 group-hover:text-white transition-colors">{result.title}</td>
                        <td className="px-6 py-4"><StatusBadge status={result.status} /></td>
                        <td className="px-6 py-4"><SeverityBadge severity={result.severity} /></td>
                        <td className="px-6 py-4 text-sm text-neutral-400">{result.message}</td>
                        <td className="px-6 py-4">
                          <button 
                            onClick={() => toggleExpand(result.rule_id)}
                            className="text-brand-orange hover:text-white text-xs font-bold tracking-widest uppercase transition-colors flex items-center gap-1"
                          >
                            {expandedRule === result.rule_id ? 'Hide Details' : 'Inspect'}
                          </button>
                        </td>
                      </motion.tr>
                      <AnimatePresence>
                        {expandedRule === result.rule_id && (
                          <motion.tr 
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                            className="bg-neutral-900/50 overflow-hidden block w-full table-row"
                          >
                            <td colSpan="6" className="p-0 border-b-0">
                              <motion.div 
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                                transition={{ delay: 0.1 }}
                                className="p-8 flex flex-col gap-8 max-w-4xl"
                              >
                                {result.evidence && (
                                  <div>
                                    <div className="text-xs font-bold uppercase tracking-widest text-neutral-500 mb-3 flex items-center gap-2">
                                      <div className="w-2 h-2 rounded-full bg-brand-orange"></div>
                                      Extracted Evidence
                                    </div>
                                    <div className="bg-[#040506] border-l-2 border-brand-orange/50 p-6 rounded-r-sm overflow-x-auto text-sm font-mono text-neutral-300 whitespace-pre-wrap shadow-inner">
                                      {result.evidence}
                                    </div>
                                    {result.evidence_start_line && (
                                      <div className="text-neutral-500 mt-3 text-xs font-mono">
                                        Source line reference: <span className="text-neutral-300">{result.evidence_start_line}</span>
                                      </div>
                                    )}
                                  </div>
                                )}
                                
                                <div>
                                  <div className="text-xs font-bold uppercase tracking-widest text-neutral-500 mb-3 flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
                                    Remediation Protocol
                                  </div>
                                  <div className="bg-neutral-800/30 border border-neutral-700/50 p-6 rounded-sm text-neutral-300 text-sm leading-relaxed">
                                    <p>{result.remediation}</p>
                                    <div className="mt-6 flex items-start gap-3 pt-4 border-t border-neutral-700/50">
                                      <AlertTriangle size={16} className="text-warning flex-shrink-0 mt-0.5" />
                                      <p className="text-xs text-neutral-400 font-mono">
                                        <strong>WARNING:</strong> Production changes require internal review and staged deployment. This is read-only guidance.
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              </motion.div>
                            </td>
                          </motion.tr>
                        )}
                      </AnimatePresence>
                    </React.Fragment>
                  ))}
                </motion.tbody>
              </table>
            </motion.div>
          )}
        </main>
        
        <Footer />
      </div>
    </PageTransition>
  );
}
