1. osm_client.py fetches POI (points of interest) data from Overpass API.
2. places_db.py initializes the places.db SQLite database.
3. importer.py processes and inserts POI data into the database.
4. test_import.py is used to trigger the import process manually.
5. test2_overpass_raw.py for API debugging