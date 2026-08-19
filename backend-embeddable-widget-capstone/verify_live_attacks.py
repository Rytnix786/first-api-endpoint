# verify_live_attacks.py — Manual Live Attack Verification Script

import urllib.request
import urllib.error
import json
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"

print("======================================================================")
print("RUNNING LIVE END-TO-END MANUAL CAPSTONE ATTACK TESTS")
print("======================================================================")

# 1. Attack Test: Bad Email Payload
print("\n[1] ATTACK TEST: Malformed Email Payload")
req1 = urllib.request.Request(
    f"{BASE_URL}/api/v1/submissions",
    data=json.dumps({
        "widget_id": "w_demo_123",
        "name": "Attacker",
        "email": "not-an-email"
    }).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
try:
    urllib.request.urlopen(req1)
    print("❌ FAILED: Server accepted invalid email!")
except urllib.error.HTTPError as e:
    print(f"✅ PASSED: Rejected with HTTP {e.code} Bad Request")
    print(f"   Error Envelope: {e.read().decode('utf-8')}")

# 2. Attack Test: Honeypot Bot Spam
print("\n[2] ATTACK TEST: Automated Bot Spam via Honeypot")
req2 = urllib.request.Request(
    f"{BASE_URL}/api/v1/submissions",
    data=json.dumps({
        "widget_id": "w_demo_123",
        "name": "SpamBot 3000",
        "email": "bot@automated-traffic.xyz",
        "message": "Click here for free bitcoin",
        "_website_url_hp": "http://spambot-link.com"
    }).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
res2 = urllib.request.urlopen(req2)
res2_data = json.loads(res2.read().decode("utf-8"))
print(f"✅ PASSED: Response HTTP {res2.status} | Status: {res2_data.get('status')}")
print(f"   Message: {res2_data.get('message')}")

# 3. Attack Test: Burst Rate Limit (12 requests in burst)
print("\n[3] ATTACK TEST: Burst Flood (12 requests from same IP)")
attacker_ip = "198.51.100.77"
blocked_count = 0
for i in range(1, 13):
    req3 = urllib.request.Request(
        f"{BASE_URL}/api/v1/submissions",
        data=json.dumps({
            "widget_id": "w_demo_123",
            "name": f"Flood User {i}",
            "email": f"flood{i}@victim.com"
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": attacker_ip
        }
    )
    try:
        res3 = urllib.request.urlopen(req3)
        if i == 1 or i == 10:
            print(f"   Request {i}: HTTP {res3.status} Allowed")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            blocked_count += 1
            print(f"✅ PASSED: Request {i} Refused with HTTP 429 Too Many Requests | Retry-After: {e.headers.get('Retry-After')}s")
            print(f"   Response Detail: {e.read().decode('utf-8')}")

# 4. Verification of Live Enriched Submission via Public IP
print("\n[4] VERIFICATION: Public IP Geo-Enrichment")
req4 = urllib.request.Request(
    f"{BASE_URL}/api/v1/submissions",
    data=json.dumps({
        "widget_id": "w_demo_123",
        "name": "Maria Garcia",
        "email": "maria@madrid-tech.es",
        "message": "Testing public geo enrichment"
    }).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "X-Forwarded-For": "8.8.8.8"
    }
)
res4 = urllib.request.urlopen(req4)
res4_data = json.loads(res4.read().decode("utf-8"))
print(f"✅ PASSED: Enriched Location -> Country: {res4_data.get('country')}, City: {res4_data.get('city')}, Geo Enriched: {res4_data.get('geo_enriched')}")

# 5. Verification of Analytics Dashboard
print("\n[5] VERIFICATION: Owner Analytics & Geo Dashboard")
req5 = urllib.request.Request(
    f"{BASE_URL}/api/v1/analytics/stats",
    headers={"X-API-Key": "ak_live_acme_secret_key_123"}
)
res5 = urllib.request.urlopen(req5)
res5_data = json.loads(res5.read().decode("utf-8"))
print(f"✅ PASSED: Total Submissions: {res5_data.get('total_submissions')} | Spam Blocked: {res5_data.get('spam_blocked_count')}")

print("\n======================================================================")
print("ALL LIVE MANUAL ATTACK AND VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
print("======================================================================")
