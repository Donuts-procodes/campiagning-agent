import urllib.request
import urllib.error
import json
import time
from datetime import date
from typing import Any

API_URL = "http://localhost:8000/api/campaigns"

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def main():
    print_header("B2B OUTREACH AGENT - TERMINAL CLI")
    
    print("Select an option:")
    print("1. Launch Default Campaign (Cold Email)")
    print("2. Launch Custom Campaign")
    choice = input("Enter choice [1 or 2]: ").strip()
    
    payload: dict[str, Any] = {
        "campaign_name": "Terminal Test Campaign",
        "company_name": "Acme Corp",
        "product_service": "Cloud Storage",
        "value_proposition": "Fastest cloud storage on the market",
        "target_icp": "IT Directors at Mid-Market companies",
        "campaign_type": "cold_email",
        "duration_days": 30,
        "start_date": date.today().isoformat(),
        "business_okrs": [],
        "target_meetings": 10,
        "channels_allowed": ["email"]
    }
    
    if choice == "2":
        payload["campaign_name"] = input("Campaign Name: ") or payload["campaign_name"]
        payload["product_service"] = input("Product/Service: ") or payload["product_service"]
        payload["value_proposition"] = input("More about the Product (Value Prop): ") or payload["value_proposition"]
        payload["target_icp"] = input("Target ICP: ") or payload["target_icp"]
        
        docs_input = input("Product Docs / URLs (comma separated, optional): ")
        if docs_input:
            payload["content_assets"] = [s.strip() for s in docs_input.split(",") if s.strip()]

        case_study_input = input("Key Case Study / Proof Point (optional): ")
        if case_study_input:
            payload["case_studies"] = [case_study_input.strip()]

        tone_input = input("Brand Tone [direct_consultative / challenger / peer_founder] (default direct_consultative): ")
        if tone_input:
            payload["brand_tone"] = tone_input.strip()

        neg_input = input("Negative Constraints / Forbidden Words (comma separated, optional): ")
        if neg_input:
            payload["negative_constraints"] = [s.strip() for s in neg_input.split(",") if s.strip()]

        budget_input = input("Budget (USD, optional): ")
        if budget_input:
            try:
                payload["budget"] = float(budget_input)
            except ValueError:
                pass
                
        campaign_type = input("Campaign Type (cold_email, multi_channel, linkedin_outreach): ")
        if campaign_type:
            payload["campaign_type"] = campaign_type
            
    print_header("INITIALIZING AGENT WORKFLOW")
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json", "X-API-Key": "default_dev_key"}, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            thread_id = res_json.get("data", {}).get("thread_id")
            print(f"[SUCCESS] Workflow started! Thread ID: {thread_id}")
    except urllib.error.URLError as e:
        print(f"[ERROR] Failed to submit workflow: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode("utf-8"))
        return

    print_header("PIPELINE EXECUTION (POLLING)")
    state_url = f"{API_URL}/{thread_id}/state"
    
    while True:
        time.sleep(3)
        try:
            state_req = urllib.request.Request(state_url, headers={"X-API-Key": "default_dev_key"})
            with urllib.request.urlopen(state_req) as response:
                state_data = json.loads(response.read().decode("utf-8"))
                data = state_data.get("data", {})
                current_node = data.get("current_node")
                
                print(f"[*] Agent is currently at node: {current_node}")
                
                if current_node == "hitl_approval_node":
                    print("\n[!] AGENT PAUSED: HUMAN APPROVAL REQUIRED")
                    handle_approval(thread_id, data)
                    break
                elif current_node == "outreach_dispatcher":
                    print("\n[SUCCESS] Workflow reached final dispatch stage!")
                    break
                elif "error" in data:
                    print(f"\n[ERROR] Workflow failed: {data['error']}")
                    break
        except Exception as e:
            print(f"[ERROR] Polling failed: {e}")
            break

def handle_approval(thread_id, state_data):
    print_header("HUMAN-IN-THE-LOOP APPROVAL")
    
    strategy = state_data.get("strategy", {})
    variants = strategy.get("strategy_variants", [])
    
    if not variants:
        print("No strategy variants found in state.")
        return
        
    print("The agent has generated the following strategies:\n")
    for idx, v in enumerate(variants):
        print(f"--- Option {idx + 1} ---")
        print(f"Name: {v.get('variant_name')}")
        print(f"Angle: {v.get('messaging_angle')}")
        print(f"Est Reply Rate: {v.get('estimated_reply_rate')}")
        print(f"Req Contact Vol: {v.get('required_contact_volume')}\n")
        
    choice = input(f"Select a variant to approve [1-{len(variants)}]: ")
    try:
        idx = int(choice) - 1
        selected = variants[idx]["variant_id"]
        
        print(f"\nApproving variant: {selected}...")
        approve_url = f"{API_URL}/{thread_id}/approve"
        payload = {
            "approved_variant_id": selected,
            "human_modifications": {},
            "review_status": "approved"
        }
        req = urllib.request.Request(approve_url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "X-API-Key": "default_dev_key"}, method="POST")
        with urllib.request.urlopen(req) as response:
            print("[SUCCESS] Strategy approved! Agent is resuming execution...")
            
    except (ValueError, IndexError, urllib.error.URLError) as e:
        print(f"[ERROR] Invalid choice or submission failed: {e}")

if __name__ == "__main__":
    main()
