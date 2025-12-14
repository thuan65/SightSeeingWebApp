# MapRoutingRoute.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db  # Import db của SQLAlchemy
from models import Favorite, Image  # Import Models đã định nghĩa ở Bước 1

# --- IMPORT MODULES ---
from .routing import get_route
from .multi_point_routing import find_shortest_route_multi_points
from .geocoding import geocode_address, reverse_geocode

MapRouting_bp = Blueprint("Map_Routing_System", __name__, template_folder="templates")


# ============================================================
# CÁC ROUTE API
# ============================================================

@MapRouting_bp.route('/')
def index():
    return render_template('map.html')


@MapRouting_bp.route('/api/test', methods=['GET'])
def test_route():
    return jsonify({'success': True, 'message': 'MapRouting Blueprint is working!'})


# --- Geocoding Routes ---
@MapRouting_bp.route('/api/geocode', methods=['POST'])
def geocode():
    data = request.json
    address = data.get('address')
    if not address:
        return jsonify({'success': False, 'error': 'Address empty'}), 400

    result = geocode_address(address)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Not found'}), 404


@MapRouting_bp.route('/api/reverse-geocode', methods=['POST'])
def reverse_geo():
    data = request.json
    try:
        lat, lon = float(data['lat']), float(data['lon'])
        result = reverse_geocode(lat, lon)
        if result:
            return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except (KeyError, ValueError) as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# --- Routing Routes ---
@MapRouting_bp.route('/api/route', methods=['POST'])
def calculate_route():
    try:
        data = request.json
        route_data = get_route(
            float(data['start_lat']), float(data['start_lon']),
            float(data['end_lat']), float(data['end_lon']),
            data.get('vehicle', 'car')
        )
        if route_data:
            return jsonify({'success': True, 'route': route_data})
        return jsonify({'success': False, 'error': 'Cannot find route'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@MapRouting_bp.route('/api/multi-route', methods=['POST'])
def calculate_multi_route():
    try:
        data = request.json
        destinations = data.get('destinations', [])
        if not (1 <= len(destinations) <= 3):
            return jsonify({'success': False, 'error': 'Destinations must be 1-3'}), 400

        result = find_shortest_route_multi_points(
            float(data['start_lat']), float(data['start_lon']),
            destinations,
            data.get('vehicle', 'car')
        )
        if result:
            return jsonify({'success': True, 'route': result})
        return jsonify({'success': False, 'error': 'Cannot find route'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- API FAVORITES (ĐÃ CHUẨN HÓA DÙNG ORM) ---
@MapRouting_bp.route('/api/favorites', methods=['GET'])
def get_user_favorites():
    # 1. Kiểm tra đăng nhập
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401

    try:
        # 2. Query dữ liệu
        favorites = (
            db.session.query(Favorite, Image)
            .join(Image, Favorite.image_id == Image.id)
            .filter(Favorite.user_id == current_user.id)
            .order_by(Favorite.created_at.desc())
            .all()
        )

        results = []
        print(f"📊 [FAVORITES] Tìm thấy {len(favorites)} mục cho User {current_user.id}")

        for fav, img in favorites:
            # --- CŨ (XÓA BỎ) ---
            # search_query = img.address if img.address else img.name
            # geo_data = geocode_address(search_query)
            # -------------------

            # --- MỚI (DÙNG TRỰC TIẾP DB) ---
            item = {
                'id': fav.id,
                'name': img.name,
                'address': img.address, # Vẫn gửi address để hiển thị text trên UI
                'tags': img.tags
            }

            # Kiểm tra xem trong DB đã có tọa độ chưa
            if img.latitude is not None and img.longitude is not None:
                item.update({
                    'lat': img.latitude,
                    'lon': img.longitude,
                    'display_name': img.name # Hoặc dùng address nếu muốn
                })
            else:
                # Trường hợp dữ liệu cũ chưa chạy tool update tọa độ
                item['error'] = 'Chưa cập nhật tọa độ trong hệ thống'

            results.append(item)

        return jsonify({'success': True, 'data': results})

    except Exception as e:
        print(f"❌ [FAVORITES] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500