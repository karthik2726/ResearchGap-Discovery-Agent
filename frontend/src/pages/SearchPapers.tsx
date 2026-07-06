import React, { useState, useEffect } from 'react';
import { Search as SearchIcon, FileText, ArrowRight, Clock, ShieldCheck, Download, Trash2, RotateCcw, AlertCircle, Sparkles, Filter } from 'lucide-react';

interface Passage {
  chunk_id: string;
  text: string;
  source_file: string;
  page_number: number;
  section: string;
  rrf_score?: number;
  rerank_score?: number;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  confidence_score?: number;
  latency?: number;
  passages?: Passage[];
}

export default function SearchPapers() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Conversation and search state
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [currentPassages, setCurrentPassages] = useState<Passage[]>([]);
  const [currentConfidence, setCurrentConfidence] = useState<number | null>(null);
  const [currentLatency, setCurrentLatency] = useState<number | null>(null);

  // Filters
  const [papers, setPapers] = useState<any[]>([]);
  const [selectedPaper, setSelectedPaper] = useState('');
  const [selectedSection, setSelectedSection] = useState('');

  // Modal for Chunk Preview
  const [activeChunk, setActiveChunk] = useState<Passage | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Local storage query history
  const [queryHistory, setQueryHistory] = useState<string[]>(() => {
    const saved = localStorage.getItem('researchiq_query_history');
    return saved ? JSON.parse(saved) : [];
  });

  const sectionsList = [
    'Abstract',
    'Introduction',
    'Related Work',
    'Background',
    'Methodology',
    'Results',
    'Discussion',
    'Conclusion',
    'References',
    'Future Work'
  ];

  // Fetch papers for filter dropdown
  useEffect(() => {
    const fetchPapers = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/papers');
        const data = await res.json();
        setPapers(data);
      } catch (e) {
        console.error("Failed to fetch papers list", e);
      }
    };
    fetchPapers();
  }, []);

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    
    // Add user query to chat history
    const userMsg: ChatMessage = { role: 'user', content: searchQuery };
    setChatHistory(prev => [...prev, userMsg]);

    // Build the request body with conversational history
    // Get past messages in conversational format
    const formattedHistory = chatHistory.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    // Save search query in history list
    const updatedHistory = [searchQuery, ...queryHistory.filter(q => q !== searchQuery)].slice(0, 10);
    setQueryHistory(updatedHistory);
    localStorage.setItem('researchiq_query_history', JSON.stringify(updatedHistory));

    try {
      const res = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          history: formattedHistory,
          paper_filter: selectedPaper || null,
          section_filter: selectedSection || null
        })
      });

      if (!res.ok) throw new Error("Search request failed");

      const data = await res.json();
      
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.answer,
        confidence_score: data.confidence_score,
        latency: data.search_latency_ms,
        passages: data.passages
      };

      setChatHistory(prev => [...prev, assistantMsg]);
      setCurrentPassages(data.passages || []);
      setCurrentConfidence(data.confidence_score);
      setCurrentLatency(data.search_latency_ms);
      
    } catch (error) {
      console.error("RAG search failed", error);
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: "Error: Failed to fetch responses from search service. Please check if backend is running."
      };
      setChatHistory(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
      setQuery('');
    }
  };

  const clearChat = () => {
    setChatHistory([]);
    setCurrentPassages([]);
    setCurrentConfidence(null);
    setCurrentLatency(null);
  };

  const deleteHistoryItem = (qToDelete: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = queryHistory.filter(q => q !== qToDelete);
    setQueryHistory(updated);
    localStorage.setItem('researchiq_query_history', JSON.stringify(updated));
  };

  const exportChatToMarkdown = () => {
    if (chatHistory.length === 0) return;
    
    let content = `# ResearchIQ Intelligence Query Report\n`;
    content += `Generated on: ${new Date().toLocaleString()}\n\n`;
    
    chatHistory.forEach((msg, idx) => {
      if (msg.role === 'user') {
        content += `### Query [${idx + 1}]: ${msg.content}\n\n`;
      } else {
        content += `#### Answer:\n${msg.content}\n\n`;
        if (msg.confidence_score !== undefined) {
          content += `- **Confidence**: ${msg.confidence_score}%\n`;
          content += `- **Latency**: ${msg.latency} ms\n\n`;
        }
        if (msg.passages && msg.passages.length > 0) {
          content += `#### Supporting Citations:\n`;
          msg.passages.forEach((p, pIdx) => {
            content += `[${pIdx + 1}] **${p.source_file}** (Page ${p.page_number}, ${p.section})\n`;
            content += `> ${p.text}\n\n`;
          });
        }
        content += `---\n\n`;
      }
    });

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_query_export_${new Date().toISOString().slice(0,10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const openPreview = (passage: Passage) => {
    setActiveChunk(passage);
    setIsModalOpen(true);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 min-h-[calc(100vh-12rem)] relative">
      
      {/* Sidebar for Query History & Filters */}
      <div className="lg:col-span-1 space-y-6 flex flex-col justify-between h-full bg-gray-900/10 dark:bg-white/5 p-5 rounded-3xl border border-gray-200 dark:border-gray-800 backdrop-blur-xl">
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-800">
            <h3 className="font-bold text-sm tracking-wide uppercase text-gray-400 flex items-center gap-2">
              <Filter size={16} /> Filters
            </h3>
            {(selectedPaper || selectedSection) && (
              <button 
                onClick={() => { setSelectedPaper(''); setSelectedSection(''); }}
                className="text-xs text-blue-500 hover:text-blue-400 font-semibold flex items-center gap-1"
              >
                <RotateCcw size={12} /> Reset
              </button>
            )}
          </div>

          {/* Paper dropdown filter */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400">Filter by Paper</label>
            <select
              value={selectedPaper}
              onChange={(e) => setSelectedPaper(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-200"
            >
              <option value="">All Papers</option>
              {papers.map((p) => (
                <option key={p.id} value={p.filename}>{p.title || p.filename}</option>
              ))}
            </select>
          </div>

          {/* Section dropdown filter */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400">Filter by Section</label>
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-200"
            >
              <option value="">All Sections</option>
              {sectionsList.map((sec) => (
                <option key={sec} value={sec}>{sec}</option>
              ))}
            </select>
          </div>

          {/* Query History */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
            <h3 className="font-bold text-sm tracking-wide uppercase text-gray-400 mb-3 flex items-center gap-2">
              <Clock size={16} /> Recent Queries
            </h3>
            {queryHistory.length === 0 ? (
              <p className="text-xs text-gray-500 dark:text-gray-500 italic">No search history yet.</p>
            ) : (
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {queryHistory.map((q, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSearch(q)}
                    className="flex justify-between items-center text-xs p-2.5 rounded-xl hover:bg-gray-150 dark:hover:bg-white/5 cursor-pointer text-gray-700 dark:text-gray-300 transition-colors group"
                  >
                    <span className="truncate pr-2 font-medium">{q}</span>
                    <button 
                      onClick={(e) => deleteHistoryItem(q, e)}
                      className="text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {chatHistory.length > 0 && (
          <div className="pt-4 border-t border-gray-200 dark:border-gray-800 space-y-2">
            <button
              onClick={exportChatToMarkdown}
              className="w-full py-2.5 rounded-xl bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 font-semibold flex items-center justify-center gap-2 border border-blue-500/20 transition-colors text-xs"
            >
              <Download size={14} /> Export Query Report
            </button>
            <button
              onClick={clearChat}
              className="w-full py-2.5 rounded-xl hover:bg-red-500/10 text-gray-500 dark:text-gray-400 hover:text-red-500 font-semibold flex items-center justify-center gap-2 transition-colors text-xs"
            >
              <Trash2 size={14} /> Clear Conversation
            </button>
          </div>
        )}
      </div>

      {/* Main Conversation & Retrieval Interface */}
      <div className="lg:col-span-3 space-y-6 flex flex-col justify-between min-h-[calc(100vh-15rem)]">
        
        {/* Chat Logs & Answers */}
        <div className="flex-1 space-y-6 overflow-y-auto max-h-[calc(100vh-22rem)] pr-2">
          {chatHistory.length === 0 ? (
            <div className="text-center py-20 space-y-4 max-w-lg mx-auto">
              <div className="w-16 h-16 bg-blue-500/10 text-blue-500 rounded-3xl flex items-center justify-center mx-auto border border-blue-500/20 shadow-inner">
                <Sparkles size={28} className="animate-pulse" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Ask your Research Corpus</h2>
              <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                Query papers using advanced Semantic Hybrid Search. Retrieve key sections, get synthesized summaries, and drill down on citations.
              </p>
              <div className="flex flex-wrap gap-2 justify-center pt-4">
                <button onClick={() => setQuery("What is the core methodology used in the papers?")} className="px-3.5 py-1.5 bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-full text-xs font-semibold hover:border-blue-500 transition-colors">
                  "What is the methodology?"
                </button>
                <button onClick={() => setQuery("What limitations did the authors outline?")} className="px-3.5 py-1.5 bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-full text-xs font-semibold hover:border-blue-500 transition-colors">
                  "Show paper limitations"
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {chatHistory.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} animate-in fade-in duration-300`}>
                  {msg.role === 'user' ? (
                    <div className="p-4 rounded-2xl bg-blue-600 text-white font-medium text-sm shadow-md max-w-2xl">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="w-full space-y-4">
                      {/* Latency and Confidence badges */}
                      {msg.confidence_score !== undefined && (
                        <div className="flex items-center gap-4 text-xs font-semibold text-gray-500 dark:text-gray-400">
                          <span className="flex items-center gap-1">
                            <Clock size={14} className="text-blue-500" />
                            Latency: {msg.latency} ms
                          </span>
                          <span className="flex items-center gap-1">
                            <ShieldCheck size={14} className="text-emerald-500" />
                            Confidence: {msg.confidence_score}%
                          </span>
                        </div>
                      )}

                      {/* Answer bubble */}
                      <div className="w-full p-6 rounded-3xl bg-white dark:bg-gray-900 border border-gray-250 dark:border-gray-850 shadow-sm leading-relaxed prose dark:prose-invert max-w-none text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                        {msg.content}
                      </div>

                      {/* Citation Passage List */}
                      {msg.passages && msg.passages.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Retrieved Passages &amp; Citations:</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {msg.passages.map((p, idx) => (
                              <div
                                key={idx}
                                onClick={() => openPreview(p)}
                                className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-950 border border-gray-150 dark:border-gray-850 hover:border-blue-500/40 dark:hover:border-blue-500/40 cursor-pointer transition-all flex flex-col justify-between group"
                              >
                                <div>
                                  <div className="flex items-center justify-between text-xs font-bold text-blue-500 mb-2">
                                    <span className="flex items-center gap-1 truncate max-w-[150px]">
                                      <FileText size={12} />
                                      {p.source_file}
                                    </span>
                                    <span className="px-2 py-0.5 bg-blue-500/10 text-blue-500 rounded text-xxs border border-blue-500/10">
                                      Page {p.page_number} • {p.section}
                                    </span>
                                  </div>
                                  <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-3">
                                    "{p.text}"
                                  </p>
                                </div>
                                <div className="mt-3 pt-2.5 border-t border-gray-200/40 dark:border-gray-800/40 text-xxs font-bold text-gray-400 group-hover:text-blue-500 flex items-center justify-between transition-colors">
                                  <span>View context</span>
                                  <ArrowRight size={10} className="transform group-hover:translate-x-1 transition-transform" />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="space-y-4">
          {/* Form input */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleSearch(query); }}
            className="relative flex items-center"
          >
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <SearchIcon className="text-gray-400" size={20} />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
              placeholder="Query papers, e.g., 'What are the dataset limitations?'..."
              className="w-full pl-12 pr-32 py-4 rounded-2xl border border-gray-250 dark:border-gray-850 bg-white dark:bg-gray-900 shadow-sm focus:ring-1 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-sm text-gray-800 dark:text-gray-200 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute inset-y-2 right-2 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-800 text-white font-semibold text-xs transition-colors flex items-center gap-1.5"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Searching...
                </>
              ) : (
                'Query'
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Chunk Context Preview Modal */}
      {isModalOpen && activeChunk && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-850 shadow-2xl p-6 relative overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]">
            
            <div className="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-800 mb-4 flex-shrink-0">
              <div className="flex items-center gap-2 text-blue-500">
                <FileText size={20} />
                <div>
                  <h4 className="font-bold text-sm text-gray-900 dark:text-white truncate max-w-md">{activeChunk.source_file}</h4>
                  <span className="text-xs text-gray-400">Page {activeChunk.page_number} • Section: {activeChunk.section}</span>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="w-8 h-8 rounded-full hover:bg-gray-100 dark:hover:bg-white/10 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 flex items-center justify-center transition-colors text-lg"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto text-sm text-gray-700 dark:text-gray-300 leading-relaxed bg-gray-50 dark:bg-gray-950 p-5 rounded-2xl border border-gray-150 dark:border-gray-850 max-h-[50vh]">
              <span className="font-bold block text-gray-400 text-xxs uppercase tracking-wider mb-2">Context excerpt:</span>
              <p className="whitespace-pre-wrap">
                {activeChunk.text}
              </p>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-850 flex justify-end flex-shrink-0">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-6 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-750 text-gray-700 dark:text-gray-350 font-semibold text-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
