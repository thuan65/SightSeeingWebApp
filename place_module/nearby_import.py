# place_module/nearby_import.py
import requests
from flask import Blueprint, request, jsonify, render_template
import time
import unicodedata
from createDataBase import Session
from models import Image
from extensions import db

UA = {"User-Agent": "Mozilla/5.0"}
CACHE = {}
CACHE_TTL = 3600  # 1 hour cache

nearby_import_bp = Blueprint("nearby_import_bp", __name__, template_folder="htmltemplates")


# =========================================================
# 0. Normalize text
# =========================================================
def normalize(text):
    """Remove Vietnamese accents & lowercase."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().strip()


# =========================================================
# 1. Smart City Mapping - Support all 63 provinces/cities
# =========================================================
CITY_ALIAS = {
    # TP Hồ Chí Minh
    "hcm": "Ho Chi Minh City", "hochiminh": "Ho Chi Minh City",
    "ho chi minh": "Ho Chi Minh City", "tp hcm": "Ho Chi Minh City",
    "tphcm": "Ho Chi Minh City", "sai gon": "Ho Chi Minh City",
    "saigon": "Ho Chi Minh City", "ho chi minh city": "Ho Chi Minh City",
    "hcmc": "Ho Chi Minh City", "sàigòn": "Ho Chi Minh City",
    
    # Hà Nội
    "hanoi": "Hanoi", "ha noi": "Hanoi", "hn": "Hanoi", "hà nội": "Hanoi",
    
    # Đà Nẵng
    "danang": "Da Nang", "da nang": "Da Nang", "dn": "Da Nang",
    "đà nẵng": "Da Nang",
    
    # Hải Phòng
    "haiphong": "Hai Phong", "hai phong": "Hai Phong", "hải phòng": "Hai Phong",
    
    # Cần Thơ
    "cantho": "Can Tho", "can tho": "Can Tho", "cần thơ": "Can Tho",
    
    # Các tỉnh khác
    "hue": "Hue", "huế": "Hue",
    "nha trang": "Nha Trang", "khanh hoa": "Khanh Hoa", "khánh hòa": "Khanh Hoa",
    "vung tau": "Vung Tau", "vũng tàu": "Vung Tau", "ba ria": "Ba Ria Vung Tau",
    
    # Bắc Bộ
    "hai duong": "Hai Duong", "hải dương": "Hai Duong",
    "thai nguyen": "Thai Nguyen", "thái nguyên": "Thai Nguyen",
    "cao bang": "Cao Bang", "cao bằng": "Cao Bang",
    "lang son": "Lang Son", "lạng sơn": "Lang Son",
    "bac kan": "Bac Kan", "bắc kạn": "Bac Kan",
    "tuyen quang": "Tuyen Quang", "tuyên quang": "Tuyen Quang",
    "yen bai": "Yen Bai", "yên bái": "Yen Bai",
    "lao cai": "Lao Cai", "lào cai": "Lao Cai",
    "dien bien": "Dien Bien", "điện biên": "Dien Bien",
    "son la": "Son La", "sơn la": "Son La",
    "hoa binh": "Hoa Binh", "hòa bình": "Hoa Binh",
    "phu tho": "Phu Tho", "phú thọ": "Phu Tho",
    "vinh phuc": "Vinh Phuc", "vĩnh phúc": "Vinh Phuc",
    "bac giang": "Bac Giang", "bắc giang": "Bac Giang",
    "bac ninh": "Bac Ninh", "bắc ninh": "Bac Ninh",
    "ninh binh": "Ninh Binh", "ninh bình": "Ninh Binh",
    
    # Trung Bộ
    "thanh hoa": "Thanh Hoa", "thanh hóa": "Thanh Hoa",
    "nghe an": "Nghe An", "nghệ an": "Nghe An",
    "ha tinh": "Ha Tinh", "hà tĩnh": "Ha Tinh",
    "quang binh": "Quang Binh", "quảng bình": "Quang Binh",
    "quang tri": "Quang Tri", "quảng trị": "Quang Tri",
    "thua thien": "Thua Thien Hue", "thừa thiên": "Thua Thien Hue",
    "quang nam": "Quang Nam", "quảng nam": "Quang Nam",
    "quang ngai": "Quang Ngai", "quảng ngãi": "Quang Ngai",
    "binh dinh": "Binh Dinh", "bình định": "Binh Dinh",
    "phu yen": "Phu Yen", "phú yên": "Phu Yen",
    "dak lak": "Dak Lak", "đắk lắk": "Dak Lak",
    "dak nong": "Dak Nong", "đắk nông": "Dak Nong",
    "lam dong": "Lam Dong", "lâm đồng": "Lam Dong",
    
    # Tây Nguyên
    "kon tum": "Kon Tum",
    "gia lai": "Gia Lai",
    
    # Nam Bộ
    "long an": "Long An",
    "tien giang": "Tien Giang", "tiền giang": "Tien Giang",
    "ben tre": "Ben Tre", "bến tre": "Ben Tre",
    "tra vinh": "Tra Vinh", "trà vinh": "Tra Vinh",
    "vinh long": "Vinh Long", "vĩnh long": "Vinh Long",
    "hau giang": "Hau Giang", "hậu giang": "Hau Giang",
    "soc trang": "Soc Trang", "sóc trăng": "Soc Trang",
    "bac lieu": "Bac Lieu", "bạc liêu": "Bac Lieu",
    "ca mau": "Ca Mau", "cà mau": "Ca Mau",
    
    # Kiên Giang
    "kien giang": "Kien Giang", "kiên giang": "Kien Giang",
    "an giang": "An Giang",
    "dong thap": "Dong Thap", "đồng tháp": "Dong Thap",
}

def normalize_city(query: str):
    """Convert messy user input → official city name."""
    q = normalize(query)
    if q in CITY_ALIAS:
        return CITY_ALIAS[q]
    q2 = q.replace(" ", "")
    if q2 in CITY_ALIAS:
        return CITY_ALIAS[q2]
    return query.title()


# =========================================================
# 2. Geocode city
# =========================================================
def geocode_city(query):
    """Get lat/lon from city name"""
    city = normalize_city(query)
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{city}, Vietnam",
        "format": "json",
        "limit": 1
    }
    
    try:
        r = requests.get(url, params=params, headers=UA, timeout=5)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"[ERROR] Geocoding failed: {e}")
    
    return None, None


def get_address_vietnamese(lat, lon):
    """Get Vietnamese address from lat/lon using reverse geocoding"""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "json",
            "lat": lat,
            "lon": lon,
            "zoom": 18,
            "addressdetails": 1,
            "accept-language": "vi"
        }
        r = requests.get(url, params=params, headers=UA, timeout=3)
        data = r.json()
        
        # Try to get Vietnamese address with specific details
        if "address" in data:
            addr = data["address"]
            
            # Build address string from parts - prioritize specificity
            parts = []
            
            # Order: more specific → general
            priority_keys = [
                "house_number", "road", "street",
                "village", "hamlet", "suburb", "neighbourhood",
                "town", "city",
                "district", "county",
                "province", "state"
            ]
            
            for key in priority_keys:
                if key in addr and addr[key]:
                    part = addr[key].strip()
                    if part and part.lower() not in [p.lower() for p in parts]:
                        parts.append(part)
                    if len(parts) >= 3:  # Max 3 parts for conciseness
                        break
            
            if parts:
                return ", ".join(parts)
        
        # Fallback: try display_name
        if "display_name" in data:
            name = data["display_name"]
            # Extract first meaningful part
            parts = name.split(",")
            if len(parts) >= 2:
                return ", ".join(parts[:2]).strip()
    
    except Exception as e:
        print(f"[REVERSE GEOCODE] {e}")
    
    # Final fallback - just coordinates
    return None


# =========================================================
# 3. Filter SPAM - VERY STRICT garbage filtering
# =========================================================
BAD_KEYWORDS = [
    # Cờ, kỷ niệm vật, tượng, đại
    "flag", "cờ", "monument", "statue", "tượng", "memorial", "đài tưởng niệm",
    "south vietnam", "north vietnam", "french indochina",
    "historical region", "historical country",
    
    # Xã, phường, tỉnh thành (generic)
    "unnamed", "no name", "point", "spot", "place",
    "building", "house", "shop", "store", "office", "townhouse",
    "residential", "commercial", "industrial", "warehouse", "factory",
    "parking", "garage", "fuel", "gas", "atm", "bank", "post", "telephone",
    "street", "road", "lane", "path", "highway", "railway", "bridge", "cầu",
    "cemetery", "grave", "mộ", "hy sinh", "tử trận", "thanh niên",
    "entrance", "exit", "corner", "intersection", "junction", "crossing",
    "bus stop", "station", "depot", "platform",
    "apartment", "condo", "flat", "dormitory", "hostel", "hotel",
    "private", "closed", "demolish", "ruin", "abandoned",
    "school", "trường", "cao đẳng", "đại học", "trung học",
    "hospital", "clinic", "bệnh viện", "phòng khám",
    "police", "fire", "cảnh sát", "công an",
    "commune", "district", "province", "xã", "huyện", "tỉnh",
    "thôn", "ấp", "làng",
]

def is_spam(name):
    """Check if place name is spam/garbage - VERY STRICT"""
    if not name or len(name.strip()) < 3:
        return True
    
    name_lower = name.lower().strip()
    
    # Skip very short names
    if len(name_lower) < 3:
        return True
    
    # Skip if less than 2 letters
    letter_count = sum(1 for c in name_lower if c.isalpha())
    if letter_count < 2:
        return True
    
    # Check bad keywords - EXACT match on word boundaries
    for kw in BAD_KEYWORDS:
        if kw.lower() == name_lower or f" {kw.lower()} " in f" {name_lower} ":
            return True
        if kw.lower() in name_lower and len(kw) > 4:  # For longer keywords, partial match
            return True
    
    # Skip if mostly digits
    digit_ratio = sum(1 for c in name if c.isdigit()) / len(name) if name else 0
    if digit_ratio > 0.4:
        return True
    
    # Skip if name is just numbers with punctuation
    if all(c.isdigit() or c in '.,/-' for c in name):
        return True
    
    # Skip names with too many special characters
    special_count = sum(1 for c in name if not c.isalnum() and c != ' ')
    if special_count > len(name) * 0.3:
        return True
    
    return False


# =========================================================
# 4. Fetch Wikipedia Landmarks - FAST with parallel image fetch
# =========================================================
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_wiki_landmarks(lat, lon, radius=2500, limit=20):
    """Get landmarks from Wikipedia Geosearch - FAST"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": radius,
        "gslimit": limit
    }
    
    print(f"[INFO] Fetching Wikipedia landmarks around: ({lat:.4f}, {lon:.4f}), radius: {radius}m")
    
    try:
        r = requests.get(url, params=params, headers=UA, timeout=5)
        items = r.json().get("query", {}).get("geosearch", [])
        
        results = []
        
        # Parallel fetch of images
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {}
            
            for item in items:
                name = item.get("title", "").strip()
                
                # Filter spam first (before fetching image)
                if is_spam(name):
                    continue
                
                pageid = item["pageid"]
                lat_f = float(item["lat"])
                lon_f = float(item["lon"])
                
                # Submit image fetch task
                future = executor.submit(fetch_wiki_thumbnail_safe, pageid, name, lat_f, lon_f)
                future_to_item[future] = (name, lat_f, lon_f)
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                name, lat_f, lon_f = future_to_item[future]
                try:
                    image_url, address = future.result()
                    results.append({
                        "name": str(name),
                        "lat": lat_f,
                        "lon": lon_f,
                        "image_url": image_url,
                        "address": address or f"{lat_f:.4f}, {lon_f:.4f}"
                    })
                except Exception as e:
                    print(f"[WARN] Failed to fetch for {name}: {e}")
        
        print(f"[INFO] Found {len(results)} valid landmarks after filtering")
        return results
    
    except Exception as e:
        print(f"[ERROR] Wiki fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def save_place_to_db(place):
    try:
        # Tránh trùng (nếu đã có tên này trong DB)
        exists = db.session.query(Image).filter_by(name=place["name"]).first()
        if exists:
            return

        img = Image(
            name=place["name"],
            tags="nearby",
            filename=place["image_url"],
            description="Địa điểm nhập tự động",
            rating=0,
            rating_count=1,
            address=place["address"]   # <── quan trọng
        )
        db.session.add(img)
        db.session.commit()
    except Exception as e:
        print("DB error:", e)
        db.session.rollback()

def fetch_wiki_thumbnail_safe(pageid, name, lat, lon):
    """Safe wrapper to fetch image + address in parallel"""
    image_url = fetch_wiki_thumbnail(pageid, name)
    address = get_address_vietnamese(lat, lon)
    return image_url, address


# =========================================================
# 5. Fetch Wikipedia Thumbnail - Multiple sources
# =========================================================
def fetch_wiki_thumbnail(pageid, name):
    """Get image from Wikipedia - validates image exists"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "pageids": pageid,
        "prop": "pageimages",
        "pithumbsize": 500
    }
    
    try:
        r = requests.get(url, params=params, headers=UA, timeout=4)
        pages = r.json().get("query", {}).get("pages", {})
        page = pages.get(str(pageid), {})
        
        if "thumbnail" in page:
            img_url = page["thumbnail"]["source"]
            # Validate it's a real image URL
            if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                print(f"[OK] Got Wiki image for: {name}")
                return str(img_url)
    except Exception as e:
        print(f"[WARN] Wiki thumbnail fetch failed for {name}: {e}")
    
    # Fallback: Try Wikimedia Commons directly
    return get_commons_image(name)


# =========================================================
# 6. Fallback: Get image from Wikimedia Commons
# =========================================================
def get_commons_image(name):
    """Search Wikimedia Commons for real images"""
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": name,
            "srnamespace": "6",  # File namespace
            "format": "json",
            "srlimit": 3
        }
        r = requests.get(url, params=params, headers=UA, timeout=3)
        results = r.json().get("query", {}).get("search", [])
        
        if results:
            file_title = results[0]["title"]
            # Get image from file
            img_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{file_title}?width=500"
            print(f"[OK] Got Commons image for: {name}")
            return str(img_url)
    except Exception as e:
        print(f"[WARN] Commons fetch failed for {name}: {e}")
    
    # Final fallback - generic tourism image
    print(f"[FALLBACK] Using generic image for: {name}")
    return "https://source.unsplash.com/500x400/?vietnam,landmark,tourism"


# =========================================================
# 7. API Route - MAIN
# =========================================================
@nearby_import_bp.route("/import_nearby", methods=["GET"])
def api_import_nearby():
    city_raw = request.args.get("city", "").strip()
    
    if not city_raw:
        return jsonify({"error": "Vui lòng nhập tên thành phố"}), 400
    
    # Check cache
    cache_key = f"city_{normalize_city(city_raw)}"
    if cache_key in CACHE:
        cache_time, data = CACHE[cache_key]
        if time.time() - cache_time < CACHE_TTL:
            print(f"[CACHE] Using cached data for: {city_raw}")
            resp = jsonify(data)
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            return resp
    
    # Geocode
    print(f"[INFO] Geocoding: {city_raw}")
    lat, lon = geocode_city(city_raw)
    if not lat:
        error_resp = jsonify({"error": f"Không tìm thấy tọa độ cho '{city_raw}'"})
        error_resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_resp, 404
    
    try:
        # Fetch landmarks - AUTO 2.5KM radius
        print(f"[INFO] Fetching landmarks for {city_raw} at ({lat:.4f}, {lon:.4f})")
        places = fetch_wiki_landmarks(lat, lon, radius=2500, limit=30)
        for p in places:
            save_place_to_db(p)

        
        if not places:
            error_resp = jsonify({"error": f"Không tìm thấy địa danh nào tại '{city_raw}'"})
            error_resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            return error_resp, 404
        
        # Cache result - ensure JSON serializable
        result_data = {
            "total": len(places),
            "city": normalize_city(city_raw),
            "places": places
        }
        CACHE[cache_key] = (time.time(), result_data)
        
        resp = jsonify(result_data)
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp
    
    except Exception as e:
        print(f"[ERROR] API Error: {e}")
        import traceback
        traceback.print_exc()
        error_resp = jsonify({"error": f"Lỗi server: {str(e)}"})
        error_resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_resp, 500


# =========================================================
# 8. Test UI
# =========================================================
@nearby_import_bp.route("/import_nearby_test")
def import_nearby_test():
    return render_template("nearby_import_test.html")
