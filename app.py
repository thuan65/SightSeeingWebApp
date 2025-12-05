# app.py

from flask import (
    Flask, render_template, request, jsonify, Response, json,
    redirect, url_for, flash, session
)

from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    UserMixin, current_user
)

from sqlalchemy import func, or_
from sentence_transformers import util

# 🟩 QUAN TRỌNG: dùng Session từ createDataBase (đã fix DB path)
# from createDataBase import Image, Session

# from createDataBase import Image, UserSession, FriendRequest, Friendship, User, Feedback
from models import User, Post, Answer, ConversationHistory, LiveLocation, Image
from extensions import db, bcrypt

import os

from __init__ import create_app

# ---------------------------------------------------------
# CẤU HÌNH ỨNG DỤNG FLASK
# ---------------------------------------------------------
app = create_app()



# engine = create_engine("sqlite:///instance/images.db")
# Session = sessionmaker(bind=engine)
# db_session = Session()




# =========================================================
# LOGIN MANAGER
# =========================================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_bp.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------------------------------------
# KẾT NỐI DB ẢNH VÀ REGISTER BLUEPRINT
#  ---------------------------------------------------------
# app.register_blueprint(search_filter)
# app.register_blueprint(search_text)
# app.register_blueprint(feedback_bp)
# app.register_blueprint(chatBot_bp)
# app.register_blueprint(forum)
# app.register_blueprint(search_image_bp)
# app.register_blueprint(login_bp)

# app.register_blueprint(friends_bp)
# app.register_blueprint(favorite_bp)
# app.register_blueprint(MapRouting_bp, url_prefix= "/MapRouting")
# app.register_blueprint(nearby_import_bp)















# ---------------------------------------------------------
# TRANG CHÍNH
# =========================================================
@app.route("/")
def index():
    keyword = request.args.get("q", "")
    
    if keyword:
        images = db.session.query(Image).filter(Image.tags.like(f"%{keyword}%")).all()
    else:
        images = db.session.query(Image).all()
    return render_template("index.html", images=images, keyword=keyword)


# =========================================================
# CHI TIẾT ẢNH
# =========================================================
@app.route("/image/<int:image_id>")
def image_detail(image_id):
    image = db.session.query(Image).filter_by(id=image_id).first()
    if not image:
        return "Ảnh không tồn tại!", 404
    return render_template("detail.html", image=image)


# =========================================================
# API: TÌM KIẾM ẢNH
# =========================================================
@app.route("/api/search")
def search():
    keyword = request.args.get("q", "").lower()
    results = db.session.query(Image).filter(
        or_(
            func.lower(Image.tags).like(f"%{keyword}%"),
            func.lower(Image.name).like(f"%{keyword}%")
        )
    ).all()

# Chuyển tất cả fields của Image thành dict        
    data = [ {c.name: getattr(img, c.name) for c in img.__table__.columns} 
                 for img in results ]
    return jsonify(data)


# =========================================================
# GIAO DIỆN CHATBOT
# =========================================================
@app.route("/chat_ui")
def chat_ui():
    return render_template("chat_ui.html")


# =========================================================
# TRANG BẠN BÈ
# =========================================================
@app.route("/friends")
def friends_page():
    if "user_id" not in session:
        return redirect("/auth/login")  
    return render_template("friends.html")


# =========================================================
# CHẠY ỨNG DỤNG
# =========================================================
if __name__ == "__main__":
    print("=== Initializing Flask Database ===")
    with app.app_context():
        db.create_all()

    print("=== Starting Web App ===")
    app.run(debug=False, use_reloader=False)
