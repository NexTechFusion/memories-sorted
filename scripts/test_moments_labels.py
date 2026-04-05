#!/usr/bin/env python3
"""Verify moments labeling diversity after fix."""
from moments_engine import MomentsEngine
import json, os, numpy as np, sys

idx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")
with open(idx_path) as f:
    idx = json.load(f)

emb = {}
clip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clip_vectors.npz")
if os.path.exists(clip_path):
    data = np.load(clip_path)
    for k in data:
        emb[k] = data[k]

engine = MomentsEngine()
result = engine.compute_moments(idx['image_catalog'], emb, min_cluster_size=3)

labels = [m['label'] for m in result]
print("=== MOMENTS AFTER FIX ===")
for m in result:
    print(f"  {m['label']:25s} ({m['count']} photos)")

# Check diversity
unique_labels = set(labels)
print(f"\nTotal moments: {len(labels)}")
print(f"Unique labels: {len(unique_labels)}")
print(f"Labels: {labels}")
if len(unique_labels) == len(labels):
    print("PASS: All labels are unique!")
else:
    print(f"WARN: {len(labels) - len(unique_labels)} duplicate(s) remain")
    sys.exit(1)
