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

        # 3. Time Gap
        timestamps = []
        for img in data.get('image_catalog', []):
            ts_str = img.get('analyzed_at', '')
            if ts_str:
                try:
                    timestamps.append(datetime.fromisoformat(ts_str))
                except:
                    pass
        
        if timestamps and len(timestamps) > 1:
            timestamps.sort()
            now = datetime.now()
            gap = now - max(timestamps)
            gap_display = f"{gap.days} days" if gap.days > 0 else f"{max(1, gap.seconds // 3600)} hours"
            insights.append({
                'type': 'status',
                'title': 'Last Memory Captured',
                'message': f"Your last photo was uploaded {gap_display} ago.\nYou have {len(timestamps)} photos in your library.",
                'icon': '📸'
            })

        # 4. Captions Summary
        captions = []
        for img in data.get('image_catalog', []):
            cap = img.get('data', {}).get('caption', '') or img.get('caption', '')
            if cap and cap != 'N/A' and len(cap) > 5:
                captions.append(cap)
        
        if captions:
            unique = list(set(captions))[:3]
            msg = "\n".join(f"• {c}" for c in unique)
            insights.append({
                'type': 'stories',
                'title': 'Recent Snapshots',
                'message': msg,
                'icon': '📝'
            })

        # 5. Total stats
        total_p = len(data.get('person_registry', {}))
        insights.append({
            'type': 'stat',
            'title': 'Your World in Numbers',
            'message': f"{total_p} unique faces. {len(data.get('image_catalog', []))} photos captured.",
            'icon': '🌍'
        })

        # Sort: stories first, then status, favorite, reminder, stat
        order = {'stories': 0, 'status': 1, 'favorite': 2, 'reminder': 3, 'stat': 4}
        return sorted(insights, key=lambda x: order.get(x.get('type', ''), 5))
