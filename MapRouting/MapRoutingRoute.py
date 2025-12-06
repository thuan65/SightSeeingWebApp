from flask import Flask, render_template, request, jsonify, Blueprint
import sqlite3
import os

# --- SỬA LỖI 1: THÊM DẤU CHẤM ĐỂ IMPORT TƯƠNG ĐỐI ---
from .routing import get_route
from .multi_point_routing import find_shortest_route_multi_points
from .geocoding import geocode_address, reverse_geocode

# --- SỬA LỖI 2 & 3: ĐẶT TÊN BIẾN LÀ MapRouting_bp VÀ ĐỔI TÊN BLUEPRINT ĐỂ TRÁNH TRÙNG ---
MapRouting_bp = Blueprint("Map_Routing_System", __name__, template_folder="templates")

# --- CẤU HÌNH ĐƯỜNG DẪN DATABASE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'instance', 'FlaskDataBase.db')
DB_PATH = os.path.normpath(DB_PATH)

def get_db_connection():
    if not os.path.exists(DB_PATH):
        print(f"⚠️ Error: Không tìm thấy file database tại {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- CÁC ROUTE (Sử dụng biến MapRouting_bp) ---

@MapRouting_bp.route('/')
def index():
    return render_template('map.html')

@MapRouting_bp.route('/api/geocode', methods=['POST'])
def geocode():
    try:
        data = request.json
        address = data.get('address', '')
        if not address: return jsonify({'success': False, 'error': 'Address empty'}), 400
        result = geocode_address(address)
        if result: return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500

@MapRouting_bp.route('/api/reverse-geocode', methods=['POST'])
def reverse_geo():
    try:
        data = request.json
        lat = float(data['lat'])
        lon = float(data['lon'])
        result = reverse_geocode(lat, lon)
        if result: return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'Not found'}), 404
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500

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
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500

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
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500

@MapRouting_bp.route('/api/favorites/<int:user_id>', methods=['GET'])
def get_user_favorites(user_id):
    conn = get_db_connection()
    try:
        query = """
            SELECT f.id as fav_id, i.name, i.tags 
            FROM favorites f
            JOIN images i ON f.image_id = i.id
            WHERE f.user_id = ? ORDER BY f.created_at DESC
        """
        favorites = conn.execute(query, (user_id,)).fetchall()
        results = []
        for fav in favorites:
            place_name = fav['name']
            geo_data = geocode_address(place_name)
            if geo_data:
                results.append({
                    'id': fav['fav_id'], 'name': place_name, 'tags': fav['tags'],
                    'lat': geo_data['lat'], 'lon': geo_data['lon'], 'display_name': geo_data['display_name']
                })
            else:
                results.append({'id': fav['fav_id'], 'name': place_name, 'tags': fav['tags'], 'error': 'Not found'})
        return jsonify({'success': True, 'data': results})
    except Exception as e: return jsonify({'success': False, 'error': str(e)}), 500
    finally: conn.close()