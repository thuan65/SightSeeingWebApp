import requests

lat = 10.8231
lon = 106.6297

query = f"""
[out:json][timeout:25];
node(around:3000,{lat},{lon})["tourism"];
out center;
"""

url = "https://overpass.kumi.systems/api/interpreter"

print("Sending request...")
res = requests.post(url, data=query, headers={"Content-Type": "text/plain"})
print("Status:", res.status_code)

try:
    data = res.json()
    print("Elements:", len(data.get("elements", [])))
    print("Sample:", data.get("elements", [])[:5])
except Exception as e:
    print("JSON decode error:", e)
    print("Raw response:", res.text[:500])
