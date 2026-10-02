#!/usr/bin/env python3
"""
Fetch face image paths from thispersonnotexist.org API.
Builds a JSON catalog of image paths organized by race/sex/age.
"""
import json, base64, time, sys, os
from urllib.request import Request, urlopen

API = "https://thispersonnotexist.org/load-faces"

RACES = {
    'asian': 'asian',
    'indian': 'indian',
    'white': 'white',
    'latino': 'latino hispanic',
    'middle': 'middle eastern',
    'black': 'black',
}
SEXES = {'m': 'M', 'f': 'F'}
AGES = {
    'y': '1-21',
    'a': '21-35',
    'm': '34-50',
    'o': '49-100',
}

IMAGES_PER_CAT = 210
PER_CALL = 8  # API returns 8 per call


def fetch_faces(api_type, age, race):
    payload = json.dumps({
        "type": api_type,
        "age": age,
        "race": race,
        "emotion": "none",
    }).encode()
    req = Request(API, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    paths = []
    for token in data.get("fc", []):
        decoded = base64.b64decode(token[1:]).decode()  # strip leading 'A'
        paths.append(decoded)
    return paths


def main():
    out_path = os.path.join(os.path.dirname(__file__), "face_catalog.json")

    existing = {}
    if os.path.exists(out_path):
        with open(out_path) as f:
            existing = json.load(f)
        old_total = sum(len(v) for v in existing.values())
        print(f"Loaded existing catalog: {old_total} images across {len(existing)} categories")

    catalog = {}
    total_categories = len(RACES) * len(SEXES) * len(AGES)
    done = 0

    for race_key, api_race in RACES.items():
        for sex_key, api_type in SEXES.items():
            for age_key, api_age in AGES.items():
                cat_key = f"{race_key}_{sex_key}_{age_key}"
                prev = existing.get(cat_key, [])
                seen = set(prev)
                paths = list(prev)

                if len(paths) >= IMAGES_PER_CAT:
                    catalog[cat_key] = paths[:IMAGES_PER_CAT]
                    done += 1
                    print(f"[{done}/{total_categories}] {cat_key}: {len(catalog[cat_key])} images (cached)")
                    continue

                max_attempts = 40
                attempts = 0
                while len(paths) < IMAGES_PER_CAT and attempts < max_attempts:
                    try:
                        batch = fetch_faces(api_type, api_age, api_race)
                        for p in batch:
                            if p not in seen:
                                seen.add(p)
                                paths.append(p)
                        attempts += 1
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"  Error fetching {cat_key}: {e}", file=sys.stderr)
                        attempts += 1
                        time.sleep(1)

                catalog[cat_key] = paths[:IMAGES_PER_CAT]
                done += 1
                added = len(catalog[cat_key]) - len(prev)
                print(f"[{done}/{total_categories}] {cat_key}: {len(catalog[cat_key])} images (+{added} new)")

    with open(out_path, "w") as f:
        json.dump(catalog, f, separators=(",", ":"))

    total_images = sum(len(v) for v in catalog.values())
    size_kb = os.path.getsize(out_path) / 1024
    print(f"\nDone: {total_images} images across {len(catalog)} categories")
    print(f"Catalog size: {size_kb:.1f} KB -> {out_path}")


if __name__ == "__main__":
    main()
