#!/usr/bin/env python3
import sys, os, json, numpy as np
sys.path.insert(0, '/root/memories-sorted')
from moments_engine import MomentsEngine
from clip_engine import ClipSearchEngine
from sync import MemoriesSync

syncer = MemoriesSync()
clip = ClipSearchEngine(model_name="RN50x4")
clip.load_embeddings('/root/memories-sorted/clip_vectors.npz')

print(f"Images in catalog: {len(syncer.index.image_catalog)}")
print(f"CLIP vectors loaded: {len(clip._image_embeddings)}")

me = MomentsEngine()
catalog = [{"file_path": i.file_path, "analyzed_at": i.analyzed_at} for i in syncer.index.image_catalog]
moments = me.compute_moments(catalog, clip._image_embeddings, min_cluster_size=2)

print(f"Moments computed: {len(moments)}")
for m in moments:
    cover = os.path.basename(m['cover_image'])
    print(f"  {m['id']}: {m['label']} ({m['count']} photos) -> {cover}")

with open('/root/memories-sorted/moments.json', 'w') as f:
    json.dump(moments, f, indent=2)
print("Saved moments.json")
