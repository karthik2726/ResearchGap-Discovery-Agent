import React from 'react';
import { Target, AlertCircle, Loader2 } from 'lucide-react';
import { useTask } from '../TaskContext';

const mockGaps = [
  {
    title: "Agentic Healthcare Monitoring",
    description: "Lack of research on using multi-agent systems for continuous patient monitoring instead of single-model approaches.",
    impact: "High",
    difficulty: 8.5
  },
  {
    title: "Federated Learning on Edge Devices",
    description: "Missing experiments regarding power consumption and latency when training transformers on mobile edge devices.",
    impact: "Medium",
    difficulty: 9.0
  }
];

export default function GapAnalysis() {
  const { results, isLoading, isCompleted, taskStatus } = useTask();

  const gaps = isCompleted && results?.research_gaps?.length
    ? results.research_gaps.map(g => ({
        title: g.title || g.gap || 'Research Gap',
        gapType: g.gap_type || 'Implicit Gap',
        description: g.description || '',
        evidence: g.evidence || '',
        impact: g.potential_impact || 'Medium',
        opportunity: g.research_opportunity || '',
        difficulty: g.difficulty_score ?? g.difficulty ?? 7,
      }))
    : mockGaps.map(g => ({
        title: g.title,
        gapType: 'Demo Gap',
        description: g.description,
        evidence: 'This is a sample evidence excerpt from the document context supporting this gap.',
        impact: g.impact,
        opportunity: 'Address this gap by running localized trials on low-power devices.',
        difficulty: g.difficulty,
      }));

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-2">
        <Target className="w-8 h-8 text-purple-500 animate-pulse" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Research Gap Analysis</h2>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">
          <Loader2 className="animate-spin flex-shrink-0" size={18} />
          <span className="text-sm font-medium">Analyzing gaps… <span className="opacity-70">{taskStatus}</span></span>
        </div>
      )}

      {!isCompleted && !isLoading && (
        <p className="text-sm text-gray-500 dark:text-gray-400 italic">Showing demo data. Upload papers to see AI-generated gaps.</p>
      )}

      <div className="grid grid-cols-1 gap-6">
        {gaps.map((gap, i) => (
          <div key={i} className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden group hover:border-purple-500/30 transition-all">
            <div className={`absolute top-0 right-0 w-2 h-full ${gap.impact.toLowerCase() === 'high' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
            
            <div className="flex items-center justify-between mb-3 pr-4 flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 text-xs font-bold rounded-lg border border-purple-100 dark:border-purple-950">
                  {gap.gapType}
                </span>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">{gap.title}</h3>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${gap.impact.toLowerCase() === 'high' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'}`}>
                {gap.impact} Impact
              </span>
            </div>
            
            <p className="text-gray-600 dark:text-gray-300 mb-4 text-sm leading-relaxed">{gap.description}</p>
            
            {gap.evidence && (
              <div className="mb-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-950 border border-gray-150 dark:border-gray-850 text-xs text-gray-500 dark:text-gray-400">
                <span className="font-bold block text-gray-700 dark:text-gray-300 mb-1">Supporting Evidence / Excerpt:</span>
                <blockquote className="italic leading-relaxed">"{gap.evidence}"</blockquote>
              </div>
            )}

            {gap.opportunity && (
              <div className="mb-4 p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/10 border border-emerald-100/30 dark:border-emerald-900/20 text-xs text-emerald-800 dark:text-emerald-300">
                <span className="font-bold block text-emerald-700 dark:text-emerald-400 mb-1">Research Opportunity:</span>
                <p className="leading-relaxed">{gap.opportunity}</p>
              </div>
            )}

            <div className="flex items-center justify-between text-xs font-semibold text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-800 pt-4 mt-2">
              <div className="flex items-center gap-2">
                <AlertCircle size={14} className="text-purple-400" />
                <span>Difficulty Score: {gap.difficulty.toFixed(1)} / 10</span>
              </div>
              <div className="w-24 bg-gray-200 dark:bg-gray-800 rounded-full h-1.5 overflow-hidden">
                <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: `${gap.difficulty * 10}%` }}></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

