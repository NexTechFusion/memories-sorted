"""
Memory Intelligence — Cross-Reference Observer
Generates insights like: favorite person, one-offs, time gaps, stories, total people.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter

class MemoryIntelligence:
    """Generates insight cards from the existing index.json."""
    
    def __init__(self, index_path: str = "/root/memories-sorted/index.json"):
        self.index_path = index_path
    
    def generate_insights(self) -> List[Dict]:
        """Return a list of insight cards: {type, title, message, icon, data}."""
        if not os.path.exists(self.index_path):
            return []
        with open(self.index_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return []
        
        if not data:
            return []
        
        insights = []
        
        # 1. Favorite Person
        person_counts = {}
        for pid, pinfo in data.get('person_registry', {}).items():
            raw_name = pinfo.get('name')
            if not raw_name or raw_name.startswith('PERSON_'):
                name = pid.replace('PERSON_', 'Person ')
            else:
                name = raw_name
            person_counts[name] = pinfo.get('face_count', 0)
        
        if person_counts:
            top_name, top_count = max(person_counts.items(), key=lambda x: x[1])
            msg = f"{top_name} appears in {top_count} face detections."
            top_others = sorted(person_counts.items(), key=lambda x: -x[1])[:5]
            others_str = ", ".join(f"{n}: {c}" for n, c in top_others)
            msg += f"\n\nTop people: {others_str}"
            insights.append({
                'type': 'favorite',
                'title': 'Most Photographed',
                'message': msg,
                'icon': '🏆'
            })
            
            # 2. Singletons
            singletons = [n for n, c in person_counts.items() if c <= 1]
            if singletons and len(singletons) < 10:
                insights.append({
                    'type': 'reminder',
                    'title': 'People Seen Only Once',
                    'message': f"You only caught {', '.join(singletons)} once. Maybe it is time for a reunion?",
                    'icon': '👋'
                })

        # 3. Relationship Discovery (Co-occurrence)
        relationships = Counter()
        for img in data.get('image_catalog', []):
            pids = list(set(a.get('person_id') for a in img.get('assignments', []) if a.get('person_id')))
            if len(pids) > 1:
                pids.sort()
                for i in range(len(pids)):
                    for j in range(i + 1, len(pids)):
                        relationships[(pids[i], pids[j])] += 1
        
        if relationships:
            (p1, p2), count = relationships.most_common(1)[0]
            n1 = data.get('person_registry', {}).get(p1, {}).get('name') or p1.replace('PERSON_', 'Person ')
            n2 = data.get('person_registry', {}).get(p2, {}).get('name') or p2.replace('PERSON_', 'Person ')
            insights.append({
                'type': 'relationship',
                'title': 'Dynamic Duo',
                'message': f"{n1} and {n2} are frequently captured together (seen in {count} photos).",
                'icon': '👥'
            })

        # 4. Perspective (Quality/Aesthetics)
        scores = [img.get('quality_score', 0) for img in data.get('image_catalog', []) if img.get('quality_score')]
        if scores:
            avg_score = sum(scores) / len(scores)
            best_photos = sorted(data.get('image_catalog', []), key=lambda x: x.get('quality_score', 0), reverse=True)[:3]
            highlights = []
            for bp in best_photos:
                cap = bp.get('caption') or os.path.basename(bp.get('file_path'))
                highlights.append(f"• {cap}")
            
            insights.append({
                'type': 'quality',
                'title': 'AI Highlights',
                'message': f"Your library has an average aesthetic score of {avg_score:.1f}/10.\n\nTop curated shots:\n" + "\n".join(highlights),
                'icon': '✨'
            })

        # 5. Total stats
        total_p = len(data.get('person_registry', {}))
        insights.append({
            'type': 'stat',
            'title': 'Your World in Numbers',
            'message': f"{total_p} unique faces. {len(data.get('image_catalog', []))} photos captured.",
            'icon': '🌍'
        })

        # Sort: relationships first, then quality, favorite, reminder, stat
        order = {'relationship': 0, 'quality': 1, 'favorite': 2, 'reminder': 3, 'stat': 4}
        return sorted(insights, key=lambda x: order.get(x.get('type', ''), 5))
