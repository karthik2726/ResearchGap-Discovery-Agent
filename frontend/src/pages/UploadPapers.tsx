import React, { useState, useCallback } from 'react';
import { UploadCloud, File, X, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { useTask } from '../TaskContext';

export default function UploadPapers() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { taskId, setTaskId, taskStatus, isLoading, isCompleted, hasError } = useTask();

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
    setFiles(prev => [...prev, ...droppedFiles]);
  }, []);

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 90) { clearInterval(interval); return 90; }
        return p + 10;
      });
    }, 500);

    const formData = new FormData();
    files.forEach(file => formData.append("files", file));

    try {
      const res = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setTaskId(data.task_id);
      setProgress(100);
      setFiles([]);
    } catch (error) {
      console.error("Upload failed", error);
    } finally {
      clearInterval(interval);
      setUploading(false);
    }
  };

  const statusColor = isCompleted
    ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
    : hasError
    ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800'
    : 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800';

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="text-center space-y-2 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Upload Research Papers</h2>
        <p className="text-gray-500 dark:text-gray-400">Upload PDF files. Our AI agents will analyze them to find gaps, audit quality, and generate novel ideas.</p>
      </div>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-3xl p-12 text-center bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
      >
        <UploadCloud className="w-16 h-16 mx-auto text-blue-500 mb-4" />
        <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Drag &amp; Drop PDFs here</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6">or click to browse from your computer</p>
        <input
          type="file"
          multiple
          accept="application/pdf"
          className="hidden"
          id="file-upload"
          onChange={(e) => setFiles(prev => [...prev, ...Array.from(e.target.files || [])])}
        />
        <label htmlFor="file-upload" className="px-6 py-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors cursor-pointer">
          Select Files
        </label>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h4 className="font-semibold mb-4 text-gray-900 dark:text-white">Selected Files ({files.length})</h4>
          <ul className="space-y-3 mb-6">
            {files.map((f, i) => (
              <li key={i} className="flex justify-between items-center p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                <div className="flex items-center gap-3">
                  <File className="text-blue-500" size={20} />
                  <span className="text-sm font-medium truncate max-w-md text-gray-800 dark:text-gray-200">{f.name}</span>
                </div>
                <button onClick={() => setFiles(files.filter((_, idx) => idx !== i))} className="text-gray-400 hover:text-red-500">
                  <X size={20} />
                </button>
              </li>
            ))}
          </ul>

          {uploading ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm font-medium text-gray-700 dark:text-gray-300">
                <span>Uploading...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full transition-all" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          ) : (
            <button
              onClick={handleUpload}
              className="w-full py-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              <UploadCloud size={20} />
              Launch AI Analysis
            </button>
          )}
        </div>
      )}

      {/* Task status banner */}
      {taskId && (
        <div className="space-y-6">
          <div className={`p-4 rounded-2xl flex items-start gap-3 ${statusColor}`}>
            {isCompleted ? (
              <CheckCircle className="mt-0.5 flex-shrink-0" size={20} />
            ) : hasError ? (
              <AlertCircle className="mt-0.5 flex-shrink-0" size={20} />
            ) : (
              <Loader2 className="mt-0.5 flex-shrink-0 animate-spin" size={20} />
            )}
            <div>
              <p className="font-semibold">
                {isCompleted ? 'Analysis Complete!' : hasError ? 'Analysis Failed' : 'Agents are Working…'}
              </p>
              <p className="text-sm mt-0.5 opacity-80">
                {hasError
                  ? `Error: ${taskStatus}`
                  : isCompleted
                  ? 'Navigate to Research Landscape, Gap Analysis, Quality Audit, Idea Generator, or Writing Quality to view results.'
                  : `Current Pipeline Stage: ${taskStatus || 'Initializing…'}`}
              </p>
              <p className="text-xs mt-1 opacity-60">Task ID: {taskId}</p>
            </div>
          </div>

          {/* Pipeline stages list */}
          {!hasError && (
            <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 border border-gray-250 dark:border-gray-850 shadow-sm space-y-4">
              <h4 className="font-bold text-xs uppercase tracking-wider text-gray-400">AI Processing Pipeline Status</h4>
              <div className="space-y-3">
                {[
                  { name: "PDF Text Extraction & Parsing", match: ["Processing", "Parsing", "Pending"] },
                  { name: "Parent-Child Chunking & Dense Embeddings", match: ["Chunking", "Indexing"] },
                  { name: "LangGraph Multi-Agent Orchestration", match: ["Agentic", "Running"] },
                  { name: "SQLite Database & Result Persistence", match: ["Persisting", "Saving"] }
                ].map((step, idx) => {
                  let isDone = isCompleted;
                  let isActive = false;
                  
                  if (!isCompleted && taskStatus) {
                    const statusLower = taskStatus.toLowerCase();
                    // Determine if this step is done or active
                    const matchesStep = step.match.some(m => statusLower.includes(m.toLowerCase()));
                    if (matchesStep) {
                      isActive = true;
                    }
                    
                    // Previous steps are done
                    if (idx === 0 && (statusLower.includes("chunking") || statusLower.includes("indexing") || statusLower.includes("agentic") || statusLower.includes("persisting"))) {
                      isDone = true;
                    }
                    if (idx === 1 && (statusLower.includes("agentic") || statusLower.includes("persisting"))) {
                      isDone = true;
                    }
                    if (idx === 2 && statusLower.includes("persisting")) {
                      isDone = true;
                    }
                  }

                  return (
                    <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-950 border border-gray-150 dark:border-gray-850">
                      <div className="flex items-center gap-3">
                        {isDone ? (
                          <CheckCircle className="text-emerald-500 flex-shrink-0" size={18} />
                        ) : isActive ? (
                          <Loader2 className="text-blue-500 animate-spin flex-shrink-0" size={18} />
                        ) : (
                          <div className="w-[18px] h-[18px] rounded-full border border-gray-300 dark:border-gray-700 flex-shrink-0"></div>
                        )}
                        <span className={`text-xs font-semibold ${isDone ? 'text-gray-500 dark:text-gray-400 line-through decoration-gray-400' : isActive ? 'text-blue-500 font-bold' : 'text-gray-700 dark:text-gray-300'}`}>
                          {step.name}
                        </span>
                      </div>
                      <span className={`text-xxs px-2 py-0.5 rounded font-bold ${isDone ? 'bg-emerald-500/10 text-emerald-500' : isActive ? 'bg-blue-500/10 text-blue-500 animate-pulse' : 'bg-gray-100 dark:bg-gray-800 text-gray-400'}`}>
                        {isDone ? 'Complete' : isActive ? 'Processing' : 'Pending'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
