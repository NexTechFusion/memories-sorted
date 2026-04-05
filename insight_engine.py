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
            person_counts[pid] = pinfo.get('face_count', 0)
        
        if person_counts:
            items = list(person_counts.items())
            if items:
                top_pid, top_count = max(items, key=lambda x: x[1])
                pinfo = data.get('person_registry', {}).get(top_pid, {})
                top_name = pinfo.get('name') or top_pid.replace('PERSON_', 'Person ')
                
                msg = f"{top_name} appears in {top_count} face detections."
                top_others = sorted(person_counts.items(), key=lambda x: -x[1])[:5]
                others_list = []
                for opid, ocount in top_others:
                    oname = data.get('person_registry', {}).get(opid, {}).get('name') or opid.replace('PERSON_', 'Person ')
                    others_list.append(f"{oname}: {ocount}")
                
                msg += f"\n\nTop people: {', '.join(others_list)}"
                insights.append({
                    'type': 'favorite',
                    'title': 'Most Photographed',
                    'message': msg,
                    'icon': '🏆',
                    'action': {'type': 'person', 'id': top_pid}
                })
            
            singletons = [n for n, c in person_counts.items() if c <= 1]
            if singletons and len(singletons) < 10:
                insights.append({
                    'type': 'reminder',
                    'title': 'People Seen Only Once',
                    'message': f"You only caught {', '.join(singletons)} once. Maybe it is time for a reunion?",
                    'icon': '👋'
                })

        # 2. Relationship Discovery (Co-occurrence)
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
                'message': f"[[person:{p1}|{n1}]] and [[person:{p2}|{n2}]] are frequently captured together (seen in {count} photos).",
                'icon': '👥'
            })

        # 3. Total stats
        total_p = len(data.get('person_registry', {}))
        insights.append({
            'type': 'stat',
            'title': 'Your World in Numbers',
            'message': f"{total_p} unique faces. {len(data.get('image_catalog', []))} photos captured.",
            'icon': '🌍'
        })

        # 4. 🔥 On This Day (Memory Flashbacks)
        import datetime
        today = datetime.date.today()
        
        # USE ONLY captured_at (EXIF). fallback to analyzed_at makes everything look like "Spring 2026"
        photos_by_date = {}
        for img in data.get('image_catalog', []):
            cap = img.get('captured_at')
            if not cap:
                continue
            try:
                dt = datetime.datetime.fromisoformat(cap.replace('Z', '+00:00'))
                d = dt.date()
                if d.month == today.month and d.day == today.day and d.year < today.year:
                    years_ago = today.year - d.year
                    if years_ago not in photos_by_date:
                        photos_by_date[years_ago] = []
                    photos_by_date[years_ago].append(img)
            except:
                continue
        
        if photos_by_date:
            best_year = max(photos_by_date.keys(), key=lambda y: len(photos_by_date[y]))
            count = len(photos_by_date[best_year])
            people_ids = set()
            for img in photos_by_date[best_year]:
                for a in img.get('assignments', []):
                    if a.get('person_id'):
                        people_ids.add(a.get('person_id'))
            people_count = len(people_ids)
            insights.append({
                'type': 'memory_flashback',
                'title': f'📸 On This Day ({best_year} years ago)',
                'message': f"You captured {count} photo{'s' if count > 1 else ''} on this day in {today.year - best_year}, with {people_count} people. Relive the moment!",
                'icon': '🕰️',
                'data': {
                    'photos': [img.get('file_path') for img in photos_by_date[best_year]],
                    'years_ago': best_year
                }
            })

        # 5. 🍂 Seasonal Intelligence
        season_months = {
            'Spring': (3, 4, 5), 'Summer': (6, 7, 8),
            'Autumn': (9, 10, 11), 'Winter': (12, 1, 2)
        }
        season_names = {
            'Spring': '🌸 Spring', 'Summer': '☀️ Summer',
            'Autumn': '🍂 Autumn', 'Winter': '❄️ Winter'
        }
        season_years = {}
        
        for img in data.get('image_catalog', []):
            # ONLY use EXIF captured_at for seasonal history. Fallback to analyzed_at (today) hallucinate 2026.
            cap = img.get('captured_at')
            if not cap:
                continue
            try:
                dt = datetime.datetime.fromisoformat(cap.replace('Z', '+00:00'))
                month = dt.month
                year = dt.year
                
                # Winter logic: Dec is start of season for following year
                for s_name, s_months in season_months.items():
                    if month in s_months:
                        # Correct winter year label (Dec 23 is Winter 24)
                        if month == 12:
                            lab_year = year + 1
                        else:
                            lab_year = year
                            
                        # Ignore current year seasons to avoid 2026 hallucination
                        if lab_year >= today.year:
                            continue
                            
                        key = f"{s_name}_{lab_year}"
                        if key not in season_years:
                            season_years[key] = {'season': s_name, 'year': lab_year, 'photos': [], 'people': set()}
                        season_years[key]['photos'].append(img)
                        for a in img.get('assignments', []):
                            if a.get('person_id'):
                                season_years[key]['people'].add(a.get('person_id'))
                        break
            except:
                continue
        
        if season_years:
            # Sort by year then season index
            s_order = ['Winter', 'Spring', 'Summer', 'Autumn']
            sorted_seasons = sorted(season_years.items(), key=lambda x: (x[1]['year'], s_order.index(x[1]['season'])), reverse=True)
            best_key, best_data = sorted_seasons[0]
            photo_count = len(best_data['photos'])
            people_count = len(best_data['people'])
            season_label = season_names[best_data['season']]
            year = best_data['year']
            insights.append({
                'type': 'seasonal',
                'title': f'{season_label} {year}',
                'message': f"{photo_count} photos with {people_count} people. Your {'busiest' if photo_count > 10 else 'quiet'} season from {year}.",
                'icon': season_names[best_data['season']].split()[0],
                'data': {
                    'photos': [img.get('file_path') for img in best_data['photos'][:12]],
                    'season': best_data['season'],
                    'year': year
                }
            })

        order = {'relationship': 0, 'favorite': 1, 'reminder': 2, 'stat': 3, 'memory_flashback': 4, 'seasonal': 5}
        return sorted(insights, key=lambda x: order.get(x.get('type', ''), 5))
