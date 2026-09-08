import urllib.request
import urllib.error
import json
import time

from datetime import date

API_URL = "http://localhost:8000/api/campaigns"
TODAY = date.today().isoformat()

payload = {
    "campaign_name": "Test Complete Output",
    "company_name": "Acme Corp",
    "product_service": "Cloud Storage",
    "value_proposition": "Fastest cloud storage on the market",
    "target_icp": "IT Directors at Mid-Market companies",
    "campaign_type": "cold_email",
    "duration_days": 30,
    "start_date": TODAY,
    "business_okrs": [],
    "target_meetings": 10,
    "channels_allowed": ["email"]
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json", "X-API-Key": "default_dev_key"}, method="POST")

print("1. Submitting dummy workflow...")
try:
    with urllib.request.urlopen(req) as response:
        res_body = response.read().decode("utf-8")
        res_json = json.loads(res_body)
        thread_id = res_json.get("data", {}).get("thread_id")
        print(f"[SUCCESS] Workflow started! Thread ID: {thread_id}")
except urllib.error.URLError as e:
    print(f"[ERROR] Failed to submit workflow: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode("utf-8"))
    exit(1)

print("\n2. Polling for state updates (waiting for LLM pods to finish)...")
state_url = f"{API_URL}/{thread_id}/state"

for attempt in range(1, 30):
    time.sleep(3)
    try:
        state_req = urllib.request.Request(state_url, headers={"X-API-Key": "default_dev_key"})
        with urllib.request.urlopen(state_req) as response:
            state_data = json.loads(response.read().decode("utf-8"))
            data = state_data.get("data", {})
            current_node = data.get("current_node")
            print(f"   [Attempt {attempt}] Current node: {current_node}")
            
            if current_node in ["hitl_approval_node", "outreach_dispatcher"] or "hitl" in data:
                print("\n[SUCCESS] Pipeline reached completion or approval stage!")
                print("\n================ COMPLETE OUTPUT STATE ================\n")
                print(json.dumps(data, indent=2))
                break
            else:
                next_nodes = data.get("next_nodes", [])
                print(f"   Waiting... Next nodes: {next_nodes}")
    except Exception as e:
        print(f"   [Attempt {attempt}] Error polling state: {e}")
else:
    print("\n⏳ Polling timed out (took too long). Fetching latest state anyway:\n")
    try:
        state_req = urllib.request.Request(state_url, headers={"X-API-Key": "default_dev_key"})
        with urllib.request.urlopen(state_req) as response:
            state_data = json.loads(response.read().decode("utf-8"))
            print(json.dumps(state_data.get("data", {}), indent=2))
    except Exception as e:
        print(e)
