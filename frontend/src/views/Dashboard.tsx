import { useEffect, useState } from 'react';
import { PlayIcon } from '@heroicons/react/24/solid';

interface DashboardProps {
  onNavigate: (view: string, threadId?: string) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [threads, setThreads] = useState<string[]>([]);
  
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('recent_campaign_threads') || '[]');
      setThreads(saved);
    } catch {
      setThreads([]);
    }
  }, []);

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="neo-card text-center">
          <h3 className="neo-label text-gray-500">Total Outbound Contacts</h3>
          <p className="text-4xl font-bold mt-2 text-gray-900">0</p>
        </div>
        <div className="neo-card text-center">
          <h3 className="neo-label text-gray-500">Meetings Booked (YTD)</h3>
          <p className="text-4xl font-bold mt-2 text-gray-900">0</p>
        </div>
        <div className="neo-card text-center">
          <h3 className="neo-label text-gray-500">Avg Reply Rate</h3>
          <p className="text-4xl font-bold mt-2 text-gray-900">0.0%</p>
        </div>
      </div>

      <div className="neo-card">
        <h2 className="neo-header border-b border-gray-200 pb-2 mb-4">Recent Sequences</h2>
        {threads.length === 0 ? (
          <p className="text-gray-500 py-4 text-center">No active sequences found.</p>
        ) : (
          <div className="space-y-4">
            {threads.map(threadId => (
              <div key={threadId} className="flex justify-between items-center border border-gray-200 rounded-md p-4 bg-gray-50 hover:bg-white transition-colors">
                <div>
                   <p className="font-semibold text-lg text-gray-900">Sequence ID: {threadId.substring(0,8)}</p>
                   <p className="text-sm text-gray-500 mt-1">Last active: Just now</p>
                </div>
                <button 
                  onClick={() => onNavigate('pipeline', threadId)}
                  className="neo-button flex items-center"
                >
                  <PlayIcon className="h-4 w-4 mr-2" /> Resume
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
