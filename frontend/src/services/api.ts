export interface ObjectiveOKR {
  objective: string;
  key_results: string[];
}

export interface UserInput {
  campaign_name: string;
  company_name: string;
  product_service: string;
  value_proposition: string;
  target_icp: string;
  campaign_type: 'cold_email' | 'linkedin_outreach' | 'abm' | 'product_launch_pr' | 'partner_affiliate' | 'content_promotion' | 'retention_upsell' | 'multi_channel';
  duration_days: number;
  start_date: string;
  business_okrs?: ObjectiveOKR[];
  
  target_accounts?: string[];
  target_personas?: string[];
  content_assets?: string[];
  launch_url?: string;
  partner_profile?: string;
  customer_segment?: string;
  trigger_event?: string;
  success_metrics?: string[];
  channels_allowed?: string[];
  
  target_meetings?: number;
  competitors?: string[];
  budget?: number;
  credentials?: Record<string, string>;

  // High-precision AI steering & RAG grounding
  case_studies?: string[];
  differentiators?: string[];
  past_winning_copy?: string[];
  brand_tone?: string;
  negative_constraints?: string[];
  primary_cta?: string;
  sender_profile?: Record<string, string>;
  target_geography?: string;
  pricing_tier?: string;

  // Prospect Sourcing Pipeline
  prospect_sourcing_mode?: 'csv_upload' | 'ai_sourcing';
  initial_contacts?: Partial<CampaignLead>[];
}

export interface CadenceStep {
  day: number;
  channel: string;
  action_type: string;
}

export interface OutreachVariant {
  variant_id: string;
  variant_name: string;
  description: string;
  messaging_angle: string;
  estimated_reply_rate: number;
  required_contact_volume: number;
  selected_channels: string[];
  cadence_timeline: CadenceStep[];
  target_segments?: string[];
  assets_required?: string[];
  execution_readiness?: string;
  kpi_assumptions?: Record<string, any>;
}

export interface StrategyState {
  target_meetings: number;
  estimated_reply_rate: number;
  required_contact_volume: number;
  strategy_variants: OutreachVariant[];
}

export interface ExecutionReceipt {
  channel: string;
  job_id: string;
  contacts_enrolled: number;
  status: string;
  response_payload: Record<string, any>;
  dispatched_at: string;
}

export interface EmailSequence {
  step_number: number;
  subject_line: string;
  body_html: string;
  variables_needed: string[];
}

export interface LinkedInScript {
  step_number: number;
  message_type: string;
  text: string;
}

export interface CallScript {
  step_number: number;
  script_text: string;
}

export interface GenericAsset {
  asset_type: string;
  content_text: string;
  variables_needed: string[];
}

export interface CreativeBundle {
  variant_id: string;
  email_sequences: EmailSequence[];
  linkedin_scripts: LinkedInScript[];
  call_scripts: CallScript[];
  generic_assets: GenericAsset[];
}

export interface CreativeBundleState {
  variant_creatives: Record<string, CreativeBundle>;
}

export interface AuditError {
  check_name: string;
  message: string;
  severity: string;
}

export interface VerificationState {
  spam_words_check: boolean;
  variables_check: boolean;
  compliance_check_passed: boolean;
  all_passed: boolean;
  audit_errors: AuditError[];
}

export interface HITLState {
  approved_variant_id: string;
  human_modifications: Record<string, any>;
  review_status: 'pending' | 'approved' | 'rejected';
}

export interface CampaignState {
  user_input?: UserInput;
  strategy?: StrategyState;
  creatives?: CreativeBundleState;
  verification?: VerificationState;
  hitl?: HITLState;
  execution?: { receipts: ExecutionReceipt[] };
  revision_count?: number;
  current_node?: string;
  error?: string;
}

export async function createCampaign(input: UserInput): Promise<{ thread_id: string; current_node?: string }> {
  const res = await fetch('/api/campaigns', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': 'default_dev_key' },
    body: JSON.stringify(input)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create campaign");
  }
  const json = await res.json();
  return json.data || json;
}

export async function getCampaignState(threadId: string): Promise<CampaignState> {
  const res = await fetch(`/api/campaigns/${threadId}/state`, {
    headers: { 'X-API-Key': 'default_dev_key' }
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch state");
  }
  const json = await res.json();
  return json.data || json;
}

export async function approveCampaign(threadId: string, variantId: string, modifications: Record<string, any> = {}): Promise<void> {
  const res = await fetch(`/api/campaigns/${threadId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': 'default_dev_key' },
    body: JSON.stringify({
      approved_variant_id: variantId,
      human_modifications: modifications,
      review_status: 'approved'
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to approve");
  }
}

export async function getCampaignReceipts(threadId: string): Promise<{ receipts: ExecutionReceipt[] }> {
  const res = await fetch(`/api/campaigns/${threadId}/receipts`, {
    headers: { 'X-API-Key': 'default_dev_key' }
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch receipts");
  }
  const json = await res.json();
  return json.data || json;
}

export interface CampaignLead {
  enrollment_id: string;
  contact_id: string;
  name: string;
  title: string;
  email: string;
  linkedin_url?: string;
  company_name: string;
  status: 'enrolled' | 'sequence_active' | 'replied' | 'meeting_booked' | 'unsubscribed';
  variant_id: string;
  enrolled_at: string;
}

export async function getCampaignLeads(threadId: string): Promise<CampaignLead[]> {
  const res = await fetch(`/api/campaigns/${threadId}/crm`, {
    headers: { 'X-API-Key': 'default_dev_key' }
  });
  if (!res.ok) throw new Error("Failed to fetch campaign leads");
  const json = await res.json();
  return json.data || json;
}

export async function addCampaignLead(
  threadId: string,
  lead: { name: string; company_name: string; email: string; title?: string; linkedin_url?: string; status?: string; variant_id?: string }
): Promise<CampaignLead> {
  const res = await fetch(`/api/campaigns/${threadId}/crm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': 'default_dev_key' },
    body: JSON.stringify(lead)
  });
  if (!res.ok) throw new Error("Failed to add lead to campaign");
  const json = await res.json();
  return json.data || json;
}

export async function updateCampaignLeadStatus(threadId: string, contactId: string, status: string): Promise<void> {
  const res = await fetch(`/api/campaigns/${threadId}/crm/${contactId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': 'default_dev_key' },
    body: JSON.stringify({ status })
  });
  if (!res.ok) throw new Error("Failed to update lead status");
}

export async function seedCampaignLeads(threadId: string): Promise<CampaignLead[]> {
  const res = await fetch(`/api/campaigns/${threadId}/crm/seed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': 'default_dev_key' }
  });
  if (!res.ok) throw new Error("Failed to seed leads");
  const json = await res.json();
  return json.data || json;
}

export async function bulkEnrollCampaignLeads(
  threadId: string,
  contacts: Partial<CampaignLead>[]
): Promise<{ enrolled_count: number }> {
  const res = await fetch(`/api/campaigns/${threadId}/crm/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': 'default_dev_key' },
    body: JSON.stringify({ contacts })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to bulk enroll contacts");
  }
  const json = await res.json();
  return json.data || json;
}

export async function autoSourceCampaignLeads(
  threadId: string,
  payload?: { company_name?: string; target_icp?: string; target_geography?: string; count?: number }
): Promise<{ sourced_count: number }> {
  const res = await fetch(`/api/campaigns/${threadId}/crm/auto-source`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': 'default_dev_key' },
    body: JSON.stringify(payload || {})
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to auto-source contacts");
  }
  const json = await res.json();
  return json.data || json;
}
