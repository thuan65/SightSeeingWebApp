# LocationSharing/routes.py

from . import location_bp # Import Blueprint đã tạo
from flask import jsonify, request
from flask_login import current_user, login_required
from extensions import db
from models import Friendship, User, LiveLocation
from sqlalchemy import or_

def get_friends_ids(user_id):
    """Trả về danh sách ID bạn bè của người dùng (hai chiều)."""
    
    friendships = db.session.query(Friendship).filter(
        or_(Friendship.user_id == user_id, Friendship.friend_id == user_id)
    ).all()

    friend_ids = set()
    
    for friendship in friendships:
        if (friendship.user_id != user_id):
            friend_ids.add(friendship.user_id)
        if friendship.friend_id != user_id:
            friend_ids.add(friendship.friend_id)
        # for friendship in friendships:
        #     friend_id_to_check = None
            
        #     # 1. Xác định ID người bạn (ID khác user_id)
        #     if friendship.user_id != user_id:
        #         friend_id_to_check = friendship.user_id
        #     elif friendship.friend_id != user_id:
        #         friend_id_to_check = friendship.friend_id
            
        #     if friend_id_to_check:
        #         # 2. Lấy đối tượng User từ DB (Gây nhiều DB hit)
        #         friend_user = db.session.query(User).filter_by(id=friend_id_to_check).first()
                
        #         # 3. CÚ PHÁP KIỂM TRA ĐÚNG:
        #         if friend_user and friend_user.online == True: # True tương đương với 1 trong DB
        #             friend_ids.add(friend_id_to_check)
            
    final_ids = list(friend_ids)

    return final_ids

# Route API để lấy danh sách ID của bạn bè
@location_bp.route('/api/friends_list', methods=['GET'])
@login_required
def get_friends_list_api():
    user_id = current_user.id
    friends_ids = get_friends_ids(user_id)
    # print(f"[DEBUG ROUTES] API /api/friends_list trả về ID: {friends_ids}")
    return jsonify({"friends_ids": friends_ids}), 200

# Route API để JavaScript lấy thông tin người dùng (Đã có trong app.py)
@location_bp.route('/api/current_user_info')
@login_required 
def get_current_user_info():
    """Cung cấp user_id và username cho JavaScript."""
    return jsonify({
        'user_id': current_user.id,
        'username': current_user.username,
        'share_mode': current_user.share_mode 
    })

# Trong app.py (Thêm vào cùng vị trí với các API khác)
@location_bp.route('/api/share_mode', methods=['POST'])
@login_required
def update_share_mode():
    data = request.get_json()
    mode = data.get('mode')
    user_id = current_user.id
    
    if mode in ['friends', 'hidden']:
        current_user.share_mode = mode
        db.session.commit()
        
        # Nếu chuyển sang HIDDEN, phải gửi event xóa marker cho tất cả bạn bè
        # if mode == 'hidden':
        #     # Hàm get_friends_ids đã được định nghĩa trong app.py
        #     friend_ids = get_friends_ids(user_id) 
        #     for friend_id in friend_ids:
        #         # Gửi event để client tự xóa marker của người này
        #         socketio.emit('friend:disconnected', {'userId': user_id}, room=f'user_{friend_id}')
        
        return jsonify({"message": "Share mode updated", "new_mode": mode}), 200
    return jsonify({"message": "Invalid mode"}), 400

# Trong app.py
@location_bp.route('/api/initial_locations', methods=['GET'])
@login_required
def initial_locations():
    user_id = current_user.id
    
    # Lấy ID của tất cả bạn bè (đang share_mode='friends' hoặc chưa set)
    friend_ids = get_friends_ids(user_id) # Hàm đã có của bạn
    
    # 1. Lấy LiveLocation của tất cả bạn bè đã tìm được
    # Cần phải JOIN với bảng User để lấy username và share_mode
    locations = db.session.query(LiveLocation, User.username, User.share_mode, User.online).join(User, LiveLocation.user_id == User.id).filter(
        LiveLocation.user_id.in_(friend_ids)
    ).all()
    
    result = []
    for loc, uname, mode, is_online in locations:
        # Chỉ hiển thị vị trí cuối nếu họ không ở chế độ 'hidden'
        #if mode != 'hidden':
        result.append({
            'user_id': loc.user_id,
            'username': uname,
            'lat': loc.lat,
            'lng': loc.lng,
            'share_mode': mode,
            'is_online': is_online
        })
            
    # Thêm vị trí của chính mình (để đảm bảo map bao trùm cả mình)
    my_location = db.session.query(LiveLocation).filter_by(user_id=user_id).first()
    if my_location:
         result.append({
            'user_id': user_id,
            'username': current_user.username,
            'lat': my_location.lat,
            'lng': my_location.lng,
            'is_self': True
        })

    return jsonify({"locations": result}), 200