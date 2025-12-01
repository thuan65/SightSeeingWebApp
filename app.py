# app.py
from flask import (
    Flask, render_template, request, jsonify, Response, json,
    redirect, url_for, flash, session
)
from sentence_transformers import util
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ChatBot.chatBot import chatbot_reply
from createDataBase import Image, Favorite, UserSession
from Search_Imagine import find_similar
from models import db, bcrypt, User
from forms import RegisterForm, LoginForm
from Forum.forum import forum
from Search_Filter.search_filter import search_filter
from Search_Text.search_text import search_text




from flask_login import (
    LoginManager, login_user, logout_user, login_required, UserMixin, current_user
)


from models_loader import get_sbert_model


import torch
from feedback import feedback_bp  
# NEW CODE: để người dùng upload ảnh
import os
from friends import friends_bp
# ---------------------------------------------------------
# CẤU HÌNH ỨNG DỤNG FLASK
# ---------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'


# Khởi tạo database, bcrypt và login manager
db.init_app(app)
bcrypt.init_app(app)


# Kết nối SQLite cho phần ảnh
# Đăng ký API feedback
app.register_blueprint(search_filter)
app.register_blueprint(search_text)
app.register_blueprint(feedback_bp)
app.register_blueprint(forum)


app.register_blueprint(friends_bp)


app.config['JSON_AS_ASCII'] = False
engine = create_engine("sqlite:///images.db")
Session = sessionmaker(bind=engine)
db_session = Session()


# ---------------------------------------------------------
# TRANG CHÍNH
# ---------------------------------------------------------
@app.route("/")
def index():
    keyword = request.args.get("q", "")
    if keyword:
        images = db_session.query(Image).filter(Image.tags.like(f"%{keyword}%")).all()
    else:
        images = db_session.query(Image).all()
    return render_template("index.html", images=images, keyword=keyword)


# ---------------------------------------------------------
# CHI TIẾT ẢNH
# ---------------------------------------------------------
@app.route("/image/<int:image_id>")
def image_detail(image_id):
    image = db_session.query(Image).filter_by(id=image_id).first()
    if not image:
        return "Ảnh không tồn tại!", 404
    return render_template("detail.html", image=image)


# ---------------------------------------------------------
# TÌM KIẾM ẢNH BẰNG TỪ KHÓA
# ---------------------------------------------------------
@app.route("/api/search")
def search():
    keyword = request.args.get("q", "").lower()
    results = db_session.query(Image).filter(Image.tags.like(f"%{keyword}%")).all()
    data = [{"id": img.id, "name": img.name, "filename": img.filename} for img in results]
    return jsonify(data)


# ---------------------------------------------------------
# TÌM KIẾM ẢNH BẰNG ẢNH (UPLOAD)
# ---------------------------------------------------------
@app.route("/search_image", methods=["GET", "POST"])
def search_image():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "Không có ảnh nào được tải lên", 400


        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(upload_path)


        # Gọi hàm tìm ảnh tương tự
        best_match, score = find_similar(upload_path)
        return render_template(
            "search_result.html",
            query=file.filename,
            match=best_match,
            score=round(score, 3)
        )


    return render_template("search_image.html")


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
@app.route("/map")
def show_map():
    return render_template("map.html")


# ---------------------------------------------------------
# CHATBOT
# ---------------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400


    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400


    try:
        bot_response = chatbot_reply(user_message)
        return jsonify({"reply": bot_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat_ui")
def chat_ui():
    return render_template("chat_ui.html")


# ---------------------------------------------------------
# ĐĂNG KÝ TÀI KHOẢN
# ---------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Tạo tài khoản thành công! Hãy đăng nhập.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# ---------------------------------------------------------
# ĐĂNG NHẬP
# ---------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_page = request.args.get("next")  # Lấy URL cần redirect sau login
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['username'] = user.username
            session['user_id'] = user.id
            return redirect(next_page or url_for('index'))  # redirect về next_page nếu có
        else:
            flash("Tên đăng nhập hoặc mật khẩu sai!", "danger")
    return render_template('login.html', form=form)


# ---------------------------------------------------------
# ĐĂNG XUẤT
# ---------------------------------------------------------
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Đã đăng xuất!", "info")
    return redirect(url_for('login'))
# ---------------------------------------------------------
# KẾT BẠN
# ---------------------------------------------------------
@app.route("/friends")
def friends_page():
    if "user_id" not in session:  
        return redirect("/login")  # chưa login thì không xem friend list
   
    return render_template("friends.html")  # session tự truyền vào file


# ---------------------------------------------------------
# CHÈN YÊU THÍCH
# ---------------------------------------------------------
@app.post("/favorite/<int:image_id>")
def add_favorite(image_id):
    if "user_id" not in session:
        # Nếu chưa login, trả về JSON kèm login_url
        return jsonify({
            "error": "Bạn chưa đăng nhập",
            "login_url": url_for("login", next=url_for("image_detail", image_id=image_id))
        }), 401


    user_id = session["user_id"]
    db_sess = UserSession()


    try:
        # Kiểm tra xem đã có trong favorite chưa
        exists = db_sess.query(Favorite).filter_by(user_id=user_id, image_id=image_id).first()
        if exists:
            return jsonify({"error": "Đã có trong danh sách yêu thích"}), 400


        # Thêm mới
        fav = Favorite(user_id=user_id, image_id=image_id)
        db_sess.add(fav)
        db_sess.commit()


        return jsonify({"message": "ok"})
   
    except Exception as e:
        db_sess.rollback()
        # Trả lỗi chi tiết nếu commit fail
        return jsonify({"error": f"Lỗi khi lưu yêu thích: {e}"}), 500
   
    finally:
        db_sess.close()


@app.route("/favorites")
def show_favorites():
    if "user_id" not in session:
        flash("Bạn cần đăng nhập để xem danh sách yêu thích.", "warning")
        return redirect(url_for("login", next=url_for("show_favorites")))


    user_id = session["user_id"]
    db_sess = UserSession()
    try:
        favs = db_sess.query(Favorite).filter_by(user_id=user_id).all()
        image_ids = [f.image_id for f in favs]
        images_info = db_session.query(Image).filter(Image.id.in_(image_ids)).all()
    finally:
        db_sess.close()


    return render_template("favorites.html", images=images_info)


@app.route("/favorite/<int:image_id>", methods=["DELETE"])
def remove_favorite(image_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa login"}), 401


    user_id = session["user_id"]
    db_sess = UserSession()
    try:
        fav = db_sess.query(Favorite).filter_by(user_id=user_id, image_id=image_id).first()
        if not fav:
            return jsonify({"error": "Không tìm thấy favorite này"}), 404


        db_sess.delete(fav)
        db_sess.commit()
        return jsonify({"message": "ok"})
    except Exception as e:
        db_sess.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db_sess.close()




# ---------------------------------------------------------
# CHẠY ỨNG DỤNG
# ---------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)



