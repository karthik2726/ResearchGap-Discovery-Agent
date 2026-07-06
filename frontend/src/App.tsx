import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Upload, LayoutDashboard, FileText, Search, Target, ShieldCheck, PenTool, Lightbulb, BrainCircuit, Map } from 'lucide-react';
import DashboardHome from './pages/DashboardHome';
import UploadPapers from './pages/UploadPapers';
import SearchPapers from './pages/SearchPapers';
import ResearchLandscape from './pages/ResearchLandscape';
import GapAnalysis from './pages/GapAnalysis';
import IdeaGenerator from './pages/IdeaGenerator';
import QualityAudit from './pages/QualityAudit';
import WritingQuality from './pages/WritingQuality';
import FinalReport from './pages/FinalReport';

function App() {
  const [isDark, setIsDark] = useState(true);

  return (
    <Router>
      <div className={`min-h-screen ${isDark ? 'dark bg-gray-950 text-white' : 'bg-gray-50 text-gray-900'} font-sans`}>
        {/* Sidebar */}
        <aside className="fixed top-0 left-0 h-screen w-64 border-r border-gray-800 bg-gray-900/50 backdrop-blur-xl">
          <div className="p-6">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent flex items-center gap-2">
              <BrainCircuit className="w-8 h-8 text-blue-400" />
              ResearchIQ
            </h1>
            <p className="text-xs text-gray-400 mt-2 font-medium tracking-wide uppercase">Discover Gaps. Validate Research.</p>
          </div>
          
          <nav className="mt-6 px-4 space-y-2">
            <Link to="/" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
            </Link>
            <Link to="/upload" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <Upload size={18} />
              <span>Upload Papers</span>
            </Link>
            <Link to="/landscape" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <Map size={18} />
              <span>Research Landscape</span>
            </Link>
            <Link to="/gaps" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <Target size={18} />
              <span>Gap Analysis</span>
            </Link>
            <Link to="/audit" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <ShieldCheck size={18} />
              <span>Quality Audit</span>
            </Link>
            <Link to="/ideas" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <Lightbulb size={18} />
              <span>Idea Generator</span>
            </Link>
            <Link to="/writing" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <PenTool size={18} />
              <span>Writing Quality</span>
            </Link>
            <Link to="/search" className="flex items-center gap-3 px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all text-sm">
              <Search size={18} />
              <span>Semantic Search</span>
            </Link>
            <Link to="/report" className="flex items-center gap-3 px-4 py-2 rounded-lg text-blue-400 hover:bg-blue-500/10 hover:text-blue-300 transition-all text-sm font-semibold mt-4">
              <FileText size={18} />
              <span>Master Report</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="ml-64 p-8">
          <div className="max-w-6xl mx-auto">
            <header className="flex justify-between items-center mb-12">
              <h2 className="text-3xl font-semibold tracking-tight">Intelligence Center</h2>
              <button 
                onClick={() => setIsDark(!isDark)}
                className="px-4 py-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
              >
                {isDark ? 'Light Mode' : 'Dark Mode'}
              </button>
            </header>
            
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
              <Routes>
                <Route path="/" element={<DashboardHome />} />
                <Route path="/upload" element={<UploadPapers />} />
                <Route path="/landscape" element={<ResearchLandscape />} />
                <Route path="/gaps" element={<GapAnalysis />} />
                <Route path="/audit" element={<QualityAudit />} />
                <Route path="/ideas" element={<IdeaGenerator />} />
                <Route path="/writing" element={<WritingQuality />} />
                <Route path="/search" element={<SearchPapers />} />
                <Route path="/report" element={<FinalReport />} />
              </Routes>
            </div>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
