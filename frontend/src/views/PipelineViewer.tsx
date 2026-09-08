import { useEffect, useState } from 'react';
import { getCampaignState, type CampaignState } from '../services/api';

const PIPELINE_NODES = [
  { id: 'icp_enrichment', name: 'ICP Enrichment', pod: 'Analysis Pod' },
  { id: 'goal_decomposition', name: 'Goal Decomposition', pod: 'Strategy Pod' },
  { id: 'channel_cadence', name: 'Cadence Planner', pod: 'Strategy Pod' },
  { id: 'strategy_generator', name: 'Strategy Generator', pod: 'Strategy Pod' },
  { id: 'email_generator', name: 'Email Sequence Gen', pod: 'Creation Pod' },
  { id: 'social_generator', name: 'LinkedIn Script Gen', pod: 'Creation Pod' },
  { id: 'compliance_checker', name: 'Compliance Check', pod: 'Verification Pod' },
  { id: 'hitl_approval_node', name: 'Human Approval', pod: 'Human-in-the-Loop' },
  { id: 'outreach_dispatcher', name: 'Outreach Dispatcher', pod: 'Execution Pod' }
];

export default function PipelineViewer({ threadId, onNavigate }: { threadId: string, onNavigate: (view: string, threadId: string) => void }) {
  const [state, setState] = useState<CampaignState | null>(null);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const data = await getCampaignState(threadId);
        setState(data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchState();
    const interval = setInterval(fetchState, 2000);
    return () => clearInterval(interval);
  }, [threadId]);

  if (!state) return <div className="neo-card font-bold animate-pulse">LOADING PIPELINE...</div>;

  const execution = state.execution?.receipts;
  const hasExecution = Boolean(execution) || state.current_node === 'outreach_dispatcher';

  return (
    <div className="neo-card bg-[var(--neo-bg)]">
      <div className="flex justify-between items-center mb-6 border-b-4 border-black pb-4">
         <h2 className="neo-header mb-0">Live Agent Pipeline</h2>
         <span className="neo-label bg-white border-4 border-black px-3 py-1 bg-[var(--neo-primary)]">Thread: {threadId.substring(0,8)}</span>
      </div>

      <div className="space-y-4">
        {PIPELINE_NODES.map((node, idx) => {
          const isActive = state.current_node === node.id;
          const isApproval = node.id === 'hitl_approval_node';
          const needsApproval = isApproval && isActive && state.hitl?.review_status === 'pending';

          return (
            <div 
              key={node.id} 
              className={`border-4 border-black p-4 flex items-center justify-between transition-all ${isActive ? 'bg-[var(--neo-accent)] shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] -translate-y-1 scale-105' : 'bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] opacity-70'} ${needsApproval ? 'border-dashed border-pink-500 bg-pink-100' : ''}`}
            >
              <div className="flex items-center space-x-4">
                <div className={`w-8 h-8 rounded-full border-4 border-black flex items-center justify-center font-black ${isActive ? 'bg-white' : 'bg-[#e5e5e5]'}`}>
                  {idx + 1}
                </div>
                <div>
                  <h3 className="font-black uppercase text-lg">{node.name}</h3>
                  <p className="font-bold text-xs uppercase opacity-80">{node.pod}</p>
                </div>
              </div>
              
              <div>
                {isActive && !isApproval && <span className="font-black animate-pulse uppercase">Processing...</span>}
                {needsApproval && (
                  <button onClick={() => onNavigate('approval', threadId)} className="neo-button neo-button-secondary py-1 text-sm">
                    REVIEW REQUIRED
                  </button>
                )}
                {hasExecution && node.id === 'outreach_dispatcher' && (
                  <button onClick={() => onNavigate('receipts', threadId)} className="neo-button bg-[var(--neo-primary)] py-1 text-sm">
                    VIEW RECEIPTS
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
