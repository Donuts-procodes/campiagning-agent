import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/campaigns"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "default_dev_key"
}

def make_request(url: str, method: str = "GET", data: dict | None = None) -> dict:
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        print(f"[HTTP {e.code}] Error: {err_content}")
        raise

def run_dry_test():
    print("=" * 70)
    print(" DRY TEST: CLOSED-LOOP AGENTIC WORKFLOW (jj.mmd)")
    print(" Upstream -> Midstream -> Downstream CRM -> Closed-Loop Feedback")
    print("=" * 70)

    # ---------------------------------------------------------
    # STAGE 1: Upstream (Campaign Strategy Agent)
    # ---------------------------------------------------------
    print("\n>>> [STAGE 1: UPSTREAM] Initializing Campaign with ROAS & CAC Targets...")
    campaign_payload = {
        "campaign_name": "Autonomous Performance Outbound Q4",
        "company_name": "DataMesh Systems",
        "product_service": "Enterprise Distributed Query Accelerator",
        "value_proposition": "Reduces multi-cloud Snowflake & BigQuery compute costs by 45%",
        "target_icp": "VP Data Platform, Chief Data Officer, Head of Analytics",
        "campaign_type": "multi_channel",
        "duration_days": 14,
        "start_date": "2026-09-08",
        "target_meetings": 10,
        "budget": 6000.0,
        "target_roas": 3.5,
        "target_cac": 300.0,
        "budget_allocation": {
            "cold_email": 0.35,
            "linkedin": 0.25,
            "meta_ads": 0.20,
            "google_ads": 0.20
        },
        "prospect_sourcing_mode": "csv_upload",
        "initial_contacts": [
            {
                "name": "Jordan Hayes",
                "company_name": "FinTech Core",
                "email": "j.hayes@fintechcore.com",
                "title": "Head of Data Engineering",
                "status": "enrolled",
                "attribution_source": "outbound_email"
            }
        ]
    }

    create_resp = make_request(BASE_URL, method="POST", data=campaign_payload)
    assert create_resp.get("success"), "Campaign creation failed"
    thread_id = create_resp["data"]["thread_id"]
    print(f"-> Created Campaign Thread ID: {thread_id}")

    # Poll until LangGraph pipeline reaches HITL approval node
    print("\n-> Polling LangGraph execution (Knowledge -> ICP -> Strategy -> Creatives -> Media Ads -> Compliance)...")
    max_wait = 90
    poll_start = time.time()
    state_data = None

    while time.time() - poll_start < max_wait:
        state_resp = make_request(f"{BASE_URL}/{thread_id}/state")
        current_node = state_resp.get("data", {}).get("current_node")
        print(f"   [t={int(time.time() - poll_start)}s] Current node: {current_node}")
        if current_node in ("hitl_approval_node", "outreach_dispatcher"):
            state_data = state_resp["data"]
            break
        time.sleep(3)

    assert state_data is not None, "Pipeline timed out before reaching HITL approval"
    print("-> Pipeline reached HITL approval stage successfully!")

    # Verify Strategy State has ROAS & CAC Targets
    strategy = state_data.get("strategy", {})
    variants = strategy.get("strategy_variants", [])
    print(f"-> Target ROAS: {strategy.get('target_roas')}x | Target CAC: ${strategy.get('target_cac')}")
    print(f"-> Generated Strategy Variants: {len(variants)}")
    assert len(variants) > 0, "No strategy variants generated"
    chosen_variant_id = variants[0]["variant_id"]
    print(f"-> Selected Variant for Execution: {chosen_variant_id}")

    # Verify Creatives (Meta Ads, Google Ads, Inbound Forms)
    creatives = state_data.get("creatives", {}).get("variant_creatives", {}).get(chosen_variant_id, {})
    ad_creatives = creatives.get("ad_creatives", [])
    inbound_forms = creatives.get("inbound_forms", [])
    print(f"-> Generated Ad Creatives: {len(ad_creatives)} (Platforms: {[a.get('platform') for a in ad_creatives]})")
    print(f"-> Generated Inbound Forms: {len(inbound_forms)}")
    assert len(ad_creatives) > 0, "Expected ad creatives to be generated"
    assert len(inbound_forms) > 0, "Expected inbound forms to be generated"

    # Approve and Dispatch Campaign via HITL
    print(f"\n-> Approving variant '{chosen_variant_id}' for execution...")
    approve_resp = make_request(
        f"{BASE_URL}/{thread_id}/approve",
        method="POST",
        data={"approved_variant_id": chosen_variant_id, "review_status": "approved"}
    )
    assert approve_resp.get("success"), "Approval failed"
    print("-> Campaign approved. Waiting for outreach dispatcher to write execution receipts...")
    
    # Poll for receipts
    receipts = []
    for _ in range(15):
        time.sleep(1)
        receipts_resp = make_request(f"{BASE_URL}/{thread_id}/receipts")
        receipts = receipts_resp.get("data", {}).get("receipts", [])
        if receipts:
            break

    channels = [r.get("channel") for r in receipts]
    print(f"-> Dispatched Channels: {channels}")
    assert "media_ads" in channels, "media_ads was not dispatched in ExecutionReceipts"

    # ---------------------------------------------------------
    # STAGE 2: Midstream (Inbound Data Collection)
    # ---------------------------------------------------------
    print("\n>>> [STAGE 2: MIDSTREAM] Simulating Inbound Leads from Web Forms & Ad Conversions...")
    
    # 2.1 Webhook lead from Meta Ads
    meta_lead_payload = {
        "name": "David Sterling",
        "company_name": "Vertex Global Analytics",
        "email": "d.sterling@vertexanalytics.com",
        "title": "Chief Data Officer",
        "attribution_source": "meta_ads",
        "ad_id": ad_creatives[0].get("ad_id", "meta_var1"),
        "form_id": inbound_forms[0].get("form_id", "form_var1"),
        "utm_tags": {
            "utm_source": "meta",
            "utm_medium": "cpc",
            "utm_campaign": chosen_variant_id
        },
        "deal_value": 8500.0,
        "status": "new"
    }
    inbound_resp = make_request(f"{BASE_URL}/{thread_id}/inbound/webhook", method="POST", data=meta_lead_payload)
    assert inbound_resp.get("success"), "Inbound webhook failed"
    meta_contact = inbound_resp["data"]
    meta_contact_id = meta_contact["contact_id"]
    print(f"-> [Inbound Webhook] Captured lead '{meta_contact['name']}' ({meta_contact['attribution_source']}) with deal_value=${meta_contact['deal_value']}")

    # 2.2 Inbound Demo Request
    demo_payload = {
        "name": "Rachel Vance",
        "company_name": "HyperScale Cloud",
        "email": "rvance@hyperscalecloud.io",
        "title": "VP Data Architecture",
        "notes": "Urgent: Need Snowflake optimization before Q4 budget freeze",
        "utm_tags": {"utm_source": "google", "utm_medium": "cpc"},
        "deal_value": 12000.0
    }
    demo_resp = make_request(f"{BASE_URL}/{thread_id}/inbound/demo-request", method="POST", data=demo_payload)
    assert demo_resp.get("success"), "Inbound demo request failed"
    demo_contact = demo_resp["data"]
    demo_contact_id = demo_contact["contact_id"]
    print(f"-> [Inbound Demo Request] Captured high-intent lead '{demo_contact['name']}' ({demo_contact['attribution_source']}) - Initial Status: {demo_contact['status']}")

    # ---------------------------------------------------------
    # STAGE 3: Downstream (CRM Workspace - Built-in)
    # ---------------------------------------------------------
    print("\n>>> [STAGE 3: DOWNSTREAM] Verifying CRM Records & Advancing Status Pipeline...")
    crm_resp = make_request(f"{BASE_URL}/{thread_id}/crm")
    crm_leads = crm_resp.get("data", [])
    print(f"-> Total CRM Leads linked to campaign_thread_id: {len(crm_leads)}")
    for lead in crm_leads:
        print(f"   * {lead['name']} | {lead['company_name']} | Status: {lead['status']} | Attribution: {lead['attribution_source']} | Deal: ${lead.get('deal_value', 0.0)}")

    # Advance Status Pipeline: New -> Qualified -> Converted
    print("\n-> Progressing Meta Ad lead from 'new' -> 'qualified' -> 'converted'...")
    make_request(f"{BASE_URL}/{thread_id}/crm/{meta_contact_id}", method="PATCH", data={"status": "qualified"})
    make_request(f"{BASE_URL}/{thread_id}/crm/{meta_contact_id}", method="PATCH", data={"status": "converted"})

    print("-> Progressing Demo lead from 'qualified' -> 'converted'...")
    make_request(f"{BASE_URL}/{thread_id}/crm/{demo_contact_id}", method="PATCH", data={"status": "converted"})

    # Verify pipeline statuses updated in CRM
    updated_crm = make_request(f"{BASE_URL}/{thread_id}/crm")["data"]
    converted_leads = [c for c in updated_crm if c.get("status") in ("converted", "meeting_booked")]
    print(f"-> Verified Converted Leads in CRM: {len(converted_leads)}")
    assert len(converted_leads) >= 2, "Expected at least 2 converted leads"

    # ---------------------------------------------------------
    # STAGE 4: Feedback Loop (Closed-Loop Learning)
    # ---------------------------------------------------------
    print("\n>>> [STAGE 4: FEEDBACK LOOP] Computing Actual CAC, ROAS & Channel Performance...")
    feedback_eval = make_request(f"{BASE_URL}/{thread_id}/feedback-loop")
    assert feedback_eval.get("success"), "Feedback evaluation failed"
    metrics = feedback_eval["data"]

    print("\n----- CLOSED-LOOP PERFORMANCE AUDIT -----")
    print(f"Total Budget Spend:   ${metrics['total_spend']}")
    print(f"Total Enrolled Leads: {metrics['total_enrolled']}")
    print(f"Total Converted:      {metrics['converted_count']}")
    print(f"Conversion Rate:      {metrics['conversion_rate'] * 100:.2f}%")
    print(f"Actual CAC:           ${metrics['actual_cac']} (Target: ${metrics['target_cac']})")
    print(f"Actual ROAS:          {metrics['actual_roas']}x (Target: {metrics['target_roas']}x)")
    print(f"Performance Status:   {metrics['performance_status'].upper()}")
    print("Channel Breakdown:")
    for ch, data in metrics["channel_performance"].items():
        print(f"   - {ch}: {data['enrolled']} enrolled, {data['converted']} converted, ${data['deal_value']} deal volume")
    print("Optimization Directives:")
    for rec in metrics["optimization_recommendations"]:
        print(f"   * {rec}")
    print(f"Budget Reallocations: {metrics['budget_reallocations']}")
    print("-----------------------------------------")

    # Apply Feedback back to Upstream Strategy
    print("\n-> Applying Feedback to Campaign State (ACTUALS -.-> STRATEGY)...")
    apply_resp = make_request(f"{BASE_URL}/{thread_id}/feedback-loop/apply", method="POST")
    assert apply_resp.get("success"), "Applying feedback loop failed"
    applied_data = apply_resp["data"]
    print(f"-> Successfully written to LangGraph state! Feedback payload recorded: {applied_data['feedback_payload']['historical_roas']}x ROAS")

    # Verify Campaign State reflects Closed-Loop State
    final_state = make_request(f"{BASE_URL}/{thread_id}/state")["data"]
    closed_loop_state = final_state.get("closed_loop", {})
    latest_eval = closed_loop_state.get("latest_evaluation")
    assert latest_eval is not None, "Closed loop state missing from LangGraph state"
    print(f"-> Final State Verified: latest_evaluation.actual_cac=${latest_eval['actual_cac']}, actual_roas={latest_eval['actual_roas']}x")

    print("\n" + "=" * 70)
    print(" [SUCCESS] ALL 4 STAGES OF THE AGENTIC CLOSED-LOOP WORKFLOW PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    run_dry_test()
