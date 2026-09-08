import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/campaigns"

payload = {
    "campaign_name": "Acme Cloud Infrastructure Optimization",
    "company_name": "Acme Systems",
    "product_service": "Self-Hosted Enterprise Cloud Cost Optimizer",
    "value_proposition": "Cuts AWS/GCP cloud egress and compute bills by 35% with zero agent overhead.",
    "target_icp": "VP of Infrastructure, Head of DevOps, and CTOs at scale-ups",
    "campaign_type": "multi_channel",
    "duration_days": 30,
    "start_date": "2026-09-07",
    "target_meetings": 10,
    "budget": 5000.0,
    "content_assets": [
        "https://docs.acme.com",
        "https://acme.com/features"
    ],
    "case_studies": [
        "Helped Acme Corp reduce server cost by 35%",
        "G2 rating: 4.9/5 with 500+ reviews"
    ],
    "differentiators": [
        "Self-hosted",
        "SOC2 certified",
        "No per-seat markup"
    ],
    "brand_tone": "direct_consultative",
    "primary_cta": "soft_interest",
    "negative_constraints": [
        "no pricing",
        "never say revolutionize",
        "do not mention discount"
    ],
    "target_geography": "North America",
    "pricing_tier": "mid_market",
    "sender_profile": {
        "name": "Alex",
        "title": "Head of Partnerships"
    },
    "business_okrs": [
        {
            "objective": "Drive 10 qualified discovery calls",
            "key_results": [
                "15% reply rate on sequence",
                "Zero compliance/spam trigger violations"
            ]
        }
    ]
}

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "default_dev_key"
}

def post_campaign():
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS
    )
    print("\n[1/4] POSTing payload to /api/campaigns ...")
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        data = res.get("data", {})
        thread_id = data.get("thread_id")
        current_node = data.get("current_node")
        print(f"-> Response Status: {resp.status} (Success: {res.get('success')})")
        print(f"-> Thread ID: {thread_id}")
        print(f"-> Initial Node: {current_node}")
        return thread_id

def poll_execution(thread_id: str, max_wait: int = 150):
    print(f"\n[2/4] Polling campaign pipeline execution for thread {thread_id} ...")
    start = time.time()
    last_node = ""
    while time.time() - start < max_wait:
        try:
            req = urllib.request.Request(f"{BASE_URL}/{thread_id}/state", headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                data = res.get("data", {})
                current_node = data.get("current_node")
                if current_node != last_node:
                    print(f"   * Node transitioned: {last_node or 'start'} -> {current_node}")
                    last_node = current_node
                
                # Check if reached HITL approval or completed state
                if current_node in ("hitl_approval_node", "approval_pending", "complete", "human_approval"):
                    print(f"-> Pipeline reached terminal/approval stage: {current_node}")
                    return data
                if data.get("error"):
                    print(f"-> Pipeline encountered error: {data.get('error')}")
                    return data
        except Exception as e:
            print(f"   Warning polling state: {e}")
        time.sleep(3)
    print("-> Timeout reached waiting for pipeline.")
    return None

def check_knowledge(thread_id: str):
    print(f"\n[3/4] Verifying Ingested Milvus Knowledge for thread {thread_id} ...")
    queries = [
        ("General RAG", f"{BASE_URL}/{thread_id}/knowledge?query=cloud+cost+infrastructure"),
        ("Web Intel", f"{BASE_URL}/{thread_id}/knowledge?query=market+competitor+pricing&category=web_intel")
    ]
    for label, url in queries:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                data = res.get("data", {})
                matches = data.get("matches", [])
                print(f"-> [{label}] Found {len(matches)} matches in Milvus:")
                for i, m in enumerate(matches[:3], 1):
                    snippet = m.get("text", "")[:120].replace("\n", " ")
                    score = m.get("score")
                    cat = m.get("category")
                    print(f"   [{i}] (Score: {score:.3f} | Cat: {cat}) {snippet}...")
        except Exception as e:
            print(f"-> [{label}] Query failed: {e}")

def verify_generated_copy(data: dict):
    print("\n[4/4] Inspecting Generated Creatives & Strategy ...")
    if not data:
        print("-> No state data available.")
        return
    
    strategy = data.get("strategy", {})
    variants = strategy.get("strategy_variants", [])
    print(f"-> Strategy Variants Generated: {len(variants)}")
    for v in variants:
        print(f"   * Variant [{v.get('variant_id')}]: {v.get('variant_name')} (Angle: {v.get('messaging_angle')})")
    
    creatives = data.get("creatives", {}).get("variant_creatives", {})
    print(f"-> Creatives Available for Variants: {list(creatives.keys())}")
    for var_id, bundle in creatives.items():
        emails = bundle.get("email_sequences", [])
        linkedin = bundle.get("linkedin_scripts", [])
        print(f"\n   --- Creative Bundle for {var_id} ---")
        print(f"   * Email Sequence Count: {len(emails)}")
        if emails:
            e1 = emails[0]
            print(f"     Subject: {e1.get('subject_line')}")
            print(f"     Body Snippet:\n     {e1.get('body_html', '')[:250]}...\n")
        print(f"   * LinkedIn Scripts Count: {len(linkedin)}")
        if linkedin:
            l1 = linkedin[0]
            print(f"     Type: {l1.get('message_type')}")
            print(f"     Text: {l1.get('text', '')[:180]}...")

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        t_id = sys.argv[1]
        print(f"\n[Direct Check] Querying existing thread {t_id} ...")
        req = urllib.request.Request(f"{BASE_URL}/{t_id}/state", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            final_state = res.get("data", {})
        check_knowledge(t_id)
        verify_generated_copy(final_state)
    else:
        t_id = post_campaign()
        if t_id:
            final_state = poll_execution(t_id)
            check_knowledge(t_id)
            verify_generated_copy(final_state)
