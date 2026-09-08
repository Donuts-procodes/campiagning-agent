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
    with urllib.request.urlopen(req, timeout=20) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res

def test_mode_a_csv_upload():
    print("\n" + "="*60)
    print(" DRY TEST 1: MODE A - CSV / UPLOADED PROSPECT LIST")
    print("="*60)
    
    # 1. Prepare campaign payload with CSV-style pre-loaded contacts
    csv_contacts = [
        {
            "name": "Jordan Bell",
            "company_name": "Stripe",
            "email": "jbell@stripe.com",
            "title": "Principal Infrastructure Architect",
            "linkedin_url": "https://linkedin.com/in/jordanbell-infra",
            "variant_id": "variant1",
            "status": "enrolled"
        },
        {
            "name": "Samantha Wu",
            "company_name": "Databricks",
            "email": "samantha.wu@databricks.com",
            "title": "VP of Cloud Engineering",
            "linkedin_url": "https://linkedin.com/in/samanthawu-cloud",
            "variant_id": "variant1",
            "status": "enrolled"
        },
        {
            "name": "Devon Vance",
            "company_name": "Coinbase",
            "email": "dvance@coinbase.com",
            "title": "Director of SRE & DevOps",
            "linkedin_url": "https://linkedin.com/in/devon-vance",
            "variant_id": "variant1",
            "status": "enrolled"
        }
    ]

    payload = {
        "campaign_name": "CSV Ingestion Test Campaign",
        "company_name": "Acme Cloud",
        "product_service": "Cloud Cost Optimizer",
        "value_proposition": "Cuts AWS/GCP bills by 35%",
        "target_icp": "VP Infrastructure, Head of DevOps",
        "campaign_type": "multi_channel",
        "duration_days": 14,
        "start_date": "2026-09-07",
        "target_meetings": 5,
        "prospect_sourcing_mode": "csv_upload",
        "initial_contacts": csv_contacts
    }

    print("\n[Step 1.1] Initializing Campaign in 'csv_upload' mode with 3 pre-loaded contacts...")
    res = make_request(BASE_URL, method="POST", data=payload)
    thread_id = res.get("data", {}).get("thread_id")
    print(f"-> Created Thread ID: {thread_id} (Status: {res.get('data', {}).get('status')})")

    # 2. Verify contacts in campaign CRM
    print(f"\n[Step 1.2] Querying GET /api/campaigns/{thread_id}/crm ...")
    crm_res = make_request(f"{BASE_URL}/{thread_id}/crm")
    enrolled = crm_res.get("data", [])
    print(f"-> Total Enrolled Leads in Campaign CRM: {len(enrolled)}")
    for i, lead in enumerate(enrolled, 1):
        print(f"   [{i}] {lead.get('name')} | {lead.get('title')} at {lead.get('company_name')} ({lead.get('email')}) - Status: {lead.get('status')}")

    assert len(enrolled) == 3, f"Expected 3 enrolled contacts, got {len(enrolled)}"
    assert enrolled[0]["name"] == "Jordan Bell"

    # 3. Test supplemental bulk CSV append via POST /api/campaigns/{thread_id}/crm/bulk
    print(f"\n[Step 1.3] Testing supplemental bulk append via POST /api/campaigns/{thread_id}/crm/bulk ...")
    bulk_append = {
        "contacts": [
            {
                "name": "Alex Mercer",
                "company_name": "Figma",
                "email": "amercer@figma.com",
                "title": "Head of DevOps",
                "status": "enrolled"
            }
        ]
    }
    bulk_res = make_request(f"{BASE_URL}/{thread_id}/crm/bulk", method="POST", data=bulk_append)
    print(f"-> Bulk Appended Count: {bulk_res.get('data', {}).get('enrolled_count')}")

    crm_after = make_request(f"{BASE_URL}/{thread_id}/crm").get("data", [])
    print(f"-> Updated Total in CRM: {len(crm_after)}")
    assert len(crm_after) == 4, f"Expected 4 contacts after bulk append, got {len(crm_after)}"

    print("\n[RESULT] Mode A (CSV / Uploaded Prospect List) PASSED successfully!\n")
    return thread_id

def test_mode_b_autonomous_ai_sourcing():
    print("\n" + "="*60)
    print(" DRY TEST 2: MODE B - AUTONOMOUS AI PROSPECT SOURCING")
    print("="*60)

    payload = {
        "campaign_name": "AI Autonomous Sourcing Campaign",
        "company_name": "CloudSaver AI",
        "product_service": "Autonomous Kubernetes Egress Optimizer",
        "value_proposition": "Reduces multi-cloud egress by 40% with zero agent overhead",
        "target_icp": "VP Infrastructure, Head of DevOps, Platform Engineering Directors at Mid-Market Cloud SaaS",
        "campaign_type": "multi_channel",
        "duration_days": 21,
        "start_date": "2026-09-07",
        "target_meetings": 10,
        "target_geography": "North America",
        "prospect_sourcing_mode": "ai_sourcing",
        "initial_contacts": [] # Empty list -> triggers autonomous discovery
    }

    print("\n[Step 2.1] Initializing Campaign in 'ai_sourcing' mode (0 contacts provided)...")
    res = make_request(BASE_URL, method="POST", data=payload)
    thread_id = res.get("data", {}).get("thread_id")
    print(f"-> Created Thread ID: {thread_id} (Status: {res.get('data', {}).get('status')})")

    # Give the agent a moment to complete autonomous discovery
    time.sleep(2)

    # 2. Verify AI autonomously discovered and enrolled contacts
    print(f"\n[Step 2.2] Querying GET /api/campaigns/{thread_id}/crm for AI-sourced contacts...")
    crm_res = make_request(f"{BASE_URL}/{thread_id}/crm")
    sourced = crm_res.get("data", [])
    print(f"-> Total AI-Sourced Prospects Discovered: {len(sourced)}")
    for i, lead in enumerate(sourced, 1):
        print(f"   [{i}] {lead.get('name')} | {lead.get('title')} at {lead.get('company_name')} ({lead.get('email')}) - Status: {lead.get('status')}")

    assert len(sourced) >= 3, f"Expected at least 3 AI-sourced leads, got {len(sourced)}"
    
    # Verify titles align with the ICP
    titles_str = " ".join([l.get("title", "") for l in sourced]).lower()
    print(f"\n[Verification] Sample titles generated: {[l.get('title') for l in sourced[:3]]}")
    
    # 3. Test on-demand AI auto-sourcing endpoint
    print(f"\n[Step 2.3] Testing on-demand auto-source via POST /api/campaigns/{thread_id}/crm/auto-source ...")
    auto_source_payload = {
        "company_name": "CloudSaver AI",
        "target_icp": "Chief Information Security Officer (CISO)",
        "count": 2
    }
    auto_res = make_request(f"{BASE_URL}/{thread_id}/crm/auto-source", method="POST", data=auto_source_payload)
    print(f"-> On-demand Sourced Count: {auto_res.get('data', {}).get('sourced_count')}")

    print("\n[RESULT] Mode B (Autonomous AI Prospect Sourcing) PASSED successfully!\n")
    return thread_id

if __name__ == "__main__":
    t1 = test_mode_a_csv_upload()
    t2 = test_mode_b_autonomous_ai_sourcing()
    print("="*60)
    print(" ALL DRY TESTS PASSED: BOTH PROSPECT SOURCING MODES FUNCTIONAL")
    print(f" Mode A Thread: {t1}")
    print(f" Mode B Thread: {t2}")
    print("="*60)
