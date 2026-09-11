import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getScan, getDevices, getCsvReportUrl } from '../services/api';
import { SummaryCard } from '../components/SummaryCard';
import { StatusBadge } from '../components/StatusBadge';
import { ErrorAlert } from '../components/ErrorAlert';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { ArrowLeft, Download, ShieldCheck } from 'lucide-react';
import { PageTransition } from '../components/motion/PageTransition';

export function DashboardPage() {
  const { scanId } = useParams();
  const [summary, setSummary] = useState(null);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [scanResponse, devicesResponse] = await Promise.all([
          getScan(scanId),
          getDevices(scanId)
        ]);
        
        setSummary(scanResponse.data);
        setDevices(devicesResponse.data.devices);
      } catch (err) {
        setError(err.message || 'Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [scanId]);

  if (loading) return (
    <PageTransition>
      <div className="min-h-screen bg-obsidian flex items-center justify-center font-mono uppercase tracking-widest text-sm text-neutral-500">
        <motion.div animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 1.5 }}>
          Loading telemetry...
        </motion.div>
      </div>
    </PageTransition>
  );
  
  if (error) return (
    <PageTransition>
      <div className="min-h-screen bg-obsidian flex items-center justify-center p-6"><ErrorAlert message={error} /></div>
    </PageTransition>
  );
  
  if (!summary) return (
    <PageTransition>
      <div className="min-h-screen bg-obsidian flex items-center justify-center font-mono text-neutral-500">No scan data found.</div>
    </PageTransition>
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -10 },
    show: { opacity: 1, x: 0 }
  };

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col w-full bg-obsidian">
        <Navbar />
        
        <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-12">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-12">
            <Link to="/" className="inline-flex items-center gap-2 mb-6 text-xs text-neutral-500 font-bold uppercase tracking-widest hover:text-brand-orange transition-colors group">
              <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" /> Upload Matrix
            </Link>
            
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <h1 className="text-4xl md:text-5xl font-sans font-extrabold tracking-tight text-white mb-2 uppercase">Scan Results</h1>
                <div className="text-neutral-500 text-sm font-mono flex items-center gap-2">
                  <ShieldCheck size={16} className="text-brand-orange" />
                  Completed: {new Date(summary.completed_at).toLocaleString()} &bull; {summary.device_type}
                </div>
              </div>
              
              <motion.a 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                href={getCsvReportUrl(scanId)} 
                className="px-6 py-3 border border-brand-orange/30 text-brand-orange font-bold uppercase tracking-widest text-xs rounded-sm hover:bg-brand-orange/10 transition-colors flex items-center gap-2"
                download
              >
                <Download size={16} /> Export CSV
              </motion.a>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-px bg-neutral-800/50 border border-neutral-800/80 mb-12 rounded-sm overflow-hidden"
          >
            <SummaryCard label="Devices" value={summary.summary.device_count} />
            <SummaryCard label="Rules" value={summary.summary.total_rules_evaluated} />
            <SummaryCard label="Pass" value={summary.summary.pass_count} />
            <SummaryCard label="Fail" value={summary.summary.fail_count} />
            <SummaryCard label="Warn" value={summary.summary.warning_count} />
            <SummaryCard label="High Risk" value={summary.summary.high_severity_failures} />
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="mb-16 p-10 glass-card bg-neutral-900/40 relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-orange/5 rounded-full blur-[100px] -mr-32 -mt-32 group-hover:bg-brand-orange/10 transition-colors duration-1000"></div>
            
            <h2 className="text-xs font-bold tracking-widest text-neutral-400 uppercase mb-4 relative z-10">Tested-Rule Compliance</h2>
            <div className="text-6xl md:text-8xl font-extrabold text-brand-orange tracking-tighter leading-none mb-6 relative z-10 drop-shadow-[0_0_15px_rgba(204,255,0,0.2)] flex">
              <motion.span
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, type: 'spring' }}
              >
                {summary.summary.compliance_percentage}%
              </motion.span>
            </div>
            <p className="text-neutral-500 text-sm max-w-2xl relative z-10 font-medium leading-relaxed">
              This percentage covers only the rules tested by Phoenix Protocol. It does not prove complete security.
            </p>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="mb-12">
            <h2 className="text-2xl font-extrabold tracking-tight text-white mb-6 uppercase">Target Devices</h2>
            <div className="overflow-x-auto glass-card">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-neutral-800 bg-neutral-900/30">
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Device</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Parser Status</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Pass</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Fail</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Warn</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">High Risk</th>
                    <th className="px-6 py-4 text-xs font-bold tracking-widest text-neutral-500 uppercase">Action</th>
                  </tr>
                </thead>
                <motion.tbody variants={containerVariants} initial="hidden" animate="show" className="divide-y divide-neutral-800/80">
                  {devices.map((device) => (
                    <motion.tr variants={itemVariants} key={device.id} className="hover:bg-neutral-800/30 transition-colors group">
                      <td className="px-6 py-4 font-mono text-sm text-neutral-300 group-hover:text-white transition-colors">{device.display_name}</td>
                      <td className="px-6 py-4"><StatusBadge status={device.parse_status} /></td>
                      <td className="px-6 py-4 font-mono text-neutral-400">{device.summary.pass_count}</td>
                      <td className="px-6 py-4 font-mono text-neutral-400">{device.summary.fail_count}</td>
                      <td className="px-6 py-4 font-mono text-neutral-400">{device.summary.warning_count}</td>
                      <td className={`px-6 py-4 font-mono ${device.summary.high_severity_failures > 0 ? 'text-red-400 font-bold' : 'text-neutral-400'}`}>
                        {device.summary.high_severity_failures}
                      </td>
                      <td className="px-6 py-4">
                        <Link to={`/scans/${scanId}/devices/${device.id}`} className="text-brand-orange hover:text-white text-xs font-bold tracking-widest uppercase transition-colors inline-block hover:translate-x-1 duration-200">
                          Inspect
                        </Link>
                      </td>
                    </motion.tr>
                  ))}
                </motion.tbody>
              </table>
            </div>
          </motion.div>
        </main>
        
        <Footer />
      </div>
    </PageTransition>
  );
}
