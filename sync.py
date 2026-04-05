import os
import json
import uuid
import datetime
import hashlib
from typing import List, Dict
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from sklearn.metrics.pairwise import cosine_similarity

from processor import PersonProcessor
from schemas import (
    MemoriesIndex, PersonID, FaceDetection, FaceAssignment, ImageFaces
)

class MemoriesSync:
    def __init__(self, base_dir: str = "/root/memories-sorted"):
        self.base_dir = base_dir
        self.input_dir = os.path.join(base_dir, "data/input")
        self.output_dir = os.path.join(base_dir, "data/output")
        self.thumbs_dir = os.path.join(base_dir, "data/cache/thumbs")
        self.faces_dir = os.path.join(base_dir, "data/cache/faces")
        self.blurred_dir = os.path.join(base_dir, "data/cache/blurred")
        self.index_path = os.path.join(base_dir, "index.json")
        self.clip_index_path = os.path.join(base_dir, "clip_vectors.npy")
        self.processor = PersonProcessor()
        self.index = self._load_index()

        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.thumbs_dir, exist_ok=True)
        os.makedirs(self.faces_dir, exist_ok=True)
        os.makedirs(self.blurred_dir, exist_ok=True)

    def _load_index(self) -> MemoriesIndex:
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "r") as f:
                    content = f.read().strip()
                    if not content:
                        return MemoriesIndex()
                    data = json.loads(content)
                    if data.get("version", "").startswith("v3"):
                        return _migrate_v3_to_v4(data)
                    return MemoriesIndex(**data)
            except Exception as e:
                print(f"[Sync] Warning: Failed to load index, starting fresh. {e}")
                return MemoriesIndex()
        return MemoriesIndex()

    def _save_index(self):
        tmp_path = self.index_path + ".tmp"
        with open(tmp_path, "w") as f:
            f.write(self.index.model_dump_json(indent=2))
        os.replace(tmp_path, self.index_path)

    @staticmethod
    def _extract_exif_date(file_path: str) -> str | None:
        """Read original capture date from EXIF metadata."""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            exif_tags = {
                0x9003,  # DateTimeOriginal
                0x9004,  # DateTimeDigitized
                0x0132,  # DateTime
            }
            img = Image.open(file_path)
            exif = img.getexif()
            for tag_id in exif_tags:
                val = exif.get(tag_id)
                if val and isinstance(val, str) and val.strip() not in ('', '0000:00:00 00:00:00'):
                    # Convert "2024:03:30 19:27:57" -> "2024-03-30T19:27:57"
                    cleaned = val.strip().replace(':', '-', 2)
                    cleaned = cleaned.replace(' ', 'T', 1)
                    return cleaned
        except Exception as e:
            print(f"[EXIF] Failed to read date for {file_path}: {e}")
        return None

    def _find_matching_person(self, embedding: List[float], threshold: float = 0.40) -> tuple:
        registry = self.index.person_registry
        if not registry:
            return None, 0.0
        
        person_ids = list(registry.keys())
        embeddings_matrix = np.array([p.embedding for p in registry.values()])
        current_emb = np.array([embedding])
        similarities = cosine_similarity(current_emb, embeddings_matrix)[0]
        
        best_match_idx = np.argmax(similarities)
        best_conf = float(similarities[best_match_idx])
        
        if best_conf > threshold:
            return person_ids[best_match_idx], best_conf
        
        return None, best_conf

    def sync(self):
        """Scan input directory, process new images."""
        self.index = self._load_index()  # Ensure index is fresh before starting
        cataloged_paths = {item.file_path for item in self.index.image_catalog}
        processed = 0
        
        for filename in os.listdir(self.input_dir):
            if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".heic", ".webp")):
                continue
            
            file_path = os.path.join(self.input_dir, filename)
            if file_path in cataloged_paths:
                continue
            
            print(f"[Sync] Processing {filename}...")
            detected_faces = self.processor.process_image(file_path)
            
            import cv2
            img = cv2.imread(file_path)
            h, w = img.shape[:2] if img is not None else [0, 0]
            
            captured_at = self._extract_exif_date(file_path)
            image_entry = ImageFaces(file_path=file_path, resolution=[w, h], captured_at=captured_at)
            
            for face in detected_faces:
                fd = FaceDetection(
                    bbox=face['bbox'],
                    confidence=face['score'],
                    embedding=face['embedding'],
                    _source_path=file_path
                )
                image_entry.detected_faces.append(fd)
                
                person_id, conf = self._find_matching_person(face['embedding'])
                
                if not person_id:
                    # New person — initialize with this face's embedding, count=1
                    person_id = f"PERSON_{uuid.uuid4().hex[:8].upper()}"
                    self.index.person_registry[person_id] = PersonID(
                        id=person_id,
                        embedding=face['embedding'],
                        face_count=1
                    )
                    print(f"  + New person registered: {person_id} (conf: 1.00)")
                else:
                    # Running average update — correct formula
                    pid_entry = self.index.person_registry[person_id]
                    old_emb = np.array(pid_entry.embedding)
                    new_emb = np.array(face['embedding'])
                    n = pid_entry.face_count or 1  # fallback to 1 if 0
                    avg = ((old_emb * n) + new_emb) / (n + 1)
                    pid_entry.embedding = avg.tolist()
                    pid_entry.face_count = n + 1
                    pid_entry.updated_at = datetime.datetime.now().isoformat()
                    print(f"  ~ Matched {pid_entry.display_name} (conf: {conf:.2f})")
                
                image_entry.assignments.append(FaceAssignment(
                    face_hash=fd.face_hash,
                    person_id=person_id,
                    match_confidence=conf
                ))
                
                # Save face thumbnail
                thumb_path = os.path.join(self.faces_dir, f"{fd.face_hash}.jpg")
                if not os.path.exists(thumb_path):
                    PersonProcessor.extract_face_thumbnail(file_path, face['bbox'], thumb_path)
                
                # Track best face
                current = self.index.person_registry[person_id]
                if not current.best_face_hash or fd.confidence > 0.8:
                    current.best_face_hash = fd.face_hash

            self.index.image_catalog.append(image_entry)
            self._save_index()
            processed += 1
            print(f"  - Done. Found {len(detected_faces)} faces.")
        
        print(f"[Sync] Complete. Processed {processed} new image(s).")

    def rename_person(self, person_id: str, new_name: str) -> bool:
        if person_id in self.index.person_registry:
            self.index.person_registry[person_id].name = new_name
            self.index.person_registry[person_id].updated_at = datetime.datetime.now().isoformat()
            self._save_index()
            return True
        return False

    def merge_persons(self, source_id: str, target_id: str) -> bool:
        """Merge source into target. Source's faces are reassigned."""
        if source_id not in self.index.person_registry or target_id not in self.index.person_registry:
            return False
        
        target = self.index.person_registry[target_id]
        source = self.index.person_registry[source_id]
        
        # Update target embedding to include source
        if len(target.embedding) > 0 and len(source.embedding) > 0:
            n1 = target.face_count or 1
            n2 = source.face_count or 1
            merged = ((np.array(target.embedding) * n1) + (np.array(source.embedding) * n2)) / (n1 + n2)
            target.embedding = merged.tolist()
            target.face_count = n1 + n2
        
        target.merge_sources.append(source_id)
        
        # Reassign all images
        for img in self.index.image_catalog:
            for assignment in img.assignments:
                if assignment.person_id == source_id:
                    assignment.person_id = target_id
            
            # Remove duplicates
            seen = set()
            unique = []
            for a in img.assignments:
                if a.person_id not in seen:
                    seen.add(a.person_id)
                    unique.append(a)
            img.assignments = unique
        
        # Delete source from registry
        del self.index.person_registry[source_id]
        self._save_index()
        return True

    def split_face(self, image_path: str, face_hash: str, new_person_id: str = None) -> bool:
        """Remove a face from its current person and assign to a new one."""
        img_entry = self.index.get_image(image_path)
        if not img_entry:
            return False
        
        assignment = None
        for a in img_entry.assignments:
            if a.face_hash == face_hash:
                assignment = a
                break
        
        if not assignment:
            return False
        
        old_pid = assignment.person_id
        old_person = self.index.person_registry.get(old_pid)
        if old_person:
            old_person.face_count = max(0, old_person.face_count - 1)
        
        if not new_person_id:
            new_person_id = f"PERSON_{uuid.uuid4().hex[:8].upper()}"
        
        if new_person_id not in self.index.person_registry:
            # Get embedding from face detection
            fd = next((f for f in img_entry.detected_faces if f.face_hash == face_hash), None)
            self.index.person_registry[new_person_id] = PersonID(
                id=new_person_id,
                embedding=fd.embedding if fd else [0] * 512
            )
        
        assignment.person_id = new_person_id
        assignment.match_confidence = 0.0
        
        self.index.person_registry[new_person_id].face_count = \
            self.index.person_registry[new_person_id].face_count + 1
        self._save_index()
        return True


