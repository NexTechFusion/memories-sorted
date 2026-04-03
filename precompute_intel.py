import sys, os, json, datetime
sys.path.insert(0, '/root/memories-sorted')
from sync import MemoriesSync
from quality_engine import QualityScorer
from caption_engine import CaptionEngine

s = MemoriesSync()
qs = QualityScorer()
cap = CaptionEngine()

print("=== Phase 1.5 Intelligence Pre-computation ===")
print(f"Scanning {len(s.index.image_catalog)} images...")

q_done, c_done = 0, 0
for img in s.index.image_catalog:
    fp = img.file_path
    if img.data.get('quality_score', 0) <= 0:
        img.data['quality_score'] = qs.score(fp)
        q_done += 1
        print(f"  Scored: {os.path.basename(fp)} → {img.data['quality_score']}")
    if not img.data.get('caption') or img.data.get('caption') == 'N/A':
        img.data['caption'] = cap.caption(fp)
        c_done += 1
        print(f"  Captioned: {os.path.basename(fp)} → '{img.data['caption']}'")

s._save_index()
print(f"\nDone: Scored {q_done} images, Captioned {c_done} images.")
