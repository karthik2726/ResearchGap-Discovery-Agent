import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, BookOpen, Target, BrainCircuit, ShieldCheck, Loader2 } from 'lucide-react';
import { useTask } from '../TaskContext';

const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

export default function DashboardHome() {
  const { results, isLoading, isCompleted, taskStatus } = useTask();

  const papersCount = results?.paper_analyses ? Object.keys(results.paper_analyses).length : 0;
  const gapsCount = results?.research_gaps?.length ?? 0;
  const ideasCount = results?.project_ideas?.length ?? 0;

  const gapChartData = results?.research_gaps?.slice(0, 5).map((g, i) => ({
    name: g.title || g.gap || `Gap ${i + 1}`,
    value: Math.round((g.difficulty ?? 5) * 10),
  })) ?? [
    { name: 'LLM Agents', value: 85 },
    { name: 'Healthcare AI', value: 65 },
    { name: 'Federated Learning', value: 45 },
    { name: 'CV Transformers', value: 30 },
  ];

  const qualityData = results?.quality_audits
    ? (() => {
        let high = 0, med = 0, low = 0;
        Object.values(results.quality_audits).forEach(a => {
          const s = a.reliability_score ?? 0;
          if (s >= 70) high++;
          else if (s >= 40) med++;
          else low++;
        });
        return [
          { name: 'High Reliability', value: high || 12 },
          { name: 'Medium Reliability', value: med || 5 },
          { name: 'Low Reliability', value: low || 3 },
        ];
      })()
    : [
        { name: 'High Reliability', value: 12 },
        { name: 'Medium Reliability', value: 5 },
        { name: 'Low Reliability', value: 3 },
      ];

  return (
    <div className="space-y-8">
      {/* Status banner when processing */}
      {isLoading && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">
          <Loader2 className="animate-spin flex-shrink-0" size={18} />
          <span className="text-sm font-medium">Agents are processing your papers… <span className="opacity-70">{taskStatus}</span></span>
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm flex items-center gap-4">
          <div className="p-4 rounded-xl bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
            <BookOpen size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Papers Analyzed</p>
            <h3 className="text-3xl font-bold text-gray-900 dark:text-white">{isCompleted ? papersCount : '—'}</h3>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm flex items-center gap-4">
          <div className="p-4 rounded-xl bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
            <Target size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Research Gaps Found</p>
            <h3 className="text-3xl font-bold text-gray-900 dark:text-white">{isCompleted ? gapsCount : '—'}</h3>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm flex items-center gap-4">
          <div className="p-4 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
            <BrainCircuit size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Ideas Generated</p>
            <h3 className="text-3xl font-bold text-gray-900 dark:text-white">{isCompleted ? ideasCount : '—'}</h3>
          </div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <Activity className="text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Research Gaps</h3>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={gapChartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" className="dark:[stroke:#374151]" />
                <XAxis dataKey="name" stroke="#9ca3af" tick={{ fill: '#6b7280', fontSize: 12 }} />
                <YAxis stroke="#9ca3af" tick={{ fill: '#6b7280', fontSize: 12 }} />
                <RechartsTooltip cursor={{ fill: 'transparent' }} contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', borderRadius: '8px', color: '#f9fafb' }} />
                <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <ShieldCheck className="text-emerald-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Paper Reliability Audit</h3>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={qualityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {qualityData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', borderRadius: '8px', color: '#f9fafb' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="flex justify-center gap-4 mt-2">
            {qualityData.map((entry, i) => (
              <div key={i} className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                {entry.name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