def _migrate_v3_to_v4(v3_data: Dict) -> MemoriesIndex:
    v4 = MemoriesIndex(version="v4.0.0")
    for pid, pinfo in v3_data.get("person_registry", {}).items():
        v4.person_registry[pid] = PersonID(
            id=pid, name=pinfo.get("name"),
            embedding=pinfo.get("embedding", []),
            created_at=pinfo.get("created_at", ""),
            face_count=len([i for i in v3_data.get("image_catalog", [])
                           if pid in i.get("people_in_image", [])])
        )
    for img_entry in v3_data.get("image_catalog", []):
        v4.image_catalog.append(ImageFaces(
            file_path=img_entry["file_path"],
            analyzed_at=img_entry.get("analyzed_at", ""),
            resolution=img_entry.get("resolution"),
            detected_faces=[],
            assignments=[FaceAssignment(
                face_hash=f"mig_{i}_{uuid.uuid4().hex[:6]}",
                person_id=pid, match_confidence=0.95
            ) for i, pid in enumerate(img_entry.get("people_in_image", []))]
        ))
    return v4


if __name__ == "__main__":
    import sys
    syncer = MemoriesSync()
    
    if "--resync" in sys.argv:
        print("[Sync] Force re-sync: wiping catalog.")
        syncer.index.image_catalog = []
        syncer.index.person_registry = {}
        syncer._save_index()
    
    syncer.sync()
