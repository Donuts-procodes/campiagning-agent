import { useCallback, useEffect, useState } from 'react';
import { approveCampaign, getCampaignState, type OutreachVariant, type CampaignState } from '../services/api';
import { CheckCircleIcon, PaperAirplaneIcon, DocumentMagnifyingGlassIcon } from '@heroicons/react/24/solid';

export default function ApprovalPanel({ threadId, onNavigate }: { threadId: string, onNavigate: (view: string, threadId: string) => void }) {
  const [state, setState] = useState<CampaignState | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState<string | null>(null);

  const loadState = useCallback(async () => {
    try {
      const data = await getCampaignState(threadId);
      setState(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [threadId]);

  useEffect(() => {
    loadState();
    const interval = setInterval(loadState, 3000);
    return () => clearInterval(interval);
  }, [loadState]);

  if (loading) return <div className="neo-card animate-pulse font-bold">LOADING STATE...</div>;
  if (!state || !state.strategy?.strategy_variants?.length) {
    return (
      <div className="neo-card bg-[var(--neo-bg)]">
        <h2 className="neo-header">WAITING FOR AGENT</h2>
        <p className="font-mono">The agent is currently enriching ICPs and building sequences. Please wait.</p>
      </div>
    );
  }

  const variants: OutreachVariant[] = state.strategy.strategy_variants;
  const isApproved = state.hitl?.review_status === 'approved';

  const handleApprove = async (variantId: string) => {
    setApproving(variantId);
    try {
      await approveCampaign(threadId, variantId);
      onNavigate('pipeline', threadId);
    } catch (err) {
      console.error(err);
      alert('Failed to approve strategy');
    } finally {
      setApproving(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="neo-card bg-[var(--neo-accent)] flex justify-between items-center">
        <div>
           <h2 className="neo-header mb-1">Human-in-the-Loop Review</h2>
           <p className="font-bold">Select an Outreach Cadence Strategy for Execution.</p>
        </div>
        {isApproved && <span className="neo-button bg-white pointer-events-none uppercase">Strategy Approved</span>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {variants.map((v) => {
          const bundle = state.creatives?.variant_creatives?.[v.variant_id];
          return (
            <div key={v.variant_id} className="neo-container flex flex-col bg-white">
              <div className="p-6 border-b-4 border-black bg-[var(--neo-primary)]">
                 <h3 className="text-2xl font-black uppercase truncate" title={v.variant_name}>{v.variant_name}</h3>
                 <p className="font-bold text-sm mt-2">{v.description}</p>
              </div>
              
              <div className="p-6 flex-grow space-y-4">
                <div className="neo-card-pink p-4 shadow-none">
                  <span className="neo-label">Messaging Angle</span>
                  <p className="font-mono text-sm">{v.messaging_angle}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="border-4 border-black p-4 text-center bg-[#f0f0f0]">
                    <span className="neo-label text-xs">Required Contacts</span>
                    <span className="text-3xl font-black">{v.required_contact_volume}</span>
                  </div>
                  <div className="border-4 border-black p-4 text-center bg-[var(--neo-accent)]">
                    <span className="neo-label text-xs">Est. Reply Rate</span>
                    <span className="text-3xl font-black">{(v.estimated_reply_rate * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {bundle?.email_sequences && (
                  <div className="border-4 border-black p-4 bg-white">
                    <span className="neo-label flex items-center"><DocumentMagnifyingGlassIcon className="h-4 w-4 mr-1"/> Generated Sequence Examples</span>
                    <div className="mt-2 space-y-2">
                       {bundle.email_sequences.map((seq: any, idx: number) => (
                         <div key={idx} className="bg-gray-100 p-2 border-l-4 border-black text-xs font-mono">
                           <strong>Subject:</strong> {seq.subject_line}
                         </div>
                       ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="p-6 border-t-4 border-black bg-[#f0f0f0]">
                <button
                  onClick={() => handleApprove(v.variant_id)}
                  disabled={isApproved || approving === v.variant_id}
                  className={`w-full text-xl ${isApproved && state.hitl?.approved_variant_id === v.variant_id ? 'neo-button neo-button-primary' : 'neo-button bg-white'}`}
                >
                  {isApproved && state.hitl?.approved_variant_id === v.variant_id 
                    ? <><CheckCircleIcon className="inline h-6 w-6 mr-2" /> ACTIVE STRATEGY</> 
                    : <><PaperAirplaneIcon className="inline h-5 w-5 mr-2" /> APPROVE & DISPATCH</>}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
