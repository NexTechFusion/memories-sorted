#!/usr/bin/env python3
"""Force re-sync: wipe registry and catalog, re-analyze all images with face thumbnails."""
from sync import MemoriesSync

s = MemoriesSync()
s.index.image_catalog = []
s.index.person_registry = {}
s._save_index()
print("Cleared registry and catalog.")
s.sync()
