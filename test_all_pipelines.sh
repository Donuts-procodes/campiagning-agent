#!/usr/bin/env bash

# Test all 8 campaign families supported by the backend orchestration API.

API_URL="http://localhost:8000/api/campaigns"
TODAY=$(date +%Y-%m-%d)

echo "Starting tests for all 8 pipelines..."
echo "-------------------------------------"

echo "1) Testing: cold_email"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "Test Cold Email",
  "company_name": "Acme Corp",
  "product_service": "Cloud Storage",
  "value_proposition": "Fastest cloud storage on the market",
  "target_icp": "IT Directors at Mid-Market companies",
  "campaign_type": "cold_email",
  "duration_days": 30,
  "start_date": "'$TODAY'",
  "business_okrs": [],
  "target_meetings": 10,
  "channels_allowed": ["email"]
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "2) Testing: linkedin_outreach"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "Test LinkedIn Outreach",
  "company_name": "Acme Corp",
  "product_service": "Recruiting Software",
  "value_proposition": "Hire 3x faster with AI",
  "target_icp": "VP of HR / Talent Acquisition",
  "campaign_type": "linkedin_outreach",
  "duration_days": 14,
  "start_date": "'$TODAY'",
  "business_okrs": [],
  "channels_allowed": ["linkedin"]
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "3) Testing: abm (Account-Based Marketing)"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "Enterprise ABM Tier 1",
  "company_name": "Acme Corp",
  "product_service": "Enterprise Security",
  "value_proposition": "Zero-trust network architecture for Fortune 500",
  "target_icp": "CISOs at Fortune 500 banks",
  "campaign_type": "abm",
  "duration_days": 60,
  "start_date": "'$TODAY'",
  "target_accounts": ["JPMorgan Chase", "Bank of America", "Citigroup"],
  "business_okrs": []
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "4) Testing: product_launch_pr"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "v2.0 Product Launch",
  "company_name": "Acme Corp",
  "product_service": "Mobile App V2",
  "value_proposition": "Brand new interface and 10x faster performance",
  "target_icp": "Tech Journalists and SaaS Reviewers",
  "campaign_type": "product_launch_pr",
  "duration_days": 7,
  "start_date": "'$TODAY'",
  "launch_url": "https://acme.com/v2-launch",
  "business_okrs": []
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "5) Testing: partner_affiliate"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "Q3 Affiliate Push",
  "company_name": "Acme Corp",
  "product_service": "Acme Partner Program",
  "value_proposition": "Earn 30% recurring commission on all referrals",
  "target_icp": "Marketing Agencies and Tech Consultants",
  "campaign_type": "partner_affiliate",
  "duration_days": 45,
  "start_date": "'$TODAY'",
  "partner_profile": "B2B Consultants with >50 clients",
  "business_okrs": []
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "6) Testing: content_promotion"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "Whitepaper Distribution",
  "company_name": "Acme Corp",
  "product_service": "State of AI Report 2026",
  "value_proposition": "The most comprehensive data on enterprise AI adoption",
  "target_icp": "Chief Data Officers",
  "campaign_type": "content_promotion",
  "duration_days": 21,
  "start_date": "'$TODAY'",
  "content_assets": ["State of AI 2026 Whitepaper"],
  "business_okrs": []
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "7) Testing: retention_upsell"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "Pro Tier Upsell",
  "company_name": "Acme Corp",
  "product_service": "Acme Pro Features",
  "value_proposition": "Unlock advanced analytics and team collaboration",
  "target_icp": "Current Free Tier Users highly active in last 30 days",
  "campaign_type": "retention_upsell",
  "duration_days": 14,
  "start_date": "'$TODAY'",
  "customer_segment": "High-usage Free Tier",
  "trigger_event": "User hit 90% of free limit",
  "business_okrs": []
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "8) Testing: multi_channel"
curl -s -X POST "$API_URL" -H "Content-Type: application/json" -H "X-API-Key: default_dev_key" -d '{
  "campaign_name": "Omni-Channel Lead Gen",
  "company_name": "Acme Corp",
  "product_service": "Sales CRM",
  "value_proposition": "End-to-end sales tracking",
  "target_icp": "Sales Managers",
  "campaign_type": "multi_channel",
  "duration_days": 30,
  "start_date": "'$TODAY'",
  "channels_allowed": ["email", "linkedin", "call"],
  "business_okrs": []
}' || echo "Failed"
echo -e "\n-------------------------------------"

echo "All pipeline tests dispatched!"
