import json
import time
import urllib.error
import urllib.parse
import urllib.request
import sys

JSON_FILE = "payloads/backend_coverage_payloads.json"
API_URL = "http://localhost:8000/api/campaigns"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "default_dev_key",
}


def print_header(title: str):
    print(f"\n{'='*65}\n{title}\n{'='*65}")


def test_campaign_pipeline(campaign_key: str, payload: dict, approval_data: dict):
    print_header(f"TESTING PIPELINE: {campaign_key.upper()}")
    print(f"Campaign Name : {payload.get('campaign_name')}")
    print(f"Company       : {payload.get('company_name')}")
    print(f"Brand Tone    : {payload.get('brand_tone')}")
    print(f"Primary CTA   : {payload.get('primary_cta')}")
    print(f"Proof Points  : {len(payload.get('case_studies', []))} case studies")
    print(f"Guardrails    : {payload.get('negative_constraints')}")
    print(f"Docs / URLs   : {payload.get('content_assets')}")
    print("-" * 65)

    # 1. Dispatch Campaign
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=req_data, headers=HEADERS, method="POST")

    try:
        with urllib.request.urlopen(req) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            thread_id = res_json.get("data", {}).get("thread_id")
            print(f"[1/4] Workflow Dispatched! Thread ID: {thread_id}")
    except urllib.error.URLError as e:
        print(f"[ERROR] Failed to start campaign: {e}")
        if hasattr(e, "read"):
            print(e.read().decode("utf-8"))
        return False

    # 2. Poll Workflow Execution
    state_url = f"{API_URL}/{thread_id}/state"
    print(f"[2/4] Polling execution through LangGraph pods...")

    hitl_reached = False
    final_state = {}

    for attempt in range(1, 35):
        time.sleep(3)
        try:
            state_req = urllib.request.Request(state_url, headers=HEADERS)
            with urllib.request.urlopen(state_req) as res:
                body = json.loads(res.read().decode("utf-8"))
                state = body.get("data", {})
                current_node = state.get("current_node")
                next_nodes = state.get("next_nodes", [])
                print(f"   * [Attempt {attempt:02d}] Current Node: {current_node} | Next: {next_nodes}")

                if current_node == "hitl_approval_node" or "hitl_approval_node" in next_nodes:
                    print(f"   --> Reached HITL Approval Gate!")
                    hitl_reached = True
                    final_state = state
                    break
                if state.get("error"):
                    print(f"[ERROR] Pipeline error encountered: {state.get('error')}")
                    return False
        except Exception as e:
            print(f"   * [Warning] Polling error: {e}")

    if not hitl_reached:
        print("[TIMEOUT] Pipeline did not reach HITL approval within polling window.")
        return False

    # 3. Query Milvus Vector Knowledge Store
    print(f"\n[3/4] Verifying Milvus Vector Store under Campaign ID: {thread_id}")
    try:
        # General knowledge query
        knowledge_query = urllib.parse.quote("compliance audit misconfiguration")
        k_url = f"{API_URL}/{thread_id}/knowledge?query={knowledge_query}&top_k=2"
        with urllib.request.urlopen(urllib.request.Request(k_url, headers=HEADERS)) as res:
            k_res = json.loads(res.read().decode("utf-8"))
            matches = k_res.get("data", {}).get("matches", [])
            print(f"   [General RAG Knowledge] Found {len(matches)} chunks:")
            for idx, m in enumerate(matches, 1):
                print(f"   [{idx}] Cat: {m.get('category')} | Score: {m.get('score')} | Source: {m.get('source')}")
                snippet = m.get("chunk_text", "").replace("\n", " ")[:110]
                print(f"       \"{snippet}...\"")

        # Live Web Intelligence query
        web_query = urllib.parse.quote("cloud security market trends 2026")
        k_web_url = f"{API_URL}/{thread_id}/knowledge?query={web_query}&category=web_intel&top_k=3"
        with urllib.request.urlopen(urllib.request.Request(k_web_url, headers=HEADERS)) as res:
            w_res = json.loads(res.read().decode("utf-8"))
            web_matches = w_res.get("data", {}).get("matches", [])
            print(f"\n   [Live Web Intelligence in Milvus (category=web_intel)] Found {len(web_matches)} chunks:")
            for idx, m in enumerate(web_matches, 1):
                print(f"   [{idx}] Score: {m.get('score')} | Source: {m.get('source')}")
                snippet = m.get("chunk_text", "").replace("\n", " ")[:120]
                print(f"       \"{snippet}...\"")
    except Exception as e:
        print(f"   [Warning] Could not query knowledge endpoint: {e}")

    # Inspect Compliance and Generated Copy
    verification = final_state.get("verification", {})
    print(f"\n   [Verification Audit]")
    print(f"   - All Checks Passed : {verification.get('all_passed')}")
    print(f"   - Spam Words Check  : {verification.get('spam_words_check')}")
    print(f"   - Audit Errors      : {verification.get('audit_errors', [])}")

    creatives = final_state.get("creatives", {}).get("variant_creatives", {})
    for v_id, bundle in creatives.items():
        emails = bundle.get("email_sequences", [])
        if emails:
            print(f"\n   [Sample Generated Copy - Variant: {v_id}]")
            print(f"   Subject: {emails[0].get('subject_line')}")
            snippet = emails[0].get("body_html", "")[:200].replace("\n", " ")
            print(f"   Body   : \"{snippet}...\"")

    # 4. Submit HITL Approval
    print(f"\n[4/4] Submitting Human-in-the-Loop Approval...")
    approve_url = f"{API_URL}/{thread_id}/approve"
    app_data = json.dumps(approval_data).encode("utf-8")
    app_req = urllib.request.Request(approve_url, data=app_data, headers=HEADERS, method="POST")

    try:
        with urllib.request.urlopen(app_req) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            print(f"[SUCCESS] Approval submitted! Result: {res_json.get('data')}")
    except Exception as e:
        print(f"[ERROR] Failed to approve campaign: {e}")
        return False

    # Wait for outreach dispatcher completion
    time.sleep(3)
    try:
        with urllib.request.urlopen(urllib.request.Request(state_url, headers=HEADERS)) as res:
            res_state = json.loads(res.read().decode("utf-8")).get("data", {})
            print(f"Final Node: {res_state.get('current_node')}")
            print(f"Receipts  : {len(res_state.get('execution', {}).get('receipts', []))} channels dispatched")
    except Exception:
        pass

    print_header(f"PIPELINE {campaign_key.upper()} COMPLETED SUCCESSFULLY")
    return True


def main():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read {JSON_FILE}: {e}")
        return

    campaigns = config_data.get("campaign_payloads", {})
    approval_data = config_data.get("approval_payload", {"review_status": "approved", "approved_variant_id": ""})

    if not campaigns:
        print("[ERROR] No campaign payloads found.")
        return

    selected_key = sys.argv[1] if len(sys.argv) > 1 else "cold_email"

    if selected_key == "all":
        print(f"Executing full coverage run for {len(campaigns)} campaign types...")
        for key, payload in campaigns.items():
            success = test_campaign_pipeline(key, payload, approval_data)
            if not success:
                print(f"[FAILED] Pipeline failed for {key}")
                break
    elif selected_key in campaigns:
        test_campaign_pipeline(selected_key, campaigns[selected_key], approval_data)
    else:
        print(f"Unknown campaign key '{selected_key}'. Available keys: {list(campaigns.keys())} or 'all'")


if __name__ == "__main__":
    main()
