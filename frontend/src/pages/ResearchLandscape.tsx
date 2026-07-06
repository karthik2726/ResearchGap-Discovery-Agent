import React from 'react';
import { Map, Layers, Loader2 } from 'lucide-react';
import { ResponsiveContainer, Treemap } from 'recharts';
import { useTask } from '../TaskContext';

const mockClusters = [
  { name: 'Agentic AI Workflows', size: 400 },
  { name: 'Healthcare Predictive Modeling', size: 300 },
  { name: 'Federated Learning Privacy', size: 200 },
  { name: 'Vision Transformers', size: 150 }
];

const TREE_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

export default function ResearchLandscape() {
  const { results, isLoading, isCompleted, taskStatus } = useTask();

  const clusters = isCompleted && results?.topic_clusters?.length
    ? results.topic_clusters.map(c => ({
        name: c.name,
        size: c.size ?? c.count ?? 100,
      }))
    : mockClusters;

  const landscapeSummary = isCompleted && results?.research_landscape
    ? results.research_landscape
    : 'The uploaded papers predominantly cluster around Agentic AI systems and Healthcare Predictive Modeling. There is a strong intersection between decentralized learning frameworks (Federated Learning) and privacy-preserving clinical datasets.';

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-2">
        <Map className="w-8 h-8 text-blue-500" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Research Landscape</h2>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">
          <Loader2 className="animate-spin flex-shrink-0" size={18} />
          <span className="text-sm font-medium">Mapping landscape… <span className="opacity-70">{taskStatus}</span></span>
        </div>
      )}

      {!isCompleted && !isLoading && (
        <p className="text-sm text-gray-500 dark:text-gray-400 italic">Showing demo data. Upload papers to see the real topic distribution.</p>
      )}

      <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Topic Distribution (Treemap)</h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <Treemap
              data={clusters}
              dataKey="size"
              aspectRatio={4 / 3}
              stroke="#fff"
              content={({ x, y, width, height, index, name }: any) => {
                const color = TREE_COLORS[index % TREE_COLORS.length];
                return (
                  <g>
                    <rect x={x} y={y} width={width} height={height} fill={color} fillOpacity={0.85} rx={4} />
                    {width > 60 && height > 30 && (
                      <text x={x + width / 2} y={y + height / 2} textAnchor="middle" dominantBaseline="middle" fill="#fff" fontSize={Math.min(12, width / 8)} fontWeight={600}>
                        {name}
                      </text>
                    )}
                  </g>
                );
              }}
            />
          </ResponsiveContainer>
        </div>
      </div>

      <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="text-purple-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Landscape Summary</h3>
        </div>
        <p className="text-gray-600 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{landscapeSummary}</p>
      </div>
    </div>
  );
}
