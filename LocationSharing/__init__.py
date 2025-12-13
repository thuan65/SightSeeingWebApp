# LocationSharing/__init__.py

from flask import Blueprint

# Khởi tạo Blueprint cho các route HTTP
location_bp = Blueprint('location_sharing', __name__)

# Import các route (để Blueprint có thể tìm thấy chúng)
from . import routes 
# Import các sự kiện Socket (để hàm register_socket_events có thể sử dụng)
from . import socket_events

# Hàm này sẽ được gọi từ app.py để đăng ký tất cả các events SocketIO
def register_socket_events(socketio):
    """Đăng ký tất cả các event handler SocketIO."""
    socket_events.register_events(socketio)