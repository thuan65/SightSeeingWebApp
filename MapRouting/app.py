from flask import Flask, render_template, request, jsonify
from routing import get_route
from multi_point_routing import find_shortest_route_multi_points
from geocoding import geocode_address, reverse_geocode

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/console')
def console():
    return render_template('console.html')


@app.route('/api/geocode', methods=['POST'])
def geocode():
    """Convert address to coordinates"""
    try:
        data = request.json
        address = data.get('address', '')

        if not address:
            return jsonify({
                'success': False,
                'error': 'Address cannot be empty'
            }), 400

        result = geocode_address(address)

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Address not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reverse-geocode', methods=['POST'])
def reverse_geo():
    """Convert coordinates to address"""
    try:
        data = request.json
        lat = float(data['lat'])
        lon = float(data['lon'])

        result = reverse_geocode(lat, lon)

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Address not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/route', methods=['POST'])
def calculate_route():
    """Feature 1: Find route from user location to destination"""
    try:
        data = request.json
        start_lat = float(data['start_lat'])
        start_lon = float(data['start_lon'])
        end_lat = float(data['end_lat'])
        end_lon = float(data['end_lon'])
        vehicle = data.get('vehicle', 'car')

        route_data = get_route(start_lat, start_lon, end_lat, end_lon, vehicle)

        if route_data:
            return jsonify({
                'success': True,
                'route': route_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Cannot find route'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/multi-route', methods=['POST'])
def calculate_multi_route():
    """Feature 2: Find shortest route through multiple points"""
    try:
        data = request.json
        start_lat = float(data['start_lat'])
        start_lon = float(data['start_lon'])
        destinations = data['destinations']  # List of {lat, lon}
        vehicle = data.get('vehicle', 'car')

        if len(destinations) < 1 or len(destinations) > 3:
            return jsonify({
                'success': False,
                'error': 'Number of destinations must be between 1 and 3'
            }), 400

        result = find_shortest_route_multi_points(
            start_lat, start_lon, destinations, vehicle
        )

        if result:
            return jsonify({
                'success': True,
                'route': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Cannot find route'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)