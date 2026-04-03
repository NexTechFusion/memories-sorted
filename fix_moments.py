#!/usr/bin/env python3
"""Manual moments trigger for fixing empty moments tab."""
import sys, os, json, numpy as np
sys.path.insert(0, '/root/memories-sorted')

from moments_engine import MomentsEngine
from clip_engine import ClipSearchEngine
from sync import MemoriesSync
from clip_vectors import CLIP_PATH as CP

syncer = MemoriesSync()
clip = ClipSearchEngine(model_name="RN50x4")

FIX: Add this
clip.load_embeddings('/root/memories-sorted/clip_vectors.npz')

print(f"[FIX] Images in catalog: {len(syncer.index.image_catalog)}")
print(f"[FIX] CLIP vectors loaded: {len(clip._image_embeddings)}")

me = MomentsEngine()
catalog = [{"file_path": i.file_path, "analyzed_at": i.analyzed_at for i in syncer.index.image_catalog]
moments = me.compute_moments(catalog, clip._image_embeddings, min_cluster_size=2)

print(f"[FIX] Moments computed: {len(moments)}")
for m in moments:
cover = os.path.basename(m['cover_image'])
print(f"  [OK] {m['id']}: \"{m['label']}\" ({m['count']} photos) -> {cover}")moments_path = '/root/memories-sorted/moments.json'
with open(moments_path, 'w') as f:
json.dump(moments, f, indent=2)
print(f"[FIX] Saved moments to {moments_path}")
