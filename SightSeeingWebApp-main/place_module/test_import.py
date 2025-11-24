print("TEST_IMPORT RUNNING…")

from importer import import_places

count = import_places("Ho Chi Minh", radius_km=3)
print("Added:", count)
