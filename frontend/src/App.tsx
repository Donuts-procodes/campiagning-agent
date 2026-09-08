import { useState } from 'react';
import CampaignCreator from './views/CampaignCreator';
import Dashboard from './views/Dashboard';
import PipelineViewer from './views/PipelineViewer';
import ApprovalPanel from './views/ApprovalPanel';
import ReceiptsView from './views/ReceiptsView';
import CRMWorkspace from './views/CRMWorkspace';
import { PlayIcon, CheckCircleIcon, DocumentTextIcon, UserGroupIcon } from '@heroicons/react/24/solid';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [activeThread, setActiveThread] = useState<string | null>(() => {
    return localStorage.getItem('last_active_thread') || null;
  });

  const handleNavigate = (view: string, threadId?: string) => {
    setCurrentView(view);
    if (threadId) {
      setActiveThread(threadId);
      localStorage.setItem('last_active_thread', threadId);
    }
  };

  return (
    <div className="min-h-screen p-8 max-w-6xl mx-auto">
      <header className="mb-8 flex justify-between items-end border-b border-gray-200 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight px-2 inline-block">
            B2B Outreach Agent
          </h1>
          <p className="text-sm font-medium text-gray-500 mt-2 max-w-md px-2">
            AI SDR: Prospecting, Sequencing, and Dispatch
          </p>
        </div>
        <nav className="flex space-x-4">
          <button 
            onClick={() => handleNavigate('dashboard')} 
            className={`neo-button ${currentView === 'dashboard' ? 'bg-gray-100' : 'bg-white'}`}
          >
            Dashboard
          </button>
          <button 
            onClick={() => handleNavigate('create')}
            className={`neo-button ${currentView === 'create' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-white text-gray-700'}`}
          >
            + New Campaign
          </button>
          <button 
            onClick={() => handleNavigate('crm', activeThread || undefined)} 
            className={`neo-button ${currentView === 'crm' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-white text-gray-700'}`}
          >
            Campaign CRM
          </button>
        </nav>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-4 gap-8">
        
        {/* Sidebar Navigation */}
        <div className="md:col-span-1 space-y-6">
           <div className="neo-card">
              <h2 className="neo-header text-lg border-b border-gray-200 pb-2 mb-4">Active Thread</h2>
              {activeThread ? (
                <div className="space-y-3 font-medium text-sm">
                  <p className="bg-gray-50 border border-gray-200 p-2 truncate text-gray-500 rounded-md" title={activeThread}>
                    ID: {activeThread.substring(0,8)}...
                  </p>
                  
                  <button onClick={() => handleNavigate('pipeline', activeThread)} className={`w-full neo-button text-left flex items-center ${currentView === 'pipeline' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-white'}`}>
                    <PlayIcon className="h-4 w-4 mr-2"/> Pipeline
                  </button>
                  <button onClick={() => handleNavigate('approval', activeThread)} className={`w-full neo-button text-left flex items-center ${currentView === 'approval' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-white'}`}>
                    <CheckCircleIcon className="h-4 w-4 mr-2 text-green-500"/> Approvals
                  </button>
                  <button onClick={() => handleNavigate('crm', activeThread)} className={`w-full neo-button text-left flex items-center ${currentView === 'crm' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-white'}`}>
                    <UserGroupIcon className="h-4 w-4 mr-2 text-purple-600"/> Campaign Leads
                  </button>
                  <button onClick={() => handleNavigate('receipts', activeThread)} className={`w-full neo-button text-left flex items-center ${currentView === 'receipts' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-white'}`}>
                    <DocumentTextIcon className="h-4 w-4 mr-2 text-gray-400"/> Receipts
                  </button>
                </div>
              ) : (
                <p className="font-medium text-gray-500 py-4 text-center">No active campaign selected.</p>
              )}
           </div>
        </div>

        {/* Main Content Area */}
        <div className="md:col-span-3">
          {currentView === 'dashboard' && <Dashboard onNavigate={handleNavigate} />}
          {currentView === 'create' && <CampaignCreator onNavigate={handleNavigate} />}
          {currentView === 'pipeline' && (
            activeThread ? (
              <PipelineViewer threadId={activeThread} onNavigate={handleNavigate} />
            ) : (
              <div className="neo-card text-center py-12">
                <h2 className="neo-header text-xl mb-2">No Active Campaign Selected</h2>
                <p className="text-gray-500 mb-6">Create a campaign or select a recent sequence from the dashboard.</p>
                <button onClick={() => handleNavigate('create')} className="neo-button bg-blue-50 text-blue-700 border-blue-200">
                  + Create Campaign
                </button>
              </div>
            )
          )}
          {currentView === 'approval' && activeThread && <ApprovalPanel threadId={activeThread} onNavigate={handleNavigate} />}
          {currentView === 'receipts' && activeThread && <ReceiptsView threadId={activeThread} />}
          {currentView === 'crm' && (
            activeThread ? (
              <CRMWorkspace threadId={activeThread} />
            ) : (
              <div className="neo-card text-center py-12">
                <h2 className="neo-header text-xl mb-2">No Campaign Selected for CRM</h2>
                <p className="text-gray-500 mb-6">Each campaign has its own dedicated CRM. Select an active campaign or create one to manage enrolled leads.</p>
                <button onClick={() => handleNavigate('create')} className="neo-button bg-blue-50 text-blue-700 border-blue-200">
                  + Create Campaign
                </button>
              </div>
            )
          )}
        </div>
      </main>
    </div>
  );
}
