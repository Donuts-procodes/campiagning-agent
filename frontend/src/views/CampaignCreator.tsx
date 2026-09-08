import { useState } from 'react';
import { createCampaign, type UserInput, type CampaignLead } from '../services/api';

interface CampaignCreatorProps {
  onNavigate: (view: string, threadId?: string) => void;
}

export default function CampaignCreator({ onNavigate }: CampaignCreatorProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<UserInput>({
    campaign_name: '',
    company_name: '',
    product_service: '',
    value_proposition: '',
    target_icp: '',
    competitors: [],
    campaign_type: 'multi_channel',
    target_meetings: 10,
    duration_days: 30,
    start_date: new Date().toISOString().split('T')[0],
    business_okrs: [],
    content_assets: [],
    success_metrics: [],
    credentials: {},
    brand_tone: 'direct_consultative',
    primary_cta: 'soft_interest',
    target_geography: 'North America',
    pricing_tier: 'mid_market',
  });
  
  const [budgetStr, setBudgetStr] = useState('');
  const [contentStr, setContentStr] = useState('');
  const [caseStudiesStr, setCaseStudiesStr] = useState('');
  const [differentiatorsStr, setDifferentiatorsStr] = useState('');
  const [negativeConstraintsStr, setNegativeConstraintsStr] = useState('');
  const [senderName, setSenderName] = useState('');
  const [senderTitle, setSenderTitle] = useState('');
  const [okrStr, setOkrStr] = useState('');
  const [linkedinApi, setLinkedinApi] = useState('');
  const [emailApi, setEmailApi] = useState('');
  
  // Dual-Mode Prospect Sourcing Pipeline
  const [sourcingMode, setSourcingMode] = useState<'ai_sourcing' | 'csv_upload'>('ai_sourcing');
  const [csvContacts, setCsvContacts] = useState<Partial<CampaignLead>[]>([]);
  const [csvFileName, setCsvFileName] = useState('');
  const [csvParseError, setCsvParseError] = useState('');

  const [loading, setLoading] = useState(false);

  const handleCsvFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvFileName(file.name);
    setCsvParseError('');

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const text = evt.target?.result as string;
        const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
        if (lines.length < 2) {
          setCsvParseError("CSV file is empty or missing data rows");
          return;
        }

        const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/['"]/g, ''));
        const nameIdx = headers.findIndex(h => h.includes('name') || h.includes('contact') || h.includes('person'));
        const emailIdx = headers.findIndex(h => h.includes('email') || h.includes('mail'));
        const companyIdx = headers.findIndex(h => h.includes('company') || h.includes('org') || h.includes('corp'));
        const titleIdx = headers.findIndex(h => h.includes('title') || h.includes('role') || h.includes('position'));
        const linkedinIdx = headers.findIndex(h => h.includes('linkedin') || h.includes('profile') || h.includes('social'));

        if (nameIdx === -1 || emailIdx === -1 || companyIdx === -1) {
          setCsvParseError("CSV must include columns for Name, Email, and Company");
          return;
        }

        const parsed: Partial<CampaignLead>[] = [];
        for (let i = 1; i < lines.length; i++) {
          const row = lines[i].split(',').map(c => c.trim().replace(/^["']|["']$/g, ''));
          if (row.length <= Math.max(nameIdx, emailIdx, companyIdx)) continue;
          const name = row[nameIdx] || '';
          const email = row[emailIdx] || '';
          const company_name = row[companyIdx] || '';
          const title = titleIdx !== -1 ? row[titleIdx] || '' : '';
          const linkedin_url = linkedinIdx !== -1 ? row[linkedinIdx] || '' : '';

          if (name && email && company_name) {
            parsed.push({
              name,
              email,
              company_name,
              title,
              linkedin_url,
              status: 'enrolled'
            });
          }
        }

        if (parsed.length === 0) {
          setCsvParseError("No valid contact rows could be parsed.");
          return;
        }

        setCsvContacts(parsed);
      } catch (err: any) {
        setCsvParseError("Failed to parse CSV: " + (err.message || String(err)));
      }
    };
    reader.readAsText(file);
  };

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault();
    setStep(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // Process string inputs into the complex types
    const finalData = { ...formData };
    
    if (budgetStr) finalData.budget = parseFloat(budgetStr);
    if (contentStr) finalData.content_assets = contentStr.split(',').map(s => s.trim()).filter(Boolean);
    if (caseStudiesStr) finalData.case_studies = caseStudiesStr.split('\n').map(s => s.trim()).filter(Boolean);
    if (differentiatorsStr) finalData.differentiators = differentiatorsStr.split(',').map(s => s.trim()).filter(Boolean);
    if (negativeConstraintsStr) finalData.negative_constraints = negativeConstraintsStr.split(',').map(s => s.trim()).filter(Boolean);
    
    if (senderName || senderTitle) {
      finalData.sender_profile = { name: senderName, title: senderTitle };
    }

    if (okrStr) {
      finalData.business_okrs = okrStr.split(',').map(s => ({ objective: s.trim(), key_results: [] })).filter(o => o.objective);
    }
    
    const creds: Record<string, string> = {};
    if (linkedinApi) creds['linkedin_api_key'] = linkedinApi;
    if (emailApi) creds['email_provider_key'] = emailApi;
    finalData.credentials = creds;

    // Prospect Sourcing Mode & Payload
    finalData.prospect_sourcing_mode = sourcingMode;
    finalData.initial_contacts = sourcingMode === 'csv_upload' ? csvContacts : [];

    try {
      const res = await createCampaign(finalData);
      const thread_id = res.thread_id;
      if (thread_id) {
        try {
          const stored = JSON.parse(localStorage.getItem('recent_campaign_threads') || '[]');
          if (!stored.includes(thread_id)) {
            localStorage.setItem('recent_campaign_threads', JSON.stringify([thread_id, ...stored]));
          }
          localStorage.setItem('last_active_thread', thread_id);
        } catch (e) {
          console.warn(e);
        }
        onNavigate('pipeline', thread_id);
      } else {
        throw new Error("No thread ID returned from server");
      }
    } catch (err: any) {
      console.error(err);
      alert(`Failed to create campaign: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  if (step === 1) {
    return (
      <div className="neo-card">
        <h2 className="neo-header border-b-4 border-black pb-2 mb-6 inline-block bg-[var(--neo-accent)] px-2 -rotate-1">Step 1: Campaign Basics</h2>
        <form onSubmit={handleNextStep} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="neo-card-pink">
               <label className="neo-label">Campaign Name</label>
               <input required className="neo-input" value={formData.campaign_name} onChange={e => setFormData({...formData, campaign_name: e.target.value})} placeholder="Q4 SaaS Leads" />
            </div>

            <div className="neo-card-purple">
               <label className="neo-label">Company Name</label>
               <input required className="neo-input" value={formData.company_name} onChange={e => setFormData({...formData, company_name: e.target.value})} placeholder="Acme Corp" />
            </div>

            <div className="md:col-span-2 neo-container p-6 bg-white">
               <label className="neo-label">Product/Service</label>
               <input required className="neo-input" value={formData.product_service} onChange={e => setFormData({...formData, product_service: e.target.value})} placeholder="AI Customer Support Widget" />
               
               <label className="neo-label mt-4">Value Proposition</label>
               <textarea required className="neo-input h-24" value={formData.value_proposition} onChange={e => setFormData({...formData, value_proposition: e.target.value})} placeholder="Reduces ticket resolution time by 40%..." />
            </div>

            <div className="md:col-span-2 neo-container p-6 bg-[var(--neo-primary)]">
               <label className="neo-label">Target ICP</label>
               <textarea required className="neo-input h-24" value={formData.target_icp} onChange={e => setFormData({...formData, target_icp: e.target.value})} placeholder="VP of Customer Success at Series B tech companies..." />
            </div>

            <div className="neo-card-pink">
               <label className="neo-label">Outreach Type</label>
               <select className="neo-input" value={formData.campaign_type} onChange={e => setFormData({...formData, campaign_type: e.target.value as any})}>
                  <option value="cold_email">Cold Email Only</option>
                  <option value="linkedin_outreach">LinkedIn Only</option>
                  <option value="multi_channel">Multi-Channel Sequence</option>
                  <option value="abm">Account-Based Marketing</option>
               </select>
            </div>

            <div className="neo-container p-6 bg-[var(--neo-accent)]">
               <label className="neo-label">Target Meetings</label>
               <input type="number" required className="neo-input" value={formData.target_meetings || ''} onChange={e => setFormData({...formData, target_meetings: e.target.value ? parseInt(e.target.value) : 0})} min="1" />
            </div>
          </div>

          <div className="pt-6 border-t-4 border-black text-right">
            <button type="submit" className="neo-button neo-button-primary text-xl px-8 py-4">
              NEXT: ADVANCED CONFIG &rarr;
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="neo-card">
      <h2 className="neo-header border-b-4 border-black pb-2 mb-6 inline-block bg-[var(--neo-secondary)] px-2 rotate-1">Step 2: Advanced Configuration</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-6">
          
          {/* 1. Milvus RAG Knowledge Ingestion */}
          <div className="neo-container p-6 bg-white space-y-4">
            <h3 className="font-bold text-sm uppercase tracking-wider text-blue-700">1. Milvus RAG Knowledge & Grounding</h3>
            <div>
              <label className="neo-label">Product Docs / Links / Collateral (Comma separated URLs)</label>
              <input className="neo-input" value={contentStr} onChange={e => setContentStr(e.target.value)} placeholder="https://docs.acme.com, https://acme.com/features" />
            </div>
            <div>
              <label className="neo-label">Proof Points & Case Studies (One per line)</label>
              <textarea className="neo-input h-20" value={caseStudiesStr} onChange={e => setCaseStudiesStr(e.target.value)} placeholder="Helped Acme Corp reduce server cost by 35%&#10;G2 rating: 4.9/5 with 500+ reviews" />
            </div>
            <div>
              <label className="neo-label">Key Differentiators / 'Why We Win' (Comma separated)</label>
              <input className="neo-input" value={differentiatorsStr} onChange={e => setDifferentiatorsStr(e.target.value)} placeholder="Self-hosted, SOC2 certified, No per-seat markup" />
            </div>
          </div>

          {/* 2. Target Prospect Sourcing Pipeline */}
          <div className="neo-container p-6 bg-[#fdfcf7] space-y-4 border-4 border-black">
            <div className="flex items-center justify-between">
              <h3 className="font-black text-sm uppercase tracking-wider text-black">
                2. Target Prospect Sourcing Pipeline
              </h3>
              <span className="text-xs font-bold uppercase bg-yellow-300 border-2 border-black px-2 py-0.5">
                Dual-Mode Ingestion
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div 
                onClick={() => setSourcingMode('ai_sourcing')}
                className={`p-4 border-3 border-black cursor-pointer transition-all ${
                  sourcingMode === 'ai_sourcing' 
                    ? 'bg-blue-100 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' 
                    : 'bg-white hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <input 
                    type="radio" 
                    name="sourcing_mode" 
                    checked={sourcingMode === 'ai_sourcing'} 
                    onChange={() => setSourcingMode('ai_sourcing')} 
                    className="accent-black h-4 w-4"
                  />
                  <span className="font-black text-sm">Autonomous AI Discovery</span>
                </div>
                <p className="text-xs text-gray-600 mt-2">
                  The agent automatically searches, discovers, and enrolls high-probability B2B buyer profiles matching your ICP, titles, and geography.
                </p>
              </div>

              <div 
                onClick={() => setSourcingMode('csv_upload')}
                className={`p-4 border-3 border-black cursor-pointer transition-all ${
                  sourcingMode === 'csv_upload' 
                    ? 'bg-purple-100 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' 
                    : 'bg-white hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <input 
                    type="radio" 
                    name="sourcing_mode" 
                    checked={sourcingMode === 'csv_upload'} 
                    onChange={() => setSourcingMode('csv_upload')} 
                    className="accent-black h-4 w-4"
                  />
                  <span className="font-black text-sm">Upload CSV Prospect List</span>
                </div>
                <p className="text-xs text-gray-600 mt-2">
                  Directly ingest and enroll your verified spreadsheet of prospects into the campaign's dedicated CRM pipeline.
                </p>
              </div>
            </div>

            {sourcingMode === 'csv_upload' && (
              <div className="mt-4 p-4 bg-white border-2 border-dashed border-black space-y-3">
                <label className="neo-label text-xs">Select Prospect CSV File (.csv)</label>
                <input 
                  type="file" 
                  accept=".csv" 
                  onChange={handleCsvFileChange}
                  className="block w-full text-sm text-gray-900 file:mr-4 file:py-2 file:px-4 file:border-2 file:border-black file:text-xs file:font-black file:uppercase file:bg-yellow-300 hover:file:bg-yellow-400 cursor-pointer"
                />
                <p className="text-[11px] text-gray-500">
                  Headers required: <code>name</code>, <code>email</code>, <code>company</code> (Optional: <code>title</code>, <code>linkedin</code>)
                </p>

                {csvParseError && (
                  <p className="text-xs font-bold text-red-600 bg-red-50 p-2 border border-red-300">
                    {csvParseError}
                  </p>
                )}

                {csvContacts.length > 0 && (
                  <div className="space-y-2 mt-2">
                    <div className="flex items-center justify-between text-xs font-bold text-green-700 bg-green-50 p-2 border border-green-300">
                      <span>✓ Loaded {csvContacts.length} prospects from {csvFileName}</span>
                      <span className="uppercase text-[10px] bg-green-200 px-2 py-0.5 border border-green-800">Ready to Enroll</span>
                    </div>

                    <div className="max-h-28 overflow-y-auto border border-gray-300 text-xs">
                      <table className="w-full text-left">
                        <thead className="bg-gray-100 font-bold">
                          <tr>
                            <th className="p-1">Name</th>
                            <th className="p-1">Email</th>
                            <th className="p-1">Company</th>
                            <th className="p-1">Title</th>
                          </tr>
                        </thead>
                        <tbody>
                          {csvContacts.slice(0, 5).map((c, i) => (
                            <tr key={i} className="border-t border-gray-200">
                              <td className="p-1 font-semibold">{c.name}</td>
                              <td className="p-1 font-mono text-[10px]">{c.email}</td>
                              <td className="p-1">{c.company_name}</td>
                              <td className="p-1 text-gray-500">{c.title || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {csvContacts.length > 5 && (
                        <p className="text-[10px] text-gray-400 text-center py-1 bg-gray-50">
                          + {csvContacts.length - 5} more prospects...
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 3. Brand Tone, Guardrails & Strategy */}
          <div className="neo-container p-6 bg-gray-50 space-y-4">
            <h3 className="font-bold text-sm uppercase tracking-wider text-purple-700">3. Brand Tone & AI Guardrails</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="neo-label">Brand Tone / Voice</label>
                <select className="neo-input" value={formData.brand_tone} onChange={e => setFormData({...formData, brand_tone: e.target.value})}>
                  <option value="direct_consultative">Direct & Consultative</option>
                  <option value="challenger">Challenger / Provocative</option>
                  <option value="peer_founder">Peer / Founder-to-Founder</option>
                  <option value="enterprise_formal">Enterprise Formal</option>
                </select>
              </div>
              <div>
                <label className="neo-label">Primary Offer / CTA</label>
                <select className="neo-input" value={formData.primary_cta} onChange={e => setFormData({...formData, primary_cta: e.target.value})}>
                  <option value="soft_interest">Soft Interest ("Worth a quick peek?")</option>
                  <option value="hard_demo">Hard Demo ("Grab 15 mins on calendar")</option>
                  <option value="value_asset">Value Asset ("Send you the free benchmark?")</option>
                </select>
              </div>
            </div>

            <div>
              <label className="neo-label">Negative Constraints / Forbidden Words (Comma separated)</label>
              <input className="neo-input" value={negativeConstraintsStr} onChange={e => setNegativeConstraintsStr(e.target.value)} placeholder="no pricing, never say revolutionize, do not mention discount" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="neo-label">Target Geography</label>
                <input className="neo-input" value={formData.target_geography} onChange={e => setFormData({...formData, target_geography: e.target.value})} placeholder="North America" />
              </div>
              <div>
                <label className="neo-label">Pricing Tier</label>
                <select className="neo-input" value={formData.pricing_tier} onChange={e => setFormData({...formData, pricing_tier: e.target.value})}>
                  <option value="freemium_self_serve">Freemium / Self-Serve</option>
                  <option value="mid_market">Mid-Market ($5k-$25k ACV)</option>
                  <option value="enterprise_custom">Enterprise ($50k+ Custom)</option>
                </select>
              </div>
            </div>
          </div>

          {/* 3. Sender Identity */}
          <div className="neo-container p-6 bg-white space-y-4">
            <h3 className="font-bold text-sm uppercase tracking-wider text-green-700">3. Sender Identity</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="neo-label text-sm">Sender Name</label>
                <input className="neo-input" value={senderName} onChange={e => setSenderName(e.target.value)} placeholder="Alex" />
              </div>
              <div>
                <label className="neo-label text-sm">Sender Title</label>
                <input className="neo-input" value={senderTitle} onChange={e => setSenderTitle(e.target.value)} placeholder="Head of Partnerships" />
              </div>
            </div>
          </div>

          {/* 4. Budget, Goals & Execution */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="neo-card-pink">
              <label className="neo-label">Campaign Budget ($ USD)</label>
              <input type="number" step="0.01" className="neo-input" value={budgetStr} onChange={e => setBudgetStr(e.target.value)} placeholder="5000" />
            </div>

            <div className="neo-container p-6 bg-[var(--neo-primary)]">
              <label className="neo-label">Overall Achievement / Goals (Comma separated)</label>
              <input className="neo-input" value={okrStr} onChange={e => setOkrStr(e.target.value)} placeholder="Drive 50 signups, Increase brand awareness" />
            </div>
          </div>

          <div className="neo-card-purple grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="col-span-full">
               <label className="neo-label">API Credentials (Optional for Execution)</label>
            </div>
            <div>
              <label className="neo-label text-sm">Email Provider Key</label>
              <input type="password" className="neo-input" value={emailApi} onChange={e => setEmailApi(e.target.value)} placeholder="sk_email_..." />
            </div>
            <div>
              <label className="neo-label text-sm">LinkedIn API ID/Token</label>
              <input type="password" className="neo-input" value={linkedinApi} onChange={e => setLinkedinApi(e.target.value)} placeholder="urn:li:person_..." />
            </div>
          </div>

        </div>

        <div className="pt-6 border-t-4 border-black flex justify-between">
          <button type="button" onClick={() => setStep(1)} className="neo-button bg-gray-200 text-lg px-6 py-2">
            &larr; BACK
          </button>
          <button type="submit" disabled={loading} className="neo-button neo-button-primary text-xl px-8 py-4">
            {loading ? "INITIALIZING..." : "LAUNCH AGENT PIPELINE"}
          </button>
        </div>
      </form>
    </div>
  );
}
