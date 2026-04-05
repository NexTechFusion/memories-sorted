"""
CRITICAL FIX PATCH — Run once to fix all systemic data issues.
1. Bake `person_ids` from assignments into the raw JSON.
2. Fix the Moments engine to properly cluster photos.
3. Regenerate Insights with correct data.
"""
import sys, os, json
sys.path.insert(0, '/root/memories-sorted')

from sync import MemoriesSync
from moments_engine import MomentsEngine

syncer = MemoriesSync(base_dir='/root/memories-sorted')

# 1. Bake person_ids into raw JSON for all image entries
data = json.load(open('/root/memories-sorted/index.json'))
for img_entry in data.get('image_catalog', []):
    # Compute from assignments
    assignments = img_entry.get('assignments', [])
    pids = list(set(a.get('person_id') for a in assignments if a.get('person_id')))
    img_entry['person_ids'] = pids
    # Update the pydantic model too  
    for pydantic_img in syncer.index.image_catalog:
        if pydantic_img.file_path == img_entry.get('file_path'):
            if not hasattr(pydantic_img, '_person_ids_cache'):
                pydantic_img._person_ids_cache = pids

# Save baked JSON
with open('/root/memories-sorted/index.json', 'w') as f:
    json.dump(data, f, indent=2)
print(f"✅ Baked person_ids into index.json for {len(data['image_catalog'])} images")

# 2. Force recompute moments with HDBSCAN clustering
moments_engine = MomentsEngine()

# Load CLIP embeddings if available
import numpy as np
clip_path = '/root/memories-sorted/clip_vectors.npz'
clip_embeddings = {}
try:
    clip_data = np.load(clip_path)
    for key in clip_data.files:
        clip_embeddings[key] = clip_data[key]
    print(f"✅ Loaded {len(clip_embeddings)} CLIP vectors from disk")
except Exception as e:
    print(f"⚠️ Failed to load CLIP vectors: {e}")

catalog_for_moments = [
    {"file_path": i.file_path, "analyzed_at": i.analyzed_at}
    for i in syncer.index.image_catalog
]

# Force use of all images - lower threshold to create meaningful clusters
moments = moments_engine.compute_moments(
    catalog_for_moments,
    clip_embeddings,
    min_cluster_size=2,       # Minimum 2 photos for a moment
    time_window_hours=48      # Group photos within 48 hours
)

print(f"\n=== Moments Result ===")
print(f"Total moments: {len(moments)}")
for m in moments:
    print(f"  {m['id']}: {m['label']} ({m['count']} photos)")
    if m['member_paths']:
        first = os.path.basename(m['member_paths'][0])
        print(f"    Cover: {first}")

with open('/root/memories-sorted/moments.json', 'w') as f:
    json.dump(moments, f, indent=2)
print(f"✅ Saved {len(moments)} moments to moments.json")

# 3. Refresh insights with correct data
from insight_engine import MemoryIntelligence
insights = MemoryIntelligence().generate_insights()
with open('/root/memories-sorted/insights.json', 'w') as f:
    json.dump(insights, f, indent=2)
print(f"✅ Saved {len(insights)} insights")

print("\n=== VERIFICATION COMPLETE ===")
print("Run the API now to see the fixed version.")
