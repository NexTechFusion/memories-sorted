import os
import sys
sys.path.insert(0, '/root/memories-sorted')
from clip_engine import ClipSearchEngine
from sync import MemoriesSync

syncer = MemoriesSync(base_dir='/root/memories-sorted')
clip_engine = ClipSearchEngine(model_name='RN50x4', device='cpu')

for img_entry in syncer.index.image_catalog:
    if os.path.exists(img_entry.file_path):
        print(f'Encoding: {img_entry.file_path}')
        clip_engine.ensure_embedding(img_entry.file_path)

clip_engine.save_embeddings('/root/memories-sorted/clip_vectors.npz')
print('CLIP vectors saved!')
