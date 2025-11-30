# friends.py
from flask import Blueprint, request, jsonify, session as flask_session
from datetime import datetime

from createDataBase import UserSession, FriendRequest, Friendship, User, UserBase

friends_bp = Blueprint("friends", __name__, url_prefix="/friends")

# helper: current logged user id (giả định bạn dùng flask.session['user_id'])
def get_current_user_id():
    return flask_session.get("user_id")

# 1) Gửi lời mời
@friends_bp.route("/request", methods=["POST"])
def send_request():
    data = request.json or {}
    to_user = data.get("to_user")
    from_user = get_current_user_id()

    if not from_user:
        return jsonify({"error": "User not logged in"}), 401
    if not to_user:
        return jsonify({"error": "to_user is required"}), 400
    if int(to_user) == int(from_user):
        return jsonify({"error": "Cannot friend yourself"}), 400

    usession = UserSession()
    try:
        # kiểm tra tồn tại user đích
        if not usession.query(User).filter_by(id=to_user).first():
            return jsonify({"error": "Target user not found"}), 404

        # kiểm tra đã là bạn
        already = usession.query(Friendship).filter_by(user_id=from_user, friend_id=to_user).first()
        if already:
            return jsonify({"message": "Already friends"}), 200

        # kiểm tra request hiện tại (unique constraint) - có thể pending hoặc rejected
        fr = usession.query(FriendRequest).filter_by(from_user=from_user, to_user=to_user).first()
        if fr:
            if fr.status == "pending":
                return jsonify({"message": "Request already pending"}), 200
            else:
                # nếu trước đó rejected/cancelled thì cho tạo lại (update)
                fr.status = "pending"
                fr.created_at = datetime.utcnow()
                usession.commit()
                return jsonify({"message": "Request re-sent"}), 200

        # tạo mới
        new_fr = FriendRequest(from_user=from_user, to_user=to_user, status="pending", created_at=datetime.utcnow())
        usession.add(new_fr)
        usession.commit()
        return jsonify({"message": "Friend request sent"}), 201

    except Exception as e:
        usession.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        usession.close()


# 2) Accept một lời mời
@friends_bp.route("/accept", methods=["POST"])
def accept_request():
    data = request.json or {}
    request_id = data.get("request_id")
    current = get_current_user_id()
    if not current:
        return jsonify({"error": "User not logged in"}), 401
    if not request_id:
        return jsonify({"error": "request_id required"}), 400

    usession = UserSession()
    try:
        fr = usession.query(FriendRequest).filter_by(id=request_id, to_user=current, status="pending").first()
        if not fr:
            return jsonify({"error": "Friend request not found or already handled"}), 404

        # mark accepted
        fr.status = "accepted"
        usession.add(fr)

        # tạo 2 dòng friendship (hai chiều)
        f1 = Friendship(user_id=fr.from_user, friend_id=fr.to_user, created_at=datetime.utcnow())
        f2 = Friendship(user_id=fr.to_user, friend_id=fr.from_user, created_at=datetime.utcnow())
        usession.add_all([f1, f2])
        usession.commit()
        return jsonify({"message": "Friend request accepted"}), 200

    except Exception as e:
        usession.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        usession.close()


# 3) Reject / cancel một lời mời
@friends_bp.route("/reject", methods=["POST"])
def reject_request():
    data = request.json or {}
    request_id = data.get("request_id")
    current = get_current_user_id()
    if not current:
        return jsonify({"error": "User not logged in"}), 401
    if not request_id:
        return jsonify({"error": "request_id required"}), 400

    usession = UserSession()
    try:
        fr = usession.query(FriendRequest).filter_by(id=request_id).first()
        if not fr:
            return jsonify({"error": "Friend request not found"}), 404

        # Nếu người nhận reject, hoặc người gửi cancel
        if fr.to_user != current and fr.from_user != current:
            return jsonify({"error": "Not authorized"}), 403

        fr.status = "rejected"
        usession.add(fr)
        usession.commit()
        return jsonify({"message": "Friend request rejected/cancelled"}), 200

    except Exception as e:
        usession.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        usession.close()


# 4) Unfriend (bỏ bạn)
@friends_bp.route("/unfriend", methods=["POST"])
def unfriend():
    data = request.json or {}
    target = data.get("target_user")
    current = get_current_user_id()
    if not current:
        return jsonify({"error": "User not logged in"}), 401
    if not target:
        return jsonify({"error": "target_user required"}), 400

    usession = UserSession()
    try:
        # xóa cả hai hướng
        usession.query(Friendship).filter_by(user_id=current, friend_id=target).delete()
        usession.query(Friendship).filter_by(user_id=target, friend_id=current).delete()
        usession.commit()
        return jsonify({"message": "Unfriended"}), 200

    except Exception as e:
        usession.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        usession.close()


# 5) Lấy danh sách bạn / pending requests (optional)
@friends_bp.route("/list/<int:user_id>", methods=["GET"])
def list_friends(user_id):
    usession = UserSession()
    try:
        # friends
        friends = usession.query(Friendship).filter_by(user_id=user_id).all()
        friends_ids = [f.friend_id for f in friends]
        # lấy username
        users = usession.query(User).filter(User.id.in_(friends_ids)).all() if friends_ids else []
        friends_list = [{"id": u.id, "username": u.username} for u in users]

        # pending incoming
        incoming = usession.query(FriendRequest).filter_by(to_user=user_id, status="pending").all()
        incoming_list = [{"id": r.id, "from_user": r.from_user} for r in incoming]

        # pending outgoing
        outgoing = usession.query(FriendRequest).filter_by(from_user=user_id, status="pending").all()
        outgoing_list = [{"id": r.id, "to_user": r.to_user} for r in outgoing]

        return jsonify({
            "friends": friends_list,
            "incoming_requests": incoming_list,
            "outgoing_requests": outgoing_list
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        usession.close()

@friends_bp.route("/search_user")
def search_user():
    """
    Tìm kiếm user theo username (có thể partial match, không phân biệt hoa thường).
    Trả về danh sách tối đa 10 user phù hợp, không bao gồm chính user đang đăng nhập.
    """
    username = request.args.get("username", "").strip()
    current_user = get_current_user_id()

    if not username:
        return jsonify({"error": "username required"}), 400
    if not current_user:
        return jsonify({"error": "User not logged in"}), 401

    usession = UserSession()
    try:
        # Tìm user khớp với từ khóa, không phân biệt hoa thường
        users = (
            usession.query(User)
            .filter(User.username.ilike(f"%{username}%"))
            .filter(User.id != current_user)  # bỏ qua chính user
            .limit(10)
            .all()
        )

        if not users:
            return jsonify({"error": f"No users found for '{username}'"}), 404

        # Chuẩn hóa JSON
        results = [{"id": u.id, "username": u.username} for u in users]

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        usession.close()

@friends_bp.route("/debug_users")
def debug_users():
    usession = UserSession()
    users = usession.query(User).all()
    return jsonify([{"id": u.id, "username": u.username} for u in users])
