# Messaging/__init__.py

from flask import Blueprint

# Khởi tạo Blueprint cho các route HTTP
messaging_bp = Blueprint('messaging', __name__)

# Import các route và sự kiện để module này hoạt động
from . import routes 
from . import socket_events

# Hàm này sẽ được gọi từ app.py để đăng ký tất cả các events SocketIO
def register_socket_events(socketio):
    """Đăng ký tất cả các event handler SocketIO."""
    socket_events.register_events(socketio)