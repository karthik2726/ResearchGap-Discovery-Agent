import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

export interface AnalysisResults {
  paper_analyses?: Record<string, any>;
  topic_clusters?: Array<{ name: string; size?: number; count?: number }>;
  research_landscape?: string;
  research_gaps?: Array<{
    title?: string;
    description?: string;
    gap?: string;
    impact?: string;
    difficulty?: number;
  }>;
  project_ideas?: Array<{
    title?: string;
    description?: string;
    innovation_score?: number;
    difficulty?: string;
    tech_stack?: string[];
  }>;
  quality_audits?: Record<string, {
    reliability_score?: number;
    methodology_problems?: string[];
    statistical_problems?: string[];
    reproducibility_problems?: string[];
  }>;
  writing_evaluations?: Record<string, {
    readability_score?: number;
    clarity_score?: number;
    academic_quality_score?: number;
    humanization_score?: number;
    problems?: string[];
    suggestions?: string[];
  }>;
  master_report?: string;
}

interface TaskContextType {
  taskId: string | null;
  setTaskId: (id: string) => void;
  taskStatus: string;
  results: AnalysisResults | null;
  isLoading: boolean;
  isCompleted: boolean;
  hasError: boolean;
}

const TaskContext = createContext<TaskContextType>({
  taskId: null,
  setTaskId: () => {},
  taskStatus: '',
  results: null,
  isLoading: false,
  isCompleted: false,
  hasError: false,
});

export function TaskProvider({ children }: { children: ReactNode }) {
  const [taskId, setTaskIdState] = useState<string | null>(() => {
    return localStorage.getItem('researchiq_task_id');
  });
  const [taskStatus, setTaskStatus] = useState('');
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [hasError, setHasError] = useState(false);

  const setTaskId = useCallback((id: string) => {
    setTaskIdState(id);
    localStorage.setItem('researchiq_task_id', id);
    setResults(null);
    setIsCompleted(false);
    setHasError(false);
    setTaskStatus('Pending');
  }, []);

  useEffect(() => {
    if (taskId && !isCompleted) {
      setIsLoading(true);
      let intervalId: ReturnType<typeof setInterval>;

      const poll = async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/api/status/${taskId}`);
          const statusData = await statusRes.json();
          const status: string = statusData.status || '';
          setTaskStatus(status);

          if (status === 'Completed') {
            clearInterval(intervalId);
            const resultsRes = await fetch(`http://localhost:8000/api/results/${taskId}`);
            const data = await resultsRes.json();
            setResults(data);
            setIsCompleted(true);
            setIsLoading(false);
          } else if (status.startsWith('Error')) {
            clearInterval(intervalId);
            setHasError(true);
            setIsLoading(false);
          }
        } catch (e) {
          console.error('Polling error:', e);
        }
      };

      poll();
      intervalId = setInterval(poll, 3000);
      return () => clearInterval(intervalId);
    } else if (!taskId && !results) {
      const fetchHistorical = async () => {
        try {
          const res = await fetch("http://localhost:8000/api/historical-results");
          const data = await res.json();
          if (data && data.paper_analyses && Object.keys(data.paper_analyses).length > 0) {
            setResults(data);
            setIsCompleted(true);
          }
        } catch (e) {
          console.error("Failed to load historical results", e);
        }
      };
      fetchHistorical();
    }
  }, [taskId, isCompleted, results]);

  return (
    <TaskContext.Provider value={{ taskId, setTaskId, taskStatus, results, isLoading, isCompleted, hasError }}>
      {children}
    </TaskContext.Provider>
  );
}

export function useTask() {
  return useContext(TaskContext);
}
