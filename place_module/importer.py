# place_module/importer.py
from osm_client import fetch_osm_places
from places_db import get_conn, init_db

def import_places(city: str, radius_km=5):
    init_db()
    places = fetch_osm_places(city, radius_km)
    if not places:
        print("[importer] No data from OSM")
        return 0
    
    conn = get_conn()
    cur = conn.cursor()
    added = 0

    for p in places:
        cur.execute(
            "SELECT id FROM places WHERE name=? AND city=?",
            (p["name"], city)
        )
        if cur.fetchone():
            continue

        cur.execute("""
        INSERT INTO places(name, city, description, rating, tags, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            p["name"], city, p["description"], p["rating"],
            p["tags"], p["lat"], p["lon"]
        ))
        added += 1

    conn.commit()
    conn.close()
    return added
