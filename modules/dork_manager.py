import json
from pathlib import Path

DORKS_PATH = Path(__file__).parent.parent / "data" / "dorks.json"

class DorkManager:
    def __init__(self):
        self.dorks = self._load()

    def _load(self):
        with open(DORKS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self):
        with open(DORKS_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.dorks, f, indent=2)

    def get_all(self):
        return self.dorks

    def get_by_category(self, category):
        return [d for d in self.dorks if d['category'] == category]

    def get_by_id(self, dork_id):
        for d in self.dorks:
            if d['id'] == dork_id:
                return d
        return None

    def add_dork(self, query, category, description, risk_level):
        new_id = f"u{len(self.dorks)+1:03d}"
        dork = {
            "id": new_id,
            "query": query,
            "category": category,
            "description": description,
            "risk_level": risk_level,
            "source": "user",
            "date_added": "today"
        }
        self.dorks.append(dork)
        self.save()
        return dork

    def list_categories(self):
        return sorted(set(d['category'] for d in self.dorks))
