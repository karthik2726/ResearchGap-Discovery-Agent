import React from 'react';
import { ShieldAlert, AlertTriangle, Loader2 } from 'lucide-react';
import { useTask } from '../TaskContext';

const mockAudits = [
  {
    filename: "agent_paper.pdf",
    reliabilityScore: 45.5,
    methodologyProblems: ["Small sample size (n=10)"],
    statisticalProblems: ["Missing significance testing"],
    reproducibilityProblems: ["No code repository linked"]
  }
];

export default function QualityAudit() {
  const { results, isLoading, isCompleted, taskStatus } = useTask();

  const audits = isCompleted && results?.quality_audits && Object.keys(results.quality_audits).length
    ? Object.entries(results.quality_audits).map(([filename, a]) => ({
        filename,
        reliabilityScore: a.reliability_score ?? 0,
        methodologyProblems: a.methodology_problems ?? [],
        statisticalProblems: a.statistical_problems ?? [],
        reproducibilityProblems: a.reproducibility_problems ?? [],
      }))
    : mockAudits;

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-2">
        <ShieldAlert className="w-8 h-8 text-red-500" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Paper Quality Audit</h2>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">
          <Loader2 className="animate-spin flex-shrink-0" size={18} />
          <span className="text-sm font-medium">Auditing papers… <span className="opacity-70">{taskStatus}</span></span>
        </div>
      )}

      {!isCompleted && !isLoading && (
        <p className="text-sm text-gray-500 dark:text-gray-400 italic">Showing demo data. Upload papers to see AI quality audits.</p>
      )}

      <div className="space-y-6">
        {audits.map((audit, i) => (
          <div key={i} className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
            <div className="flex justify-between items-center mb-6 pb-6 border-b border-gray-100 dark:border-gray-800">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{audit.filename}</h3>
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Reliability Score</span>
                <span className={`text-2xl font-bold ${audit.reliabilityScore > 70 ? 'text-emerald-500' : audit.reliabilityScore > 40 ? 'text-yellow-500' : 'text-red-500'}`}>
                  {audit.reliabilityScore} / 100
                </span>
              </div>
            </div>

            {/* Score bar */}
            <div className="mb-6">
              <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all ${audit.reliabilityScore > 70 ? 'bg-emerald-500' : audit.reliabilityScore > 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${audit.reliabilityScore}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <h4 className="font-medium text-sm flex items-center gap-2 text-orange-500">
                  <AlertTriangle size={16} /> Methodology
                </h4>
                <ul className="space-y-2">
                  {audit.methodologyProblems.length ? audit.methodologyProblems.map((p, idx) => (
                    <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 bg-orange-50 dark:bg-orange-900/10 p-2 rounded border border-orange-100 dark:border-orange-900/20">{p}</li>
                  )) : <li className="text-sm text-gray-400 italic">No issues found</li>}
                </ul>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-sm flex items-center gap-2 text-purple-500">
                  <AlertTriangle size={16} /> Statistics
                </h4>
                <ul className="space-y-2">
                  {audit.statisticalProblems.length ? audit.statisticalProblems.map((p, idx) => (
                    <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 bg-purple-50 dark:bg-purple-900/10 p-2 rounded border border-purple-100 dark:border-purple-900/20">{p}</li>
                  )) : <li className="text-sm text-gray-400 italic">No issues found</li>}
                </ul>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-sm flex items-center gap-2 text-blue-500">
                  <AlertTriangle size={16} /> Reproducibility
                </h4>
                <ul className="space-y-2">
                  {audit.reproducibilityProblems.length ? audit.reproducibilityProblems.map((p, idx) => (
                    <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 bg-blue-50 dark:bg-blue-900/10 p-2 rounded border border-blue-100 dark:border-blue-900/20">{p}</li>
                  )) : <li className="text-sm text-gray-400 italic">No issues found</li>}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
