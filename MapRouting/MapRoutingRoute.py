from flask import Flask, render_template, request, jsonify, Blueprint
import sqlite3
import os
from flask_login import login_required, current_user

# --- IMPORT MODULES ---
from .routing import get_route
from .multi_point_routing import find_shortest_route_multi_points
from .geocoding import geocode_address, reverse_geocode

MapRouting_bp = Blueprint("Map_Routing_System", __name__, template_folder="templates")


# ============================================================
# CẤU HÌNH ĐƯỜNG DẪN DATABASE (ĐÃ CHỈNH SỬA THEO DỮ LIỆU CỦA BẠN)
# ============================================================
def get_db_path():
    # 1. Lấy đường dẫn của file hiện tại (MapRoutingRoute.py)
    # Kết quả: ...\SightSeeingWebApp-main\MapRouting
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Đi ngược ra thư mục gốc dự án (SightSeeingWebApp-main)
    project_root = os.path.dirname(current_dir)

    # 3. Trỏ vào thư mục instance và file FlaskDatabase.db
    # Lưu ý: Mình để tên file là FlaskDatabase.db như bạn nhắn
    db_path = os.path.join(project_root, 'instance', 'FlaskDatabase.db')

    # 4. Kiểm tra xem file có tồn tại không
    if os.path.exists(db_path):
        return db_path

    # [DỰ PHÒNG] Nếu không thấy, thử tìm tên file cũ (chữ B viết hoa)
    db_path_old = os.path.join(project_root, 'instance', 'FlaskDataBase.db')
    if os.path.exists(db_path_old):
        return db_path_old

    print(f"❌ LỖI: Không tìm thấy file database tại: {db_path}")
    return db_path


