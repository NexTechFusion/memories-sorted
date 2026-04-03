"""Moments Engine v2 - Auto-cluster images into meaningful "events" using CLIP vectors and captions.
Fixes:
1. Time grouping: Since all images have the same analyzed_at, force-split by CLIP cosine similarity.
2. Labeling: Read BLIP captions from index.json and match against scene keywords.
"""

import numpy as np
from datetime import datetime
from typing import List, Dict
import os, json, time

class MomentsEngine:
    """Creates "Moments" (smart clusters) from a photo library."""

    SCENE_KEYWORDS = [
        ("Baby/Child", ["baby", "child", "kid", "daughter", "son", "holding baby"]),
        ("Pet", ["dog", "cat", "animal", "puppy", "kitten", "golden"]),
        ("Food", ["food", "dinner", "meal", "eating", "breakfast", "pizza", "cooking"]),
        ("Beach/Outdoors", ["beach", "ocean", "waves", "hiking", "mountain", "park", "forest"]),
        ("Night Life", ["night", "party", "club", "dark", "drinks"]),
        ("Bedroom/Sleep", ["bed", "sleep", "bedroom", "waking", "resting"]),
        ("Birthday/Party", ["birthday", "cake", "balloon", "celebration", "wedding"]),
        ("Travel", ["airport", "plane", "hotel", "suitcase", "vacation", "road"]),
        ("Work", ["office", "desk", "computer", "laptop", "meeting", "work"]),
        ("Sports/Active", ["gym", "running", "skateboard", "bike", "sport", "cycling"]),
    ]

    def compute_moments(
        self,
        image_catalog: List[Dict[str, str]],
        clip_embeddings: Dict[str, np.ndarray],
        min_cluster_size: int = 3
    ) -> List[Dict]:
        """
        Main entry point.
        - image_catalog: list of {"file_path": str, "analyzed_at": str} dicts
        - clip_embeddings: dict of file_path -> np.ndarray (CLIP vector)
        """
        valid_paths = [i['file_path'] for i in image_catalog if i.get('file_path') in clip_embeddings]
        
        if not valid_paths:
            return []
        
        # 1. Semantic Clustering (greedy cosine similarity) — optimized with vectorized operations
        clusters = self._greedy_cluster(valid_paths, clip_embeddings, max_size=6, min_size=min_cluster_size)
        
        # 2. Labeling & Metadata Construction — batch caption lookup with diversity
        moments = []
        mid = 0
        for cluster_paths in clusters:
            existing_labels = [m['label'] for m in moments]
            label = self._get_label(cluster_paths, existing_labels)
            try:
                ts = int(os.path.getmtime(cluster_paths[0])) if os.path.exists(cluster_paths[0]) else 0
            except (OSError, IndexError):
                ts = 0
            
            moments.append({
                'id': f'MOMENT_{mid:03d}',
                'label': label,
                'cover_image': cluster_paths[0], 
                'member_paths': cluster_paths,
                'count': len(cluster_paths),
                'created_at': datetime.now().isoformat(),
                'timestamp': ts
            })
            mid += 1
            
        return sorted(moments, key=lambda x: x.get('timestamp', 0), reverse=True)

    def _batch_load_captions(self) -> Dict[str, str]:
        """Load all captions from index.json once, return path->caption mapping."""
        captions = {}
        try:
            idx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")
            with open(idx_path) as f:
                idx = json.load(f)
            for img in idx.get("image_catalog", []):
                cap = img.get("caption") or ""
                if cap and cap != "N/A":
                    captions[img.get("file_path", "")] = cap.lower()
        except Exception:
            pass
        return captions

    def _greedy_cluster(self, paths, clip_embeddings, max_size=6, min_size=1):
        """Greedy clustering: Pick a seed, find similar ones, remove them, repeat."""
        available = set(paths)
        clusters = []
        
        # Sort by modification time to keep chronological order
        try:
            available_sorted = sorted(list(available), key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0)
        except:
            available_sorted = list(available)
            
        for seed in available_sorted:
            if seed not in available: continue
            available.remove(seed)
            
            seed_vec = clip_embeddings[seed]
            current_cluster = [seed]
            current_vecs = [seed_vec]
            
            # Grow cluster with nearest neighbors
            candidates = sorted(available)
            for cand in candidates:
                cand_vec = clip_embeddings[cand]
                # Simple centroid similarity
                centroid = np.mean(current_vecs, axis=0)
                sim = np.dot(centroid, cand_vec) / (np.linalg.norm(centroid) * np.linalg.norm(cand_vec))
                
                if sim >= 0.70: # High similarity threshold for tighter moments
                    current_cluster.append(cand)
                    current_vecs.append(cand_vec)
                    if len(current_cluster) >= max_size: break
            
            # Update availability
            for p in current_cluster:
                available.discard(p)
            
            # If cluster is too small, merge with the closest existing cluster
            if len(current_cluster) < min_size and clusters:
                best_sim = -2
                best_cluster_idx = -1
                seed_centroid = np.mean(current_vecs, axis=0)
                
                for i, cl in enumerate(clusters):
                    cl_vectors = [clip_embeddings[p] for p in cl]
                    cl_centroid = np.mean(cl_vectors, axis=0)
                    s = np.dot(seed_centroid, cl_centroid) / (np.linalg.norm(seed_centroid) * np.linalg.norm(cl_centroid))
                    if s > best_sim:
                        best_sim = s
                        best_cluster_idx = i
                        
                if best_sim > 0.6:
                    clusters[best_cluster_idx].extend(current_cluster)
                    continue
            
            clusters.append(current_cluster)
            
        return clusters

    def _find_best_label(self, paths, captions_found):
        """Find the best label for a cluster using caption analysis."""
        all_text = " ".join(captions_found) if captions_found else ""
        if not all_text.strip():
            all_text = " ".join(p.lower().replace("_", " ").replace("-", " ") for p in paths)

        # Score each keyword category
        scores = {}
        for label, keywords in self.SCENE_KEYWORDS:
            score = sum(2 if f" {kw} " in f" {all_text} " or all_text.endswith(" " + kw) or all_text.startswith(kw + " ") else (1 if kw in all_text else 0) for kw in keywords)
            if score > 0:
                scores[label] = score

        if not scores:
            return "Memory", 0

        # Return top 3 candidates
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        return ranked[0] if ranked else ("Memory", 0)

    def _get_cluster_people(self, paths: List[str]) -> List[str]:
        """Fetch unique names of people found in these photos."""
        names = set()
        try:
            idx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")
            with open(idx_path) as f:
                idx = json.load(f)
            registry = idx.get("person_registry", {})
            for path in paths:
                for img in idx.get("image_catalog", []):
                    if img.get("file_path") == path:
                        for asgn in img.get("assignments", []):
                            pid = asgn.get("person_id")
                            if pid and pid in registry:
                                name = registry[pid].get("name")
                                if name and not name.startswith("PERSON_"):
                                    names.add(name)
        except:
            pass
        return sorted(list(names))

    def _make_label_friendly(self, base_label: str, time_context: str, captions: List[str], people: List[str] = None) -> str:
        """Convert generic labels to friendly, narrative story titles."""
        
        # Collaborative naming logic
        people_str = ""
        if people:
            if len(people) > 2:
                people_str = f"{people[0]} and others"
            elif len(people) == 2:
                people_str = f"{people[0]} and {people[1]}"
            else:
                people_str = people[0]

        # Strategic overrides
        if people_str:
            if base_label == "Birthday/Party": return f"{people_str}'s Celebration"
            if base_label == "Food": return f"Meal with {people_str}"
            if base_label == "Travel": return f"Adventure with {people_str}"
            if base_label == "Baby/Child": return f"Time with {people_str}"
            if base_label == "Family": return f"Family moments with {people_str}"
            if time_context: return f"{time_context} with {people_str}"
            return f"Moments with {people_str}"

        # Standard descriptive fallback
        if captions:
            full_text = " ".join(captions)
            # Pick distinguishing terms
            distinguishing = {
                "Baby Time": ["baby", "child", "kid", "holding"],
                "Night Out": ["night", "dark", "party", "club"],
                "Family Moments": ["family", "together", "group", "sitting"],
                "Delicious Meal": ["food", "dinner", "eating", "meal"],
                "Staying Active": ["bike", "sport", "gym", "running"],
                "Great Outdoors": ["beach", "park", "mountain", "outdoor"],
            }

            for friendly, terms in distinguishing.items():
                if any(t in full_text for t in terms):
                    return friendly

            # Fallback: extract key noun
            for n in (full_text or "").split():
                if len(n) > 3 and n not in ["the", "and", "with", "has", "his", "her", "for", "smiling"]:
                    return f"{n.title()} Time"[:20]

        friendly_map = {
            "Baby/Child": "Baby Time",
            "Pet": "Pet Time",
            "Food": "Meal Time",
            "Beach/Outdoors": "Exploring Outdoors",
            "Night Life": "Night Out",
            "Bedroom/Sleep": "Rest & Relax",
            "Birthday/Party": "Celebration",
            "Travel": "Adventure",
            "Work": "Work Session",
            "Sports/Active": "Active Moments",
        }
        
        label = friendly_map.get(base_label, base_label)
        if time_context and label != "Memory":
            return f"{time_context} {label}"
        return label

    def _get_label(self, paths: List[str], existing_labels: List[str] = None) -> str:
        """Determine the moment label with narrative and people context."""
        captions_found = []
        all_text = ""

        # Load captions
        try:
            idx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")
            with open(idx_path) as f:
                idx = json.load(f)
            for path in paths:
                for img in idx.get("image_catalog", []):
                    if img.get("file_path") == path:
                        cap = img.get("caption") or ""
                        if cap and cap != "N/A":
                            all_text += " " + cap.lower()
                            captions_found.append(cap.lower())
        except Exception:
            pass

        people = self._get_cluster_people(paths)
        time_context = self._get_time_label(paths)
        first_choice, first_score = self._find_best_label(paths, captions_found)

        label = self._make_label_friendly(first_choice, time_context, captions_found, people)

        # Collision avoidance
        if existing_labels and label in existing_labels:
            if time_context and f"{time_context} {label}" not in existing_labels:
                label = f"{time_context} {label}"
            else:
                counter = 2
                while f"{label} {counter}" in existing_labels:
                    counter += 1
                label = f"{label} {counter}"

        return label

    def _make_friendly_from_caption(self, words, time_context, existing_labels):
        """Generate a distinctive label from caption keywords."""
        subjects = {
            "baby": "Baby Time", "child": "Child Time", "woman": "Family",
            "man": "Family", "family": "Family Time", "sitting": "Sitting Together",
            "holding": "Tender Moments", "cute": "Sweet Time",
            "smiling": "Happy Moments", "playing": "Play Time",
        }

        # Find best subject word
        for w in words:
            if w in subjects:
                label = subjects[w]
                if label not in existing_labels:
                    return label

        # Use a distinguishing word as label
        for w in sorted(words, key=len, reverse=True)[:5]:
            if len(w) > 3 and w not in ["the", "and", "with", "has", "his", "her", "for", "from", "ing", "wearing"]:
                label = f"{w.title()} Time"
                if label not in existing_labels:
                    return label

        return f"Memory {len(existing_labels) + 1}"

    def _get_time_label(self, paths: List[str]) -> str:
        """Determine time context from file modification times."""
        try:
            timestamps = []
            for p in paths:
                if os.path.exists(p):
                    timestamps.append(os.path.getmtime(p))
            if not timestamps:
                return ""
            ts = min(timestamps)
            hour = datetime.fromtimestamp(ts).hour
            if 5 <= hour < 9:
                return "Morning"
            elif 9 <= hour < 12:
                return "Late Morning"
            elif 12 <= hour < 17:
                return "Afternoon"
            elif 17 <= hour < 21:
                return "Evening"
            else:
                return "Night"
        except:
            return ""
