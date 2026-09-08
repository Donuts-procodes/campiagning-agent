import json
import time
import urllib.parse
import urllib.request
from datetime import date

API_URL = "http://localhost:8000/api/campaigns"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "default_dev_key",
}

def print_header(title: str):
    print(f"\n{'='*70}\n{title}\n{'='*70}")

def main():
    print_header("AGENT LIVE WEB RESEARCH & PIPELINE TEST")
    
    payload = {
        "campaign_name": "DevOps Real-Time Observability",
        "company_name": "Datadog",
        "product_service": "Cloud Monitoring & Infrastructure Observability",
        "value_proposition": "Unified telemetry across Kubernetes, AWS, and GCP with sub-second alert latency.",
        "target_icp": "VP of Infrastructure and Head of DevOps at High-Growth SaaS",
        "competitors": ["Dynatrace", "New Relic"],
        "campaign_type": "cold_email",
        "duration_days": 30,
        "start_date": date.today().isoformat(),
        "case_studies": [
            "Cut mean time to detect (MTTD) microservice outages by 74% for FinTech enterprise"
        ],
        "differentiators": [
            "Over 600 turnkey integrations out of the box",
            "Kernel-level eBPF observability with zero overhead"
        ],
        "brand_tone": "direct_consultative",
        "negative_constraints": ["revolutionize", "synergy", "free trial"],
        "primary_cta": "soft_interest",
        "sender_profile": {
            "name": "Jordan Cole",
            "title": "Director of Solutions Architecture"
        },
        "target_geography": "North America",
        "pricing_tier": "mid_market",
        "channels_allowed": ["email"],
        "target_meetings": 10
    }

    # 1. Dispatch
    print("1. Launching campaign with autonomous web research...")
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=req_data, headers=HEADERS, method="POST")

    with urllib.request.urlopen(req) as res:
        res_json = json.loads(res.read().decode("utf-8"))
        thread_id = res_json.get("data", {}).get("thread_id")
        print(f"   [SUCCESS] Campaign created! Thread ID: {thread_id}")

    # 2. Poll for Knowledge Ingestion
    print("\n2. Polling for knowledge ingestion & live web research completion...")
    state_url = f"{API_URL}/{thread_id}/state"
    
    for attempt in range(1, 35):
        time.sleep(3)
        try:
            with urllib.request.urlopen(urllib.request.Request(state_url, headers=HEADERS)) as res:
                body = json.loads(res.read().decode("utf-8"))
                state = body.get("data", {})
                current_node = state.get("current_node")
                next_nodes = state.get("next_nodes", [])
                print(f"   [Attempt {attempt:02d}] Current: {current_node} | Next: {next_nodes}")

                if current_node not in [None, "knowledge_ingestion"]:
                    # Ingestion is complete, let's verify Milvus right away!
                    break
        except Exception as e:
            print(f"   [Polling] {e}")

    # 3. Query Milvus Web Intel Directly
    print("\n3. Verifying Milvus Vector DB for Dynamic Web Intelligence...")
    q = urllib.parse.quote("observability devops sre trends 2026")
    k_url = f"{API_URL}/{thread_id}/knowledge?query={q}&category=web_intel&top_k=3"
    
    try:
        with urllib.request.urlopen(urllib.request.Request(k_url, headers=HEADERS)) as res:
            k_res = json.loads(res.read().decode("utf-8"))
            matches = k_res.get("data", {}).get("matches", [])
            print(f"   --> Found {len(matches)} live web intelligence chunks in Milvus:")
            for idx, m in enumerate(matches, 1):
                print(f"   [{idx}] Score: {m.get('score')} | Category: {m.get('category')} | Source: {m.get('source')}")
                snippet = m.get("chunk_text", "").replace("\n", " ")[:130]
                print(f"       Text: \"{snippet}...\"")
    except Exception as e:
        print(f"   [Error querying Milvus]: {e}")

    # 4. Wait for Copy Generation & HITL Node
    print("\n4. Waiting for Planners & Copy Generator to finish...")
    for attempt in range(1, 25):
        time.sleep(3)
        try:
            with urllib.request.urlopen(urllib.request.Request(state_url, headers=HEADERS)) as res:
                body = json.loads(res.read().decode("utf-8"))
                state = body.get("data", {})
                current_node = state.get("current_node")

                if current_node == "hitl_approval_node" or state.get("hitl"):
                    print(f"\n   [SUCCESS] Reached HITL Approval stage!")
                    
                    # Display copy generated
                    creatives = state.get("creatives", {}).get("variant_creatives", {})
                    for v_id, bundle in creatives.items():
                        emails = bundle.get("email_sequences", [])
                        if emails:
                            print(f"\n   --- Generated Copy (Variant: {v_id}) ---")
                            print(f"   Subject : {emails[0].get('subject_line')}")
                            snippet = emails[0].get("body_html", "")[:260].replace("\n", " ")
                            print(f"   Excerpt : \"{snippet}...\"")
                    break
        except Exception:
            pass

    print_header("AGENT WEB PIPELINE TEST COMPLETE")

if __name__ == "__main__":
    main()
