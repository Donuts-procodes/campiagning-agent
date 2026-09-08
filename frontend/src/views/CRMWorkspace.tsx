import { useEffect, useState } from 'react';
import {
  getCampaignLeads,
  addCampaignLead,
  updateCampaignLeadStatus,
  seedCampaignLeads,
  type CampaignLead
} from '../services/api';
import { UserPlusIcon, ArrowPathIcon, EnvelopeIcon } from '@heroicons/react/24/solid';

interface CRMWorkspaceProps {
  threadId: string;
}

export default function CRMWorkspace({ threadId }: CRMWorkspaceProps) {
  const [leads, setLeads] = useState<CampaignLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  
  const [newLead, setNewLead] = useState({
    name: '',
    company_name: '',
    email: '',
    title: '',
    linkedin_url: '',
    status: 'enrolled'
  });

  const loadLeads = async () => {
    setLoading(true);
    try {
      const data = await getCampaignLeads(threadId);
      setLeads(data);
    } catch (err) {
      console.error("Failed to load campaign leads:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads();
  }, [threadId]);

  const handleStatusChange = async (contactId: string, newStatus: string) => {
    try {
      await updateCampaignLeadStatus(threadId, contactId, newStatus);
      setLeads(prev => prev.map(l => l.contact_id === contactId ? { ...l, status: newStatus as any } : l));
    } catch (err) {
      console.error("Failed to update status:", err);
      alert("Failed to update status");
    }
  };

  const handleAddLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLead.name || !newLead.email || !newLead.company_name) {
      alert("Name, Email, and Company are required");
      return;
    }
    try {
      const created = await addCampaignLead(threadId, newLead);
      setLeads(prev => [created, ...prev]);
      setShowAddModal(false);
      setNewLead({ name: '', company_name: '', email: '', title: '', linkedin_url: '', status: 'enrolled' });
    } catch (err) {
      console.error("Failed to add lead:", err);
      alert("Failed to add lead");
    }
  };

  const handleSeedLeads = async () => {
    try {
      setLoading(true);
      const data = await seedCampaignLeads(threadId);
      setLeads(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const totalEnrolled = leads.length;
  const activeInSequence = leads.filter(l => l.status === 'sequence_active').length;
  const repliedCount = leads.filter(l => l.status === 'replied').length;
  const meetingCount = leads.filter(l => l.status === 'meeting_booked').length;

  return (
    <div className="space-y-6">
      {/* 1. Header & Scoping */}
      <div className="neo-card bg-[var(--neo-accent)] flex flex-wrap justify-between items-center gap-4">
        <div>
          <span className="text-xs font-black uppercase tracking-widest bg-black text-white px-2 py-1">
            CAMPAIGN-SCOPED CRM
          </span>
          <h2 className="neo-header mt-2 mb-1">Enrolled Leads & Pipeline</h2>
          <p className="font-bold text-sm text-gray-800">
            Managing contacts for Campaign Thread <span className="font-mono bg-white px-2 py-0.5 border border-black">{threadId.substring(0, 8)}</span>
          </p>
        </div>

        <div className="flex space-x-3">
          <button 
            onClick={loadLeads}
            className="neo-button bg-white flex items-center text-sm"
            title="Refresh Leads"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1"/> Refresh
          </button>
          <button 
            onClick={() => setShowAddModal(true)}
            className="neo-button bg-black text-white flex items-center text-sm"
          >
            <UserPlusIcon className="h-4 w-4 mr-1 text-white"/> + Enroll Lead
          </button>
        </div>
      </div>

      {/* 2. Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="neo-card text-center bg-white">
          <p className="text-xs uppercase font-bold text-gray-500">Enrolled Contacts</p>
          <p className="text-3xl font-black mt-1 text-gray-900">{totalEnrolled}</p>
        </div>
        <div className="neo-card text-center bg-blue-50 border-blue-300">
          <p className="text-xs uppercase font-bold text-blue-700">Active Sequence</p>
          <p className="text-3xl font-black mt-1 text-blue-900">{activeInSequence}</p>
        </div>
        <div className="neo-card text-center bg-purple-50 border-purple-300">
          <p className="text-xs uppercase font-bold text-purple-700">Replied / Engaged</p>
          <p className="text-3xl font-black mt-1 text-purple-900">{repliedCount}</p>
        </div>
        <div className="neo-card text-center bg-green-50 border-green-300">
          <p className="text-xs uppercase font-bold text-green-700">Meetings Booked</p>
          <p className="text-3xl font-black mt-1 text-green-900">{meetingCount}</p>
        </div>
      </div>

      {/* 3. Add Lead Modal */}
      {showAddModal && (
        <div className="neo-card bg-[#fdfbf7] border-4 border-black p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-black text-lg">Enroll New Contact into this Campaign</h3>
            <button onClick={() => setShowAddModal(false)} className="font-black text-xl px-2">&times;</button>
          </div>
          <form onSubmit={handleAddLead} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="neo-label text-xs">Full Name *</label>
              <input 
                required 
                className="neo-input" 
                value={newLead.name} 
                onChange={e => setNewLead({ ...newLead, name: e.target.value })} 
                placeholder="Sarah Connor" 
              />
            </div>
            <div>
              <label className="neo-label text-xs">Company Name *</label>
              <input 
                required 
                className="neo-input" 
                value={newLead.company_name} 
                onChange={e => setNewLead({ ...newLead, company_name: e.target.value })} 
                placeholder="Cyberdyne Systems" 
              />
            </div>
            <div>
              <label className="neo-label text-xs">Business Email *</label>
              <input 
                required 
                type="email" 
                className="neo-input" 
                value={newLead.email} 
                onChange={e => setNewLead({ ...newLead, email: e.target.value })} 
                placeholder="sarah@cyberdyne.com" 
              />
            </div>
            <div>
              <label className="neo-label text-xs">Job Title</label>
              <input 
                className="neo-input" 
                value={newLead.title} 
                onChange={e => setNewLead({ ...newLead, title: e.target.value })} 
                placeholder="VP Infrastructure" 
              />
            </div>
            <div>
              <label className="neo-label text-xs">LinkedIn URL</label>
              <input 
                className="neo-input" 
                value={newLead.linkedin_url} 
                onChange={e => setNewLead({ ...newLead, linkedin_url: e.target.value })} 
                placeholder="https://linkedin.com/in/sarah" 
              />
            </div>
            <div>
              <label className="neo-label text-xs">Initial Status</label>
              <select 
                className="neo-input" 
                value={newLead.status} 
                onChange={e => setNewLead({ ...newLead, status: e.target.value })}
              >
                <option value="enrolled">Enrolled</option>
                <option value="sequence_active">Sequence Active</option>
                <option value="replied">Replied</option>
                <option value="meeting_booked">Meeting Booked</option>
              </select>
            </div>
            <div className="md:col-span-3 flex justify-end space-x-3 mt-2">
              <button type="button" onClick={() => setShowAddModal(false)} className="neo-button bg-white">Cancel</button>
              <button type="submit" className="neo-button neo-button-primary">Enroll Contact &rarr;</button>
            </div>
          </form>
        </div>
      )}

      {/* 4. Leads Table */}
      <div className="neo-card bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-black text-base uppercase tracking-wider">Campaign Contact Roster</h3>
          {leads.length === 0 && (
            <button onClick={handleSeedLeads} className="neo-button bg-blue-50 text-blue-700 text-xs">
              + Seed 5 Sample Prospects
            </button>
          )}
        </div>

        {loading ? (
          <div className="py-12 text-center font-bold animate-pulse text-gray-500">
            LOADING CAMPAIGN LEADS...
          </div>
        ) : leads.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-gray-500 mb-4">No contacts enrolled in this campaign yet.</p>
            <button onClick={handleSeedLeads} className="neo-button neo-button-primary text-sm">
              Populate Sample ICP Prospects
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-4 border-black bg-white">
              <thead className="bg-[#f0f0f0] border-b-4 border-black">
                <tr>
                  <th className="p-3 font-black uppercase text-xs border-r-4 border-black">Contact</th>
                  <th className="p-3 font-black uppercase text-xs border-r-4 border-black">Company</th>
                  <th className="p-3 font-black uppercase text-xs border-r-4 border-black">Direct Channels</th>
                  <th className="p-3 font-black uppercase text-xs border-r-4 border-black">Strategy Variant</th>
                  <th className="p-3 font-black uppercase text-xs">Outreach Stage</th>
                </tr>
              </thead>
              <tbody>
                {leads.map(lead => (
                  <tr key={lead.contact_id} className="border-b-4 border-black last:border-b-0 hover:bg-gray-50 transition-colors">
                    <td className="p-3 border-r-4 border-black">
                      <p className="font-bold text-gray-900">{lead.name}</p>
                      <p className="text-xs text-gray-500">{lead.title}</p>
                    </td>
                    <td className="p-3 border-r-4 border-black font-semibold text-gray-800">
                      {lead.company_name}
                    </td>
                    <td className="p-3 border-r-4 border-black space-y-1">
                      <div className="flex items-center text-xs text-blue-600">
                        <EnvelopeIcon className="h-3 w-3 mr-1 text-gray-400" />
                        <a href={`mailto:${lead.email}`} className="hover:underline">{lead.email}</a>
                      </div>
                      {lead.linkedin_url && (
                        <div className="text-xs text-gray-500 truncate max-w-[160px]">
                          <a href={lead.linkedin_url} target="_blank" rel="noreferrer" className="hover:underline text-blue-700">
                            LinkedIn Profile &rarr;
                          </a>
                        </div>
                      )}
                    </td>
                    <td className="p-3 border-r-4 border-black font-mono text-xs">
                      <span className="bg-gray-100 px-2 py-1 rounded border border-gray-300">
                        {lead.variant_id}
                      </span>
                    </td>
                    <td className="p-3">
                      <select
                        value={lead.status}
                        onChange={e => handleStatusChange(lead.contact_id, e.target.value)}
                        className={`text-xs font-black uppercase px-2 py-1 border-2 border-black rounded cursor-pointer ${
                          lead.status === 'meeting_booked'
                            ? 'bg-green-100 text-green-800 border-green-800'
                            : lead.status === 'replied'
                            ? 'bg-purple-100 text-purple-800 border-purple-800'
                            : lead.status === 'sequence_active'
                            ? 'bg-blue-100 text-blue-800 border-blue-800'
                            : lead.status === 'unsubscribed'
                            ? 'bg-red-100 text-red-800 border-red-800'
                            : 'bg-white text-gray-800'
                        }`}
                      >
                        <option value="enrolled">Enrolled</option>
                        <option value="sequence_active">Sequence Active</option>
                        <option value="replied">Replied / Engaged</option>
                        <option value="meeting_booked">Meeting Booked</option>
                        <option value="unsubscribed">Unsubscribed</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
