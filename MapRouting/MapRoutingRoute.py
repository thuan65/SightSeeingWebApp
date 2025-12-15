# MapRoutingRoute.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Favorite, Image

# --- IMPORT MODULES MỚI (Đã cập nhật logic biên giới) ---
from .routing import get_route
from .multi_point_routing import find_shortest_route_multi_points
from .geocoding import geocode_address, reverse_geocode
from .vietnam_boundary import is_in_vietnam  # <--- THÊM IMPORT NÀY

MapRouting_bp = Blueprint("Map_Routing_System", __name__, template_folder="templates")


@MapRouting_bp.route('/')
def index():
    return render_template('map.html')


# ... (Giữ nguyên các API geocode/test cũ) ...

@MapRouting_bp.route('/api/geocode', methods=['POST'])
def geocode():
    # ... (Giữ nguyên code cũ) ...
    data = request.json
    address = data.get('address')
    if not address: return jsonify({'success': False, 'error': 'Address empty'}), 400
    result = geocode_address(address)
    if result: return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Not found'}), 404


@MapRouting_bp.route('/api/reverse-geocode', methods=['POST'])
def reverse_geo():
    # ... (Giữ nguyên code cũ) ...
    data = request.json
    try:
        lat, lon = float(data['lat']), float(data['lon'])
        result = reverse_geocode(lat, lon)
        if result: return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# --- CẬP NHẬT ROUTING API ĐỂ DÙNG LOGIC MỚI ---
@MapRouting_bp.route('/api/route', methods=['POST'])
def calculate_route():
    try:
        data = request.json
        # Hàm get_route này giờ đã thông minh hơn (tự đi đường ven biển nếu cần)
        route_data = get_route(
            float(data['start_lat']), float(data['start_lon']),
            float(data['end_lat']), float(data['end_lon']),
            data.get('vehicle', 'car')
        )

        if route_data:
            return jsonify({'success': True, 'route': route_data})
        return jsonify({'success': False, 'error': 'Không tìm thấy đường đi hợp lệ trong lãnh thổ VN'}), 400
    except Exception as e:
        print(f"Routing Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@MapRouting_bp.route('/api/multi-route', methods=['POST'])
def calculate_multi_route():
    try:
        data = request.json
        destinations = data.get('destinations', [])
        # ... (Giữ nguyên logic gọi hàm)
        result = find_shortest_route_multi_points(
            float(data['start_lat']), float(data['start_lon']),
            destinations,
            data.get('vehicle', 'car')
        )
        if result:
            return jsonify({'success': True, 'route': result})
        return jsonify({'success': False, 'error': 'Cannot optimize route'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- CẬP NHẬT API FAVORITES ---
@MapRouting_bp.route('/api/favorites', methods=['GET'])
def get_user_favorites():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        favorites = (
            db.session.query(Favorite, Image)
            .join(Image, Favorite.image_id == Image.id)
            .filter(Favorite.user_id == current_user.id)
            .order_by(Favorite.created_at.desc())
            .all()
        )

        results = []
        for fav, img in favorites:
            item = {
                'id': fav.id,
                'name': img.name,
                'address': img.address,
                'tags': img.tags,
                'valid_location': True,  # Mặc định
                'warning': None
            }

            if img.latitude is not None and img.longitude is not None:
                item['lat'] = img.latitude
                item['lon'] = img.longitude

                # --- KIỂM TRA BIÊN GIỚI NGAY TẠI ĐÂY ---
                # Nếu điểm lưu nằm ngoài VN (hoặc vùng nguy hiểm), đánh dấu ngay
                if not is_in_vietnam(img.latitude, img.longitude):
                    item['valid_location'] = False
                    item['warning'] = "Nằm ngoài lãnh thổ Việt Nam"
            else:
                item['valid_location'] = False
                item['error'] = 'Chưa có tọa độ'

            results.append(item)

        return jsonify({'success': True, 'data': results})

    except Exception as e:
        print(f"Favorites Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500