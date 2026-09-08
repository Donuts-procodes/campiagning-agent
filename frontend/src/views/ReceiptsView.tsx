import { useEffect, useState } from 'react';
import { getCampaignReceipts, type ExecutionReceipt } from '../services/api';
import { EnvelopeIcon, LinkIcon } from '@heroicons/react/24/outline';

export default function ReceiptsView({ threadId }: { threadId: string }) {
  const [receipts, setReceipts] = useState<ExecutionReceipt[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReceipts = async () => {
      try {
        const data = await getCampaignReceipts(threadId);
        setReceipts(data.receipts || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchReceipts();
  }, [threadId]);

  if (loading) return <div className="neo-card font-bold animate-pulse">LOADING RECEIPTS...</div>;
  if (!receipts.length) return <div className="neo-card font-bold">NO DISPATCH RECEIPTS YET.</div>;

  return (
    <div className="neo-card bg-white">
      <h2 className="neo-header border-b-4 border-black pb-2 mb-6">Dispatch Receipts</h2>
      <div className="space-y-6">
        {receipts.map((r, i) => (
          <div key={i} className="neo-container flex bg-[#fdfbf7]">
            <div className={`p-6 border-r-4 border-black flex flex-col justify-center items-center ${r.channel === 'email' ? 'bg-[var(--neo-secondary)]' : 'bg-[var(--neo-primary)]'}`}>
               {r.channel === 'email' ? <EnvelopeIcon className="h-10 w-10 text-black mb-2" /> : <LinkIcon className="h-10 w-10 text-black mb-2" />}
               <span className="font-black uppercase tracking-tighter">{r.channel}</span>
            </div>
            <div className="p-6 flex-grow flex flex-col justify-between">
               <div>
                  <p className="font-mono text-sm mb-1 bg-black text-white inline-block px-1">JOB ID: {r.job_id}</p>
                  <p className="font-bold text-lg">{r.response_payload?.message || 'Outreach Dispatched'}</p>
               </div>
               <div className="mt-4 flex space-x-6">
                  <div className="border-2 border-black px-2 py-1 bg-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                     <span className="text-xs uppercase font-bold mr-2">Contacts Enrolled:</span>
                     <span className="font-black">{r.contacts_enrolled}</span>
                  </div>
                  <div className="border-2 border-black px-2 py-1 bg-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                     <span className="text-xs uppercase font-bold mr-2">Status:</span>
                     <span className="font-black text-green-600 uppercase">{r.status}</span>
                  </div>
               </div>
               {r.dispatched_at && <p className="text-xs font-mono mt-4 border-t-2 border-dashed border-gray-400 pt-2">TIMESTAMP: {new Date(r.dispatched_at).toLocaleString()}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