def get_db_connection():
    db_path = get_db_path()
    # In ra terminal để bạn kiểm tra xem đường dẫn đúng chưa
    print(f"DEBUG DB PATH: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# CÁC ROUTE API
# ============================================================

@MapRouting_bp.route('/')
def index():
    return render_template('map.html')

# Route test để kiểm tra Blueprint hoạt động
@MapRouting_bp.route('/api/test', methods=['GET'])
def test_route():
    return jsonify({'success': True, 'message': 'MapRouting Blueprint is working!'})


@MapRouting_bp.route('/api/geocode', methods=['POST'])
def geocode():
    try:
        data = request.json
        address = data.get('address', '')
        if not address: return jsonify({'success': False, 'error': 'Address empty'}), 400
        result = geocode_address(address)
        if result: return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@MapRouting_bp.route('/api/reverse-geocode', methods=['POST'])
def reverse_geo():
    try:
        data = request.json
        lat = float(data['lat'])
        lon = float(data['lon'])
        result = reverse_geocode(lat, lon)
        if result: return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@MapRouting_bp.route('/api/route', methods=['POST'])
def calculate_route():
    try:
        data = request.json
        start_lat, start_lon = float(data['start_lat']), float(data['start_lon'])
        end_lat, end_lon = float(data['end_lat']), float(data['end_lon'])
        vehicle = data.get('vehicle', 'car')
        route_data = get_route(start_lat, start_lon, end_lat, end_lon, vehicle)
        if route_data: return jsonify({'success': True, 'route': route_data})
        return jsonify({'success': False, 'error': 'Cannot find route'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@MapRouting_bp.route('/api/multi-route', methods=['POST'])
def calculate_multi_route():
    try:
        data = request.json
        start_lat, start_lon = float(data['start_lat']), float(data['start_lon'])
        destinations = data['destinations']
        vehicle = data.get('vehicle', 'car')
        if len(destinations) < 1 or len(destinations) > 3:
            return jsonify({'success': False, 'error': 'Destinations must be 1-3'}), 400
        result = find_shortest_route_multi_points(start_lat, start_lon, destinations, vehicle)
        if result: return jsonify({'success': True, 'route': result})
        return jsonify({'success': False, 'error': 'Cannot find route'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- API FAVORITES (ĐÃ SỬA: Lấy theo User Login & Đúng DB) ---
@MapRouting_bp.route('/api/favorites', methods=['GET'])
@MapRouting_bp.route('/api/favorites/', methods=['GET'])  # Thêm route với trailing slash
def get_user_favorites():
    print(f"🔍 [FAVORITES API] Route được gọi!")
    # Kiểm tra đăng nhập thủ công để trả về JSON thay vì redirect
    try:
        # Kiểm tra an toàn hơn: kiểm tra cả is_authenticated và có id không
        if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
            print(f"❌ [FAVORITES API] User chưa đăng nhập (is_authenticated check)")
            return jsonify({'success': False, 'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401
        
        # Kiểm tra thêm: có user_id không
        if not hasattr(current_user, 'id') or not current_user.id:
            print(f"❌ [FAVORITES API] User không có ID")
            return jsonify({'success': False, 'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401
        
        print(f"✅ [FAVORITES API] User đã đăng nhập: {current_user.id}")
    except Exception as e:
        print(f"❌ [FAVORITES API] Lỗi khi kiểm tra authentication: {str(e)}")
        return jsonify({'success': False, 'error': 'Authentication error', 'code': 'AUTH_ERROR'}), 401
    conn = None
    try:
        # Lấy ID user đang đăng nhập
        user_id = current_user.id
        print(f"🔍 [FAVORITES] Đang lấy favorites cho user_id: {user_id}")

        # Kiểm tra database path
        db_path = get_db_path()
        if not os.path.exists(db_path):
            error_msg = f"Database không tồn tại tại: {db_path}"
            print(f"❌ [FAVORITES] {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500

        conn = get_db_connection()
        print(f"✅ [FAVORITES] Đã kết nối database: {db_path}")

        # Sử dụng LEFT JOIN để tránh lỗi nếu image không tồn tại
        query = """
            SELECT f.id as fav_id, i.name, i.tags, i.address 
            FROM favorites f
            LEFT JOIN images i ON f.image_id = i.id
            WHERE f.user_id = ? 
            ORDER BY f.created_at DESC
        """
        
        print(f"🔍 [FAVORITES] Đang thực thi query với user_id: {user_id}")
        favorites = conn.execute(query, (user_id,)).fetchall()
        print(f"📊 [FAVORITES] Tìm thấy {len(favorites)} favorites")

        results = []
        for fav in favorites:
            try:
                # Kiểm tra xem có dữ liệu image không
                if not fav['name']:
                    print(f"⚠️ [FAVORITES] Image không tồn tại cho fav_id: {fav['fav_id']}")
                    continue

                place_name = fav['name']
                db_address = fav['address'] if fav['address'] else None
                tags = fav['tags'] if fav['tags'] else None

                # Ưu tiên tìm tọa độ bằng địa chỉ cụ thể, nếu không có thì dùng tên
                search_query = db_address if db_address else place_name
                print(f"🔍 [FAVORITES] Đang geocode: {search_query}")

                geo_data = geocode_address(search_query)

                if geo_data:
                    results.append({
                        'id': fav['fav_id'],
                        'name': place_name,
                        'address': db_address,
                        'tags': tags,
                        'lat': geo_data['lat'],
                        'lon': geo_data['lon'],
                        'display_name': geo_data['display_name']
                    })
                    print(f"✅ [FAVORITES] Đã tìm thấy tọa độ cho: {place_name}")
                else:
                    results.append({
                        'id': fav['fav_id'],
                        'name': place_name,
                        'address': db_address,
                        'tags': tags,
                        'error': 'Không tìm thấy tọa độ'
                    })
                    print(f"⚠️ [FAVORITES] Không tìm thấy tọa độ cho: {place_name}")
            except Exception as e:
                print(f"❌ [FAVORITES] Lỗi khi xử lý favorite {fav.get('fav_id', 'unknown')}: {str(e)}")
                continue

        print(f"✅ [FAVORITES] Trả về {len(results)} kết quả")
        return jsonify({'success': True, 'data': results})

    except sqlite3.Error as e:
        error_msg = f"Lỗi database: {str(e)}"
        print(f"❌ [FAVORITES] {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500
    except Exception as e:
        error_msg = f"Lỗi không xác định: {str(e)}"
        print(f"❌ [FAVORITES] {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500
    finally:
        if conn:
            conn.close()
            print(f"🔒 [FAVORITES] Đã đóng kết nối database")