from flask import Flask, render_template, request, jsonify, Response, json, session, redirect
# app.py

from flask import (
    Flask, render_template, request, jsonify, Response, json,
    redirect, url_for, flash, session
)

from flask_login import (
    LoginManager, login_user, logout_user, login_required, UserMixin, current_user
)

from sentence_transformers import util
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, or_


from createDataBase import Image, UserSession, FriendRequest, Friendship, User, Feedback
from models import User, Post, Answer, ConversationHistory, LiveLocation
from extensions import db, bcrypt

import os

from __init__ import create_app

# ---------------------------------------------------------
# CẤU HÌNH ỨNG DỤNG FLASK
# ---------------------------------------------------------
app = create_app()



engine = create_engine("sqlite:///instance/images.db")
Session = sessionmaker(bind=engine)
db_session = Session()



# ---------------------------------------------------------
# LƯU LỊCH SỬ 
# ---------------------------------------------------------
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
# ---------------------------------------------------------
@app.route("/")
def index():
    keyword = request.args.get("q", "")
    if keyword:
        images = db.session.query(Image).filter(Image.tags.like(f"%{keyword}%")).all()
    else:
        images = db.session.query(Image).all()
    return render_template("index.html", images=images, keyword=keyword)

# ---------------------------------------------------------
# CHI TIẾT ẢNH
# ---------------------------------------------------------
@app.route("/image/<int:image_id>")
def image_detail(image_id):
    image = db.session.query(Image).filter_by(id=image_id).first()
    if not image:
        return "Ảnh không tồn tại!", 404
    return render_template("detail.html", image=image)

# ---------------------------------------------------------
# TÌM KIẾM ẢNH BẰNG TỪ KHÓA
# ---------------------------------------------------------
@app.route("/api/search")
def search():
    keyword = request.args.get("q", "").lower()
    results = db.session.query(Image).filter(
        or_(
        func.lower(Image.tags).like(f"%{keyword}%"),
        func.lower(Image.name).like(f"%{keyword}%")
        )
        ).all()
    data = [{"id": img.id, "name": img.name, "filename": img.filename} for img in results]
    return jsonify(data)



# ---------------------------------------------------------
# LỌC TÌM KIẾM.  CHƯA DÁM XOÁ SỢ SAI
# ---------------------------------------------------------
# @app.route("/search_filter", methods=["GET"])
# def search_filter():
#     city = request.args.get("city", "")
#     tag = request.args.get("tag", "")
#     min_rating = float(request.args.get("rating", 0))

#     query = "SELECT * FROM images WHERE 1=1"
#     params = {}

#     if city:
#         query += " AND city LIKE :city"
#         params["city"] = f"%{city}%"
#     if tag:
#         query += " AND tags LIKE :tag"
#         params["tag"] = f"%{tag}%"
#     query += " AND rating >= :min_rating"
#     params["min_rating"] = min_rating

#     with engine.connect() as conn:
#         results = conn.execute(text(query), params).mappings().all()

#     response = json.dumps([dict(row) for row in results], ensure_ascii=False)
#     return Response(response, content_type="application/json; charset=utf-8")

# ---------------------------------------------------------
# TÌM KIẾM THEO VĂN BẢN (AI - Sentence-BERT) Y CHANG T CHƯA DÁM XOÁ
# ---------------------------------------------------------


# def get_all_places():
#     with engine.connect() as conn:
#         results = conn.execute(text("SELECT * FROM images")).mappings().all()
#     return results

# def compute_similarity(query_text, places, top_k=5):
#     query_embedding = sbert_model.encode(query_text, convert_to_tensor=True)
#     scored = []
#     for place in places:
#         place_embedding = sbert_model.encode(place["description"], convert_to_tensor=True)
#         similarity = util.cos_sim(query_embedding, place_embedding).item()
#         scored.append((similarity, place))
#     scored.sort(reverse=True, key=lambda x: x[0])
#     return [dict(x[1]) for x in scored[:top_k]]

# @app.route("/search_text", methods=["GET"])
# def search_text():
#     user_message = request.args.get("q", "")
#     if not user_message.strip():
#         return jsonify([])

#     places = get_all_places()
#     top_results = compute_similarity(user_message, places)
#     response = json.dumps(top_results, ensure_ascii=False)
#     return Response(response, content_type="application/json; charset=utf-8")

# ---------------------------------------------------------
# TRANG BẢN ĐỒ
# ---------------------------------------------------------
# @app.route("/map")
# def show_map():
#     return render_template("map.html")


@app.route("/chat_ui")
def chat_ui():
    return render_template("chat_ui.html")
# ---------------------------------------------------------
# KẾT BẠN
# ---------------------------------------------------------
@app.route("/friends")
def friends_page():
    if "user_id" not in session:  
        return redirect("/auth/login")  # chưa login thì không xem friend list
    
    return render_template("friends.html")  # session tự truyền vào file
# ---------------------------------------------------------
# CHẠY ỨNG DỤNG
# ---------------------------------------------------------
if __name__ == "__main__":
    print("===Creating DataBase===")
    with app.app_context():
        db.create_all()
        
    #app.run(debug=True)
    print("===Starting Web App===")
    app.run(debug=False, use_reloader=False) #Chạy khi không cần debug
    print("===Web App Shutting Down===")
