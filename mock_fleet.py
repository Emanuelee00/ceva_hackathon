"""Fictional but realistic car data for the dispatcher simulation — we
don't have a real per-vehicle compound inventory, so this stands in for
it. Seeded for reproducibility: the same cars appear on every run.

Compounds are real: the top origins from the FVL empty-km analysis (Le
Havre first — it's the pilot site, highest empty-share), plus Marseille.
Each car's destination is a real French city (real coordinates) but a
random pick, not a curated per-compound route — the trip shown on the map
(`trip_map.py`) is built live from whichever destinations are currently
selected, not predefined here.
"""

import random

COMPOUNDS = ["CEVA LE HAVRE", "CEVA MARCKOLSHEIM", "CEVA BLYES", "CEVA MARSEILLE"]

# Real compound coordinates, so a trip's route map can plot the origin as
# stop #1 alongside the delivery stops.
COMPOUND_COORDS = {
    "CEVA LE HAVRE": (49.4944, 0.1079),
    "CEVA MARCKOLSHEIM": (48.2333, 7.6167),
    "CEVA BLYES": (45.8167, 5.2833),
    "CEVA MARSEILLE": (43.2965, 5.3698),
}

CITIES = [
    ("Paris", 48.8566, 2.3522), ("Lyon", 45.7640, 4.8357), ("Marseille", 43.2965, 5.3698),
    ("Lille", 50.6292, 3.0573), ("Nantes", 47.2184, -1.5536), ("Strasbourg", 48.5734, 7.7521),
    ("Toulouse", 43.6047, 1.4442), ("Bordeaux", 44.8378, -0.5792), ("Rennes", 48.1173, -1.6778),
    ("Nice", 43.7102, 7.2620), ("Dijon", 47.3220, 5.0415), ("Rouen", 49.4432, 1.0993),
    ("Venissieux", 45.6974, 4.8817), ("Vitrolles", 43.4585, 5.2472),
    ("Boissy-sous-Saint-Yon", 48.5333, 2.1667), ("Chambery", 45.5646, 5.9178),
    ("Toulon", 43.1242, 5.9280), ("Cannes", 43.5528, 7.0174),
]

MODELS = [
    ("Renault Clio V", "citadine", 0.8),
    ("Peugeot 208", "citadine", 0.8),
    ("Citroen C3", "citadine", 0.8),
    ("Peugeot 508", "berline", 1.0),
    ("Renault Talisman", "berline", 1.0),
    ("Dacia Duster", "SUV", 1.3),
    ("Peugeot 3008", "SUV", 1.3),
    ("Renault Captur", "SUV", 1.3),
    ("Citroen C5 Aircross", "SUV", 1.3),
    ("Renault Master", "utilitaire", 1.8),
    ("Peugeot Expert", "utilitaire", 1.8),
]

WMI_BY_BRAND = {"Renault": "VF1", "Peugeot": "VF3", "Citroen": "VF7", "Dacia": "UU1"}

# A few explicit cars for the Marseille multi-stop route demo — one per
# stop on that route (including Marseille itself, a short local delivery).
EXTRA_CARS = [
    {"id": "VF1DEMO0000000001", "model": "Renault Clio V", "category": "citadine", "loadingRatio": 0.82,
     "destination": {"city": "Marseille", "lat": 43.2965, "lng": 5.3698}, "compoundId": "CEVA MARSEILLE", "status": "disponible"},
    {"id": "VF3DEMO0000000002", "model": "Peugeot 3008", "category": "SUV", "loadingRatio": 1.31,
     "destination": {"city": "Toulon", "lat": 43.1242, "lng": 5.9280}, "compoundId": "CEVA MARSEILLE", "status": "disponible"},
    {"id": "VF7DEMO0000000003", "model": "Citroen C3", "category": "citadine", "loadingRatio": 0.79,
     "destination": {"city": "Cannes", "lat": 43.5528, "lng": 7.0174}, "compoundId": "CEVA MARSEILLE", "status": "disponible"},
    {"id": "VF1DEMO0000000004", "model": "Renault Master", "category": "utilitaire", "loadingRatio": 1.78,
     "destination": {"city": "Nice", "lat": 43.7102, "lng": 7.2620}, "compoundId": "CEVA MARSEILLE", "status": "disponible"},
]

# A second car per stop on the same route, same destinations, but with a
# randomized model + loadingRatio (seeded, so still reproducible run to
# run) instead of hand-picked values — gives the lot builder more than one
# candidate per city.
_EXTRA_DESTINATIONS_2 = [
    ("Marseille", 43.2965, 5.3698), ("Toulon", 43.1242, 5.9280),
    ("Cannes", 43.5528, 7.0174), ("Nice", 43.7102, 7.2620),
]


def _fake_vin(rng: random.Random, model: str) -> str:
    wmi = WMI_BY_BRAND.get(model.split()[0], "VF1")
    tail = "".join(rng.choices("0123456789ABCDEFGHJKLMNPRSTUVWXYZ", k=14))
    return wmi + tail


def generate_cars(n: int = 50, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    cars = []
    for _ in range(n):
        model, category, base_ratio = rng.choice(MODELS)
        city, lat, lng = rng.choice(CITIES)
        cars.append({
            "id": _fake_vin(rng, model),
            "model": model,
            "category": category,
            "loadingRatio": round(base_ratio + rng.uniform(-0.08, 0.08), 2),
            "destination": {"city": city, "lat": lat, "lng": lng},
            "compoundId": rng.choice(COMPOUNDS),
            "status": "disponible" if rng.random() > 0.2 else "reservee",
        })
    return cars


def _generate_extra_cars_2(seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    cars = []
    for city, lat, lng in _EXTRA_DESTINATIONS_2:
        model, category, base_ratio = rng.choice(MODELS)
        cars.append({
            "id": _fake_vin(rng, model), "model": model, "category": category,
            "loadingRatio": round(base_ratio + rng.uniform(-0.08, 0.08), 2),
            "destination": {"city": city, "lat": lat, "lng": lng},
            "compoundId": "CEVA MARSEILLE", "status": "disponible",
        })
    return cars


MOCK_CARS = generate_cars() + EXTRA_CARS + _generate_extra_cars_2()
