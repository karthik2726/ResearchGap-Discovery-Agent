import React from 'react';
import { Lightbulb, Code, Loader2 } from 'lucide-react';
import { useTask } from '../TaskContext';

const mockIdeas = [
  {
    title: "MedAgent: AI Nurse System",
    description: "A multi-agent system orchestrating specialized LLMs for continuous vitals monitoring and alert triage.",
    innovationScore: 9.5,
    difficulty: "Expert",
    techStack: ["LangGraph", "FastAPI", "React", "Kafka"]
  }
];

export default function IdeaGenerator() {
  const { results, isLoading, isCompleted, taskStatus } = useTask();

  const ideas = isCompleted && results?.project_ideas?.length
    ? results.project_ideas.map(idea => ({
        title: idea.title || 'Research Idea',
        innovationCategory: idea.innovation_category || 'Moderate Innovation',
        description: idea.description || '',
        noveltyScore: idea.novelty_score ?? 7.0,
        feasibilityScore: idea.feasibility_score ?? 7.0,
        requiredDataset: idea.required_dataset || 'None specified',
        methodology: idea.methodology || '',
        expectedOutcome: idea.expected_outcome || '',
        implementationRoadmap: idea.implementation_roadmap ?? [],
        difficulty: idea.difficulty || 'Medium',
        techStack: idea.tech_stack ?? [],
      }))
    : mockIdeas.map(idea => ({
        title: idea.title,
        innovationCategory: 'Moderate Innovation',
        description: idea.description,
        noveltyScore: idea.innovationScore,
        feasibilityScore: 8.0,
        requiredDataset: 'MIMIC-IV Clinical Database',
        methodology: 'Distributed training using secure federated learning nodes and differential privacy.',
        expectedOutcome: '95% diagnostic accuracy with zero client data leakage.',
        implementationRoadmap: [
          'Pre-process healthcare vitals signals',
          'Deploy local differential privacy checks',
          'Train federated learning nodes asynchronously',
          'Audit and validate convergence on validation set'
        ],
        difficulty: idea.difficulty,
        techStack: idea.techStack,
      }));

  const difficultyColor = (d: string) => {
    const lower = d.toLowerCase();
    if (lower === 'expert') return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
    if (lower === 'advanced') return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-2">
        <Lightbulb className="w-8 h-8 text-yellow-500 animate-pulse" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Generated Project Ideas</h2>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300">
          <Loader2 className="animate-spin flex-shrink-0" size={18} />
          <span className="text-sm font-medium">Generating ideas… <span className="opacity-70">{taskStatus}</span></span>
        </div>
      )}

      {!isCompleted && !isLoading && (
        <p className="text-sm text-gray-500 dark:text-gray-400 italic">Showing demo data. Upload papers to generate novel research ideas.</p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {ideas.map((idea, i) => (
          <div key={i} className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-sm hover:border-yellow-500/20 transition-all flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-4 gap-3">
                <div>
                  <span className="px-2 py-0.5 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 text-xs font-bold rounded-lg border border-yellow-150 dark:border-yellow-950 block mb-1.5 w-max">
                    {idea.innovationCategory}
                  </span>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">{idea.title}</h3>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold flex-shrink-0 ${difficultyColor(idea.difficulty)}`}>
                  {idea.difficulty}
                </span>
              </div>
              
              <p className="text-gray-600 dark:text-gray-300 mb-5 leading-relaxed text-sm">{idea.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 dark:text-gray-400 font-semibold">Novelty Score</span>
                    <span className="font-bold text-yellow-500">{idea.noveltyScore.toFixed(1)} / 10</span>
                  </div>
                  <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-yellow-400 h-1.5 rounded-full" style={{ width: `${idea.noveltyScore * 10}%` }}></div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 dark:text-gray-400 font-semibold">Feasibility Score</span>
                    <span className="font-bold text-emerald-500">{idea.feasibilityScore.toFixed(1)} / 10</span>
                  </div>
                  <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-emerald-400 h-1.5 rounded-full" style={{ width: `${idea.feasibilityScore * 10}%` }}></div>
                  </div>
                </div>
              </div>

              {idea.methodology && (
                <div className="mb-4 text-xs">
                  <span className="font-bold text-gray-700 dark:text-gray-300 block mb-1">Proposed Methodology:</span>
                  <p className="text-gray-500 dark:text-gray-400 leading-relaxed bg-gray-50 dark:bg-gray-950 p-3 rounded-lg border border-gray-100 dark:border-gray-850">{idea.methodology}</p>
                </div>
              )}

              {idea.requiredDataset && idea.requiredDataset !== 'None specified' && (
                <div className="mb-4 text-xs">
                  <span className="font-bold text-gray-700 dark:text-gray-300 block mb-1">Required Dataset:</span>
                  <p className="text-gray-500 dark:text-gray-400 bg-blue-50/20 dark:bg-blue-900/10 p-2.5 rounded border border-blue-100/30 dark:border-blue-900/20">{idea.requiredDataset}</p>
                </div>
              )}

              {idea.expectedOutcome && (
                <div className="mb-4 text-xs">
                  <span className="font-bold text-gray-700 dark:text-gray-300 block mb-1">Expected Outcome:</span>
                  <p className="text-gray-500 dark:text-gray-400 bg-emerald-50/20 dark:bg-emerald-900/10 p-2.5 rounded border border-emerald-100/30 dark:border-emerald-900/20">{idea.expectedOutcome}</p>
                </div>
              )}

              {idea.implementationRoadmap.length > 0 && (
                <div className="mb-6 text-xs">
                  <span className="font-bold text-gray-700 dark:text-gray-300 block mb-2">Implementation Roadmap:</span>
                  <ol className="space-y-1.5 pl-4 list-decimal text-gray-500 dark:text-gray-400 leading-relaxed">
                    {idea.implementationRoadmap.map((step, idx) => (
                      <li key={idx} className="pl-1">{step}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>

            {idea.techStack.length > 0 && (
              <div className="pt-4 border-t border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400">
                  <Code size={14} /> Tech Stack
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {idea.techStack.map((tech, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded text-xxs font-semibold">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
