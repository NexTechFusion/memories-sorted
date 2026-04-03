#!/usr/bin/env python3
"""Compute CLIP embeddings for ALL images in the catalog."""
import sys, os, json
sys.path.insert(0, '/root/memories-sorted')

from clip_engine import ClipSearchEngine
from sync import MemoriesSync

syncer = MemoriesSync()
clip = ClipSearchEngine(model_name="RN50x4")

# Load existing embeddings first
if os.path.exists('/root/memories-sorted/clip_vectors.npz'):
    clip.load_embeddings('/root/memories-sorted/clip_vectors.npz')

catalog = [img.file_path for img in syncer.index.image_catalog]
print(f"Total images in catalog: {len(catalog)}")
print(f"Already have embeddings: {len(clip._image_embeddings)}")

to_encode = [p for p in catalog if p not in clip._image_embeddings]
print(f"Need to encode: {len(to_encode)}")

for i, path in enumerate(to_encode):
    try:
        vec = clip.ensure_embedding(path)
        if vec is not None:
            print(f"  [{i+1}/{len(to_encode)}] OK: {os.path.basename(path)}")
        else:
            print(f"  [{i+1}/{len(to_encode)}] FAILED: {os.path.basename(path)}")
    except Exception as e:
        print(f"  [{i+1}/{len(to_encode)}] ERROR: {os.path.basename(path)} - {e}")

clip.save_embeddings('/root/memories-sorted/clip_vectors.npz')
print(f"\nTotal embeddings saved: {len(clip._image_embeddings)}")
