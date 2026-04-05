# Quick test script
import requests
import os
import json

BASE_URL = "http://localhost:8373"

# 1. Test the index
idx = requests.get(f"{BASE_URL}/api/index").json()
print(f"📊 Found {len(idx.get('person_registry',{}))} people")
people = list(idx.get('person_registry', {}).keys())
if not people:
    print("❌ No people found!")
    exit()
    
target_id = people[0]
print(f"🧑 Testing Timeline for: {target_id}")

# 2. Test timeline endpoint
timeline = requests.get(f"{BASE_URL}/api/timeline/{target_id}").json()
print(f"📅 Person: {timeline.get('person_name')}")
print(f"🖼️  Photos found: {len(timeline.get('photos', []))}")

if timeline.get('photos'):
    print("✅ Timeline working!")
    for p in timeline['photos'][:2]:
        print(f"   - {p['filename']} (ts: {p['timestamp']})")
else:
    print("❌ Timeline empty. Checking why...")
    # Check index assignments
    cat = idx.get('image_catalog', [])
    for img in cat:
        for asn in img.get('assignments', []):
            if asn.get('person_id') == target_id:
                print(f"   Found assignment for {target_id} in {img['file_path']}")
                break
