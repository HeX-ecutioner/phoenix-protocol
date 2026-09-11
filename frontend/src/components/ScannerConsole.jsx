import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUp, Network, CheckCircle } from 'lucide-react';
import { createScan } from '../services/api';
import { ErrorAlert } from './ErrorAlert';
import { SafetyNotice } from './SafetyNotice';
import { KineticButton } from './motion/KineticButton';
import { motion, AnimatePresence } from 'framer-motion';

export function ScannerConsole() {
  const [deviceType, setDeviceType] = useState('cisco_ios');
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, processing, success, error
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(Array.from(e.dataTransfer.files));
      setError(null);
    }
  };

  const handleScan = async () => {
    if (!files || files.length === 0) {
      setError("Please select at least one configuration file first.");
      return;
    }

    setStatus('processing');
    setError(null);

    try {
      const response = await createScan(deviceType, files);
      const scanId = response.data?.scan_id || response.data?.id || response.data?.scan?.id;

      if (!scanId) {
        throw new Error("Scan completed, but no valid scan ID was returned by the server.");
      }

      setStatus('success');
      setTimeout(() => {
        navigate(`/scans/${scanId}`);
      }, 500);

    } catch (err) {
      setError(err.message || "Failed to initiate scan.");
      setStatus('error');
    }
  };

  return (
    <section id="scanner-console" className="w-full max-w-3xl mx-auto px-6 scroll-mt-32">
      <div className="glass-card p-8 shadow-2xl bg-neutral-900/60 backdrop-blur-xl border border-neutral-800/80 rounded-sm">

        <SafetyNotice />

        {error && <ErrorAlert message={error} />}

        <div className="mb-6">
          <label className="block text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">Target Platform</label>
          <div className="relative">
            <Network className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500" size={18} />
            <select
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
              disabled={status === 'processing' || status === 'success'}
              className="w-full bg-neutral-950 border border-neutral-800 text-white pl-12 pr-4 py-4 rounded-sm appearance-none outline-none focus:border-brand-orange/50 focus:ring-1 focus:ring-brand-orange/50 transition-all font-mono disabled:opacity-50"
            >
              <option value="cisco_ios">Cisco IOS (Active MVP)</option>
              <option value="cisco_nxos">Cisco NX-OS (Extensible Architecture)</option>
              <option value="juniper_junos">Juniper Junos (Extensible Architecture)</option>
              <option value="arista_eos">Arista EOS (Extensible Architecture)</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-neutral-500">
              <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
            </div>
          </div>
        </div>

        <div className="mb-8">
          <label className="block text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">Configuration Matrix</label>
          <div
            className={`border-2 border-dashed rounded-sm p-12 text-center transition-all ${files.length > 0 ? 'border-brand-orange/50 bg-brand-orange/5' : 'border-neutral-800 hover:border-neutral-700 bg-neutral-950/50'} ${status !== 'idle' && status !== 'error' ? 'pointer-events-none opacity-50' : ''}`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              multiple
              className="hidden"
              onChange={handleFileChange}
              disabled={status === 'processing' || status === 'success'}
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center justify-center">
              <FileUp className={`w-10 h-10 mb-4 ${files.length > 0 ? 'text-brand-orange' : 'text-neutral-600'}`} />
              <span className="text-white font-mono text-sm mb-2">
                {files.length === 1
                  ? files[0].name
                  : files.length > 1
                    ? `${files.length} configuration files selected (${files.map(f => f.name).join(', ')})`
                    : "Drop configuration file(s) here"}
              </span>
              <span className="text-neutral-500 text-xs uppercase tracking-widest font-bold">
                {files.length > 0 ? "Click to change selection" : "or click to browse local filesystem (.txt, .cfg, .conf)"}
              </span>
            </label>
          </div>
        </div>

        <div className="flex justify-center overflow-hidden">
          <AnimatePresence mode="wait">
            {status === 'idle' || status === 'error' ? (
              <motion.div key="idle" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="w-full sm:w-auto">
                <KineticButton onClick={handleScan} className="w-full sm:w-auto px-12 py-4">
                  Run Compliance Scan
                </KineticButton>
              </motion.div>
            ) : status === 'processing' ? (
              <motion.div key="processing" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="w-full sm:w-auto px-12 py-4 bg-neutral-800 text-neutral-300 font-extrabold uppercase tracking-widest text-sm flex items-center justify-center gap-3 rounded-sm border border-neutral-700">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-brand-orange" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </motion.div>
            ) : (
              <motion.div key="success" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-full sm:w-auto px-12 py-4 bg-brand-orange text-black font-extrabold uppercase tracking-widest text-sm flex items-center justify-center gap-3 rounded-sm">
                <CheckCircle size={18} /> Complete
              </motion.div>
            )}
          </AnimatePresence>
        </div>

      </div>
    </section>
  );
}
