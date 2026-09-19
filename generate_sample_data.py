"""Create deterministic synthetic data for local development and demos."""

from datetime import date, timedelta
from pathlib import Path
import random

import pandas as pd

random.seed(42)

ISSUES = {
    "Roads": ["large pothole near {area} crossing", "damaged road surface on {area} main road"],
    "Water": ["water leakage outside house {number} in {area}", "no water supply since morning in {area}"],
    "Waste": ["garbage has not been collected from {area}", "overflowing community bin in {area}"],
    "Streetlights": ["streetlight not working near {area} park", "dark road because lamp is broken in {area}"],
    "Electrical": ["exposed wire near {area} market", "sparks from electric pole in {area}"],
}
AREAS = ["Green Park", "Lake View", "Old Town", "Station Road", "North Ward", "East Colony"]
LANDMARKS = [
    "bus stop", "primary school", "market entrance", "community hall",
    "public park gate", "clinic", "metro exit", "temple road",
    "water tower", "playground", "library", "bank corner",
]

rows = []
today = date.today()
for i in range(1, 221):
    category = random.choice(list(ISSUES))
    area = random.choice(AREAS)
    template = random.choice(ISSUES[category])
    # A landmark makes a report location-specific. Without it, repeated generic
    # phrases in the demo data look like duplicates even when they are not.
    description = f"{template.format(area=area, number=random.randint(1, 250))} near {random.choice(LANDMARKS)}"
    rows.append(
        {
            "complaint_id": f"CMP-{i:04d}",
            "reported_at": (today - timedelta(days=random.randint(0, 35))).isoformat(),
            "area": area,
            "description": description,
            "reported_category": category if random.random() > 0.08 else "Other",
            "severity": random.randint(1, 5),
            "status": random.choices(["Open", "In progress", "Resolved"], [0.52, 0.23, 0.25])[0],
        }
    )

# Add a few genuine-looking repeated safety reports so duplicate detection is visible.
for i in range(221, 229):
    rows.append(
        {
            "complaint_id": f"CMP-{i:04d}",
            "reported_at": (today - timedelta(days=i - 220)).isoformat(),
            "area": "Station Road",
            "description": "exposed wire and sparks near Station Road bus stop",
            "reported_category": "Electrical",
            "severity": 5,
            "status": "Open",
        }
    )

output = Path(__file__).parent / "data" / "complaints.csv"
output.parent.mkdir(exist_ok=True)
pd.DataFrame(rows).to_csv(output, index=False)
print(f"Created {len(rows)} synthetic complaints at {output}")
