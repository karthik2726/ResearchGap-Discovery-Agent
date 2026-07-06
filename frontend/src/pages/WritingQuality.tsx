import React from 'react';
import { PenTool, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';
import { useTask } from '../TaskContext';

const mockWriting = {
  filename: "agent_paper.pdf",
  readabilityScore: 65,
  clarityScore: 70,
  academicQualityScore: 85,
  humanizationScore: 92,
  problems: ["Inconsistent citation formats", "Contradictory sentence in introduction"],
  suggestions: ["Use active voice", "Unify citation style"]
};

export default function WritingQuality() {
  const { results, isLoading, isCompleted, taskStatus } = useTask();

  const writing = isCompleted && results?.writing_evaluations && Object.keys(results.writing_evaluations).length
    ? (() => {
        const [filename, w] = Object.entries(results.writing_evaluations)[0];
        return {
          filename,
          readabilityScore: w.readability_score ?? 0,
          clarityScore: w.clarity_score ?? 0,
          academicQualityScore: w.academic_quality_score ?? 0,
          humanizationScore: w.humanization_score ?? 0,
          problems: w.problems ?? [],
          suggestions: w.suggestions ?? [],
        };
      })()
    : mockWriting;

  const chartData = [
    { subject: 'Readability', A: writing.readabilityScore, fullMark: 100 },
    { subject: 'Clarity', A: writing.clarityScore, fullMark: 100 },
    { subject: 'Academic Quality', A: writing.academicQualityScore, fullMark: 100 },
    { subject: 'Humanization', A: writing.humanizationScore, fullMark: 100 },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-2">
        <PenTool className="w-8 h-8 text-blue-500" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Academic Writing Evaluator</h2>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">
          <Loader2 className="animate-spin flex-shrink-0" size={18} />
          <span className="text-sm font-medium">Evaluating writing… <span className="opacity-70">{taskStatus}</span></span>
        </div>
      )}

      {!isCompleted && !isLoading && (
        <p className="text-sm text-gray-500 dark:text-gray-400 italic">Showing demo data. Upload papers to evaluate writing quality.</p>
      )}

      <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400">
        Evaluating: <span className="font-semibold text-gray-900 dark:text-white">{writing.filename}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col items-center justify-center">
          <h3 className="text-lg font-semibold mb-4 w-full text-left text-gray-900 dark:text-white">Quality Metrics (Radar)</h3>
          <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 10 }} />
                <Radar name="Score" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Humanization Score</h3>
              <span className="text-3xl font-bold text-blue-500">{writing.humanizationScore}/100</span>
            </div>
            <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2 mb-3">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${writing.humanizationScore}%` }} />
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Measures how natural, varied, and academically polished the writing appears.</p>
          </div>

          {writing.problems.length > 0 && (
            <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
              <h3 className="text-lg font-semibold mb-4 text-red-500 flex items-center gap-2"><AlertCircle size={20}/> Issues Found</h3>
              <ul className="space-y-2">
                {writing.problems.map((p, i) => (
                  <li key={i} className="text-sm bg-red-50 dark:bg-red-900/10 text-gray-700 dark:text-gray-300 p-3 rounded-lg border border-red-100 dark:border-red-900/20">{p}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
            <h3 className="text-lg font-semibold mb-4 text-emerald-500 flex items-center gap-2"><CheckCircle size={20}/> Improvement Suggestions</h3>
            <ul className="space-y-2">
              {writing.suggestions.map((s, i) => (
                <li key={i} className="text-sm bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 p-3 rounded-lg border border-gray-100 dark:border-gray-700">{s}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
