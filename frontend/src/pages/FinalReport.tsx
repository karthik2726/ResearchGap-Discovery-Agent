import React, { useRef } from 'react';
import { FileText, Download, Loader2 } from 'lucide-react';
import { useTask } from '../TaskContext';

export default function FinalReport() {
  const printRef = useRef<HTMLDivElement>(null);
  const { results, isLoading, isCompleted, taskStatus } = useTask();

  const handleDownloadPdf = () => {
    window.print();
  };

  const hasMasterReport = isCompleted && results?.master_report;

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="w-8 h-8 text-blue-500" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Master Intelligence Report</h2>
        </div>
        <button
          onClick={handleDownloadPdf}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          <Download size={18} />
          Export to PDF
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">
          <Loader2 className="animate-spin flex-shrink-0" size={18} />
          <span className="text-sm font-medium">Generating report… <span className="opacity-70">{taskStatus}</span></span>
        </div>
      )}

      <div ref={printRef} className="p-10 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm prose prose-blue dark:prose-invert max-w-none text-gray-800 dark:text-gray-200">
        {hasMasterReport ? (
          <div className="whitespace-pre-wrap leading-relaxed">{results!.master_report}</div>
        ) : (
          <>
            <h1 className="text-gray-900 dark:text-white">Executive Summary</h1>
            <p>
              This report aggregates the findings from the Agentic Intelligence workflow analyzing the provided document corpus.
              The overall landscape indicates a strong leaning towards healthcare and agentic models.
            </p>

            <h2 className="text-gray-900 dark:text-white">Research Landscape</h2>
            <p>Major themes identified include Federated Learning, Multi-Agent LLM Orchestration, and Mobile Edge Computing.</p>

            <h2 className="text-gray-900 dark:text-white">Top Identified Gaps</h2>
            <ul>
              <li><strong>Agentic Healthcare Monitoring</strong>: Lack of research on multi-agent patient monitoring.</li>
              <li><strong>Federated Learning Edge</strong>: Missing latency metrics for edge-based transformers.</li>
            </ul>

            <h2 className="text-gray-900 dark:text-white">Top Ideas Generated</h2>
            <ol>
              <li><strong>MedAgent System</strong> (Innovation: 9.5) - Orchestrating specialized LLMs for vitals tracking.</li>
            </ol>

            <h2 className="text-gray-900 dark:text-white">Paper Quality Audit</h2>
            <p><strong>Most Reliable:</strong> medical_transformers.pdf (Score: 88)</p>
            <p><strong>Weakest:</strong> agent_paper.pdf (Score: 45.5) - Small sample size.</p>

            <h2 className="text-gray-900 dark:text-white">Recommendations</h2>
            <p>Prioritize research addressing the "Agentic Healthcare Monitoring" gap. The MedAgent System proposes an optimal approach leveraging existing state-of-the-art frameworks like LangGraph to overcome the data availability hurdle.</p>

            {!isLoading && !isCompleted && (
              <p className="text-sm text-gray-500 dark:text-gray-400 italic mt-8 border-t border-gray-100 dark:border-gray-800 pt-4">
                This is sample content. Upload research papers to generate a real master report.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
