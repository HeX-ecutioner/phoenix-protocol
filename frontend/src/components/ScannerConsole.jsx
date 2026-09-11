import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUp, Network, CheckCircle, X } from 'lucide-react';
import { createScan } from '../services/api';
import { ErrorAlert } from './ErrorAlert';
import { SafetyNotice } from './SafetyNotice';
import { KineticButton } from './motion/KineticButton';
import { motion, AnimatePresence } from 'framer-motion';

const DISALLOWED_EXTENSIONS = ['.exe', '.dll', '.bin', '.iso', '.zip', '.tar', '.gz', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3'];

function isValidConfigFile(file) {
  if (!file) return false;
  const name = (file.name || '').toLowerCase();
  if (DISALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
    return false;
  }
  return true;
}

function extractFilesOrTextFromClipboard(clipboardData, existingFileNames = []) {
  if (!clipboardData) return [];
  const extracted = [];

  // 1. First check clipboard File objects (e.g. copied files from Explorer / Finder)
  if (clipboardData.files && clipboardData.files.length > 0) {
    for (let i = 0; i < clipboardData.files.length; i++) {
      const file = clipboardData.files[i];
      if (file && (file.size > 0 || file.name)) extracted.push(file);
    }
  }

  // Also check items if files was empty
  if (extracted.length === 0 && clipboardData.items && clipboardData.items.length > 0) {
    for (let i = 0; i < clipboardData.items.length; i++) {
      const item = clipboardData.items[i];
      if (item && item.kind === 'file') {
        const file = item.getAsFile();
        if (file) extracted.push(file);
      }
    }
  }

  if (extracted.length > 0) {
    return extracted;
  }

  // 2. Plaintext configuration fallback
  let text = '';
  try {
    text = clipboardData.getData('text/plain') || clipboardData.getData('Text') || '';
  } catch {
    text = '';
  }

  if (text && typeof text === 'string') {
    const trimmed = text.trim();
    if (trimmed.length > 0) {
      let filename = 'pasted-config.txt';
      let counter = 1;
      while (existingFileNames.includes(filename)) {
        counter += 1;
        filename = `pasted-config-${counter}.txt`;
      }

      try {
        const pastedFile = new File([trimmed + '\n'], filename, {
          type: 'text/plain',
          lastModified: Date.now(),
        });
        extracted.push(pastedFile);
      } catch {
        const blob = new Blob([trimmed + '\n'], { type: 'text/plain' });
        blob.name = filename;
        blob.lastModified = Date.now();
        extracted.push(blob);
      }
    }
  }

  return extracted;
}

export function ScannerConsole() {
  const [deviceType, setDeviceType] = useState('cisco_ios');
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, processing, success, error
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const navigate = useNavigate();
  const dropzoneRef = useRef(null);
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);
  const filesRef = useRef(files);

  // Keep filesRef synchronized for global event listeners
  useEffect(() => {
    filesRef.current = files;
  }, [files]);

  const addFiles = useCallback((incomingFiles) => {
    if (!incomingFiles || incomingFiles.length === 0) return;

    const fileList = Array.from(incomingFiles);
    const validFiles = [];
    const invalidNames = [];

    for (const file of fileList) {
      if (isValidConfigFile(file)) {
        validFiles.push(file);
      } else {
        invalidNames.push(file.name || 'unsupported file');
      }
    }

    if (invalidNames.length > 0) {
      setError(
        `Unsupported binary format: ${invalidNames.join(', ')}. Please provide text configuration files (.txt, .cfg, .conf, .ios).`
      );
    }

    if (validFiles.length === 0) return;

    setFiles((prevFiles) => {
      const existingKeys = new Set(
        prevFiles.map((f) => `${f.name}:${f.size}`)
      );
      const uniqueFiles = validFiles.filter(
        (f) =>
          !existingKeys.has(`${f.name}:${f.size}`) &&
          !prevFiles.some(
            (p) =>
              p.name.startsWith('pasted-config') &&
              f.name.startsWith('pasted-config') &&
              p.size === f.size
          )
      );

      if (uniqueFiles.length === 0 && prevFiles.length > 0) {
        return prevFiles;
      }

      if (invalidNames.length === 0) {
        setError(null);
      }
      return [...prevFiles, ...uniqueFiles];
    });
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
      e.target.value = '';
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current += 1;
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'copy';
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      dragCounter.current = 0;
      setIsDragging(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'copy';
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current = 0;
    setIsDragging(false);

    let droppedFiles = [];
    if (e.dataTransfer) {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        droppedFiles = Array.from(e.dataTransfer.files);
      } else if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
        for (let i = 0; i < e.dataTransfer.items.length; i++) {
          const item = e.dataTransfer.items[i];
          if (item && item.kind === 'file') {
            const f = item.getAsFile();
            if (f) droppedFiles.push(f);
          }
        }
      }

      // Check if raw text was dragged and dropped
      if (droppedFiles.length === 0) {
        const textData = e.dataTransfer.getData('text/plain') || e.dataTransfer.getData('Text');
        if (textData && textData.trim().length > 0) {
          const existingNames = filesRef.current.map((f) => f.name);
          const extracted = extractFilesOrTextFromClipboard(e.dataTransfer, existingNames);
          if (extracted.length > 0) {
            droppedFiles = extracted;
          }
        }
      }
    }

    if (droppedFiles.length > 0) {
      addFiles(droppedFiles);
    }
  };

  const handleDropzonePaste = (e) => {
    const existingNames = filesRef.current.map((f) => f.name);
    const clipboardFiles = extractFilesOrTextFromClipboard(e.clipboardData, existingNames);
    if (clipboardFiles.length > 0) {
      e.preventDefault();
      e.stopPropagation();
      addFiles(clipboardFiles);
    }
  };

  // Prevent browser from navigating away if a file is dropped outside the dropzone
  useEffect(() => {
    const preventDefaultGlobal = (e) => {
      e.preventDefault();
    };

    window.addEventListener('dragover', preventDefaultGlobal);
    window.addEventListener('drop', preventDefaultGlobal);

    return () => {
      window.removeEventListener('dragover', preventDefaultGlobal);
      window.removeEventListener('drop', preventDefaultGlobal);
    };
  }, []);

  // Global window paste listener: catches Ctrl+V / Cmd+V anywhere on the page
  useEffect(() => {
    const handleGlobalPaste = (e) => {
      const activeTag = document.activeElement?.tagName?.toLowerCase();
      // Only ignore if the user is actively typing in a form input or textarea
      if ((activeTag === 'input' && document.activeElement?.type !== 'file') || activeTag === 'textarea') {
        return;
      }

      const clipboardData = e.clipboardData || window.clipboardData;
      if (!clipboardData) return;

      const existingNames = filesRef.current.map((f) => f.name);
      const clipboardFiles = extractFilesOrTextFromClipboard(clipboardData, existingNames);
      if (clipboardFiles && clipboardFiles.length > 0) {
        e.preventDefault();
        e.stopPropagation();
        addFiles(clipboardFiles);
      }
    };

    window.addEventListener('paste', handleGlobalPaste);
    return () => {
      window.removeEventListener('paste', handleGlobalPaste);
    };
  }, [addFiles]);

  const removeFile = (indexToRemove, e) => {
    e.stopPropagation();
    setFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
    setError(null);
  };

  const clearAllFiles = (e) => {
    e.stopPropagation();
    setFiles([]);
    setError(null);
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
              <option value="cisco_ios">Cisco IOS — ACTIVE MVP</option>
              <option value="cisco_nxos" disabled>Cisco NX-OS — PLANNED ADAPTER</option>
              <option value="juniper_junos" disabled>Juniper Junos — PLANNED ADAPTER</option>
              <option value="arista_eos" disabled>Arista EOS — PLANNED ADAPTER</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-neutral-500">
              <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
            </div>
          </div>
          <p className="mt-2 text-[11px] font-mono text-neutral-500 leading-relaxed">
            Phoenix normalizes vendor-specific configuration into a common compliance model, allowing additional vendor adapters to be added without rewriting the compliance engine.
          </p>
        </div>

        <div className="mb-8">
          <label className="block text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">Configuration Matrix</label>
          <div
            ref={dropzoneRef}
            tabIndex={0}
            onClick={() => {
              fileInputRef.current?.click();
            }}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onPaste={handleDropzonePaste}
            className={`border-2 border-dashed rounded-sm p-8 text-center transition-all outline-none focus:ring-1 focus:ring-brand-orange/50 ${
              isDragging
                ? 'border-brand-orange bg-brand-orange/20 scale-[1.005]'
                : files.length > 0
                  ? 'border-brand-orange/50 bg-brand-orange/5'
                  : 'border-neutral-800 hover:border-neutral-700 bg-neutral-950/50'
            } ${status !== 'idle' && status !== 'error' ? 'pointer-events-none opacity-50' : 'cursor-pointer'}`}
          >
            <input
              ref={fileInputRef}
              type="file"
              id="file-upload"
              multiple
              accept=".txt,.cfg,.conf,text/plain"
              className="hidden"
              onChange={handleFileChange}
              disabled={status === 'processing' || status === 'success'}
            />
            <div className="flex flex-col items-center justify-center pointer-events-none select-none">
              <FileUp className={`w-10 h-10 mb-4 transition-colors ${isDragging ? 'text-brand-orange animate-bounce' : files.length > 0 ? 'text-brand-orange' : 'text-neutral-600'}`} />
              <span className="text-white font-mono text-sm mb-2 max-w-xl text-center leading-relaxed">
                {isDragging ? (
                  <span className="text-brand-orange font-bold">Release to drop configuration files</span>
                ) : files.length === 0 ? (
                  "Drop a configuration file, choose a file, or paste configuration with Ctrl+V / Cmd+V."
                ) : files.length === 1 ? (
                  <span className="text-brand-orange font-bold">{files[0].name}</span>
                ) : (
                  <span>
                    <strong className="text-brand-orange">{files.length}</strong> configuration files selected
                  </span>
                )}
              </span>
              <span className="text-neutral-500 text-xs uppercase tracking-widest font-bold">
                {files.length > 0
                  ? "Click to choose additional files (.txt, .cfg, .conf)"
                  : "Supported extensions: .txt, .cfg, .conf"}
              </span>
              <span className="mt-2 text-[11px] font-mono text-brand-orange/80 block">
                Tip: copy Cisco configuration text and paste it here.
              </span>
            </div>

            {files.length > 0 && (
              <div 
                className="mt-4 pt-4 border-t border-neutral-800/80 flex flex-col gap-2"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex flex-wrap items-center justify-center gap-2 max-h-32 overflow-y-auto px-2">
                  {files.map((file, idx) => (
                    <span
                      key={`${file.name}-${idx}`}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-neutral-900 border border-neutral-700/80 text-neutral-200 text-xs font-mono rounded-sm"
                    >
                      <span>{file.name}</span>
                      <button
                        type="button"
                        onClick={(e) => removeFile(idx, e)}
                        title="Remove file"
                        className="text-neutral-400 hover:text-brand-orange transition-colors"
                      >
                        <X size={13} />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex justify-center pt-2">
                  <button
                    type="button"
                    onClick={clearAllFiles}
                    className="text-xs text-neutral-500 hover:text-brand-orange font-mono uppercase tracking-widest transition-colors"
                  >
                    Clear All Files
                  </button>
                </div>
              </div>
            )}
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

