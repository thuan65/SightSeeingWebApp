# from flask import Blueprint, render_template, request, redirect, session
# from sentence_transformers import SentenceTransformer, util
# from .toxic_filter import is_toxic
# from init_user_db import get_db, get_all_forum_posts

# forum = Blueprint("forum", __name__)

# sbert_model = SentenceTransformer("keepitreal/vietnamese-sbert")

# def compute_similarity(query_text, posts, top_k=5):
#     """So sánh độ tương đồng giữa query và posts trong DB"""
#     query_embedding = sbert_model.encode(query_text, convert_to_tensor=True)

#     scored = []
#     for post in posts:
#         # combine title + content
#         post_text = f"{post['title']} {post['content']}"
#         post_embedding = sbert_model.encode(post_text, convert_to_tensor=True)
#         similarity = util.cos_sim(query_embedding, post_embedding).item()
#         scored.append((similarity, post))

#     # Sắp xếp giảm dần
#     scored.sort(reverse=True, key=lambda x: x[0])

#     # Trả về top_k
#     results = [dict(x[1]) for x in scored[:top_k]]
#     # Nếu muốn, có thể thêm score vào dict
#     for i, r in enumerate(results):
#         r["score"] = float(scored[i][0])
#     return results

# @forum.route("/forum")
# def show_forum():
#     conn = get_db()
#     # Lấy tất cả post kèm tên người đăng
#     posts = conn.execute(
#         "SELECT posts.*, users.username FROM posts JOIN users ON posts.questioner_id = users.id ORDER BY created_at DESC"
#     ).fetchall()

#     posts_with_answers = []
#     for post in posts:
#         # Lấy câu trả lời cho mỗi post
#         answers = conn.execute(
#             "SELECT answers.*, users.username AS answerer_username FROM answers JOIN users ON answers.answerer_id = users.id WHERE post_id=?",
#             (post['id'],)
#         ).fetchall()
#         post_dict = dict(post)
#         post_dict['answers'] = [dict(a) for a in answers]
#         posts_with_answers.append(post_dict)

#     return render_template("forum.html", posts=posts_with_answers)

# @forum.route("/post/new", methods=["GET","POST"])
# def new_post():
#     if "questioner_id" not in session:
#         return "Không phải người dùng", 403

#     if request.method == "POST":
#         title = request.form["title"]
#         content = request.form["content"]

#         if is_toxic(content) or is_toxic(title):
#             return render_template("new_post.html", error="Nội dung câu hỏi/tiêu đề không phù hợp. Vui lòng viết lại.")
#         conn = get_db()
#         conn.execute(
#             "INSERT INTO posts(title, content, questioner_id) VALUES(?,?,?)",
#             (title, content, session["questioner_id"])
#         )
#         conn.commit()
#         return redirect("/forum")

#     return render_template("new_post.html")

# @forum.route("/post/<int:post_id>/reply", methods=["GET","POST"])
# def reply_post(post_id):
#     if "questioner_id" not in session:
#         return "Bạn không có quyền trả lời!", 403

#     conn = get_db()
#     post = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
#     if not post:
#         return "Bài viết không tồn tại", 404

#     if request.method == "POST":
#         content = request.form["content"]
#         conn.execute(
#             "INSERT INTO answers(content, answerer_id, post_id) VALUES(?,?,?)",
#             (content, session["questioner_id"], post_id)
#         )
#         conn.execute(
#             "UPDATE posts SET tag='answered' WHERE id=?",
#             (post_id,)
#         )
#         conn.commit()
#         return redirect("/forum")

#     return render_template("reply_post.html", post=post)

# # @forum.route("/search_forum", methods=["GET"])
# # def search_forum():
# #     query = request.args.get("q", "").strip()
# #     if not query:
# #         return render_template("search_results.html", posts=[], query=query)

# #     posts = get_all_forum_posts()

# #     top_results = compute_similarity(query, posts)

# #     filtered_results = [p for p in top_results if not is_toxic(p["content"])]

# #     return render_template("search_results.html", posts=filtered_results, query=query)

# @forum.route("/search_forum")
# def search_forum():
#     query = request.args.get("q", "").strip()
#     if not query:
#         return render_template("search_results.html", query=query, posts=[])

#     posts = get_all_forum_posts()
#     top_results = compute_similarity(query, posts)
#     filtered_results = [p for p in top_results if not is_toxic(p["content"])]
#     db = get_db()
#     for post in filtered_results:
#         answers = db.execute(
#             "SELECT a.content, u.username as answerer_username "
#             "FROM answers a "
#             "JOIN users u ON a.answerer_id = u.id "
#             "WHERE a.post_id=?",
#             (post["id"],)
#         ).fetchall()
#         post["answers"] = [{"content": a["content"], "answerer_username": a["answerer_username"]} for a in answers]

#     return render_template("search_results.html", posts=filtered_results, query=query)

# print(is_toxic("fuck"))   # phải trả về True
# print(is_toxic("you are stupid"))  # True
# print(is_toxic("hello world"))  # False
# print(is_toxic("đụ"))  # True
# print(is_toxic("bạn thật ngu ngốc"))  # True
# print(is_toxic("chào bạn"))  # False
# print(is_toxic("đm"))  # True
# print(is_toxic("bạn là đồ khốn nạn"))  # True
# print(is_toxic("vl"))  # True


from flask import Blueprint, render_template, request, redirect, session, flash, jsonify
from sentence_transformers import SentenceTransformer, util
from .toxic_filter import is_toxic
from models_loader import sbert_model
from flask_login import current_user
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from models import User, Post, Answer, Friendship 
from extensions import db
from werkzeug.utils import secure_filename
from .image_filter import is_nsfw_image
import os
import json

forum = Blueprint("forum", __name__, template_folder='template')

# Nếu không import được sbert_model từ models_loader thì dùng dòng dưới:
# sbert_model = SentenceTransformer("keepitreal/vietnamese-sbert")
UPLOAD_FOLDER = "static/post_images"

def compute_similarity(query_text, posts, top_k=5):
    """So sánh độ tương đồng giữa query và posts trong DB"""
    if not posts:
        return []

    query_embedding = sbert_model.encode(query_text, convert_to_tensor=True)

    scored = []
    for post in posts:
        # combine title + content
        post_text = f"{post['title']} {post['content']}"
        post_embedding = sbert_model.encode(post_text, convert_to_tensor=True)
        similarity = util.cos_sim(query_embedding, post_embedding).item()
        scored.append((similarity, post))

    # Sắp xếp giảm dần
    scored.sort(reverse=True, key=lambda x: x[0])

    # Trả về top_k
    results = [dict(x[1]) for x in scored[:top_k]]
    # Nếu muốn, có thể thêm score vào dict
    for i, r in enumerate(results):
        r["score"] = float(scored[i][0])
    return results

def get_visible_posts_orm():
    """
    Lấy danh sách posts dựa trên quyền riêng tư của người xem (current_user).
    """
    # Eager load questioner và answers (kèm answerer)
    query = Post.query.options(
        db.joinedload(Post.questioner),
        db.joinedload(Post.answers).joinedload(Answer.answerer)
    )

    if current_user.is_authenticated:
        user_id = current_user.id

        # 1. Lấy danh sách ID bạn bè
        # Lưu ý: friends_query trả về danh sách Row, cần lấy giá trị friend_id
        friends_query = Friendship.query.filter_by(user_id=user_id).with_entities(Friendship.friend_id).all()
        friend_ids = [f.friend_id for f in friends_query]

        # 2. Tạo bộ lọc (Filter Logic)
        posts = query.filter(
            or_(
                Post.privacy == 'public',                   # Ai cũng xem được
                Post.questioner_id == user_id,              # Bài của chính mình
                and_(
                    Post.privacy == 'friends',              # Bài chế độ bạn bè...
                    Post.questioner_id.in_(friend_ids)      # ...của người nằm trong list bạn bè
                )
            )
        ).order_by(Post.created_at.desc()).all()
    else:
        # Nếu chưa đăng nhập chỉ xem được Public
        posts = query.filter(Post.privacy == 'public').order_by(Post.created_at.desc()).all()
        
    result = []
    for post in posts:
        answers_list = []
        for ans in post.answers:
            answers_list.append({
                "content": ans.content,
                "answerer_username": ans.answerer.username if ans.answerer else "N/A"
            })

        result.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "tag": post.tag,
            "created_at": str(post.created_at), 
            "questioner_id": post.questioner_id,
            "username": post.questioner.username if post.questioner else "N/A",
            "privacy": post.privacy,
            "answers": answers_list,
            "images": json.loads(post.images) if post.images else [] 

        })
    return result

# --- ROUTE HIỂN THỊ FORUM (Bổ sung lại hàm này) ---
@forum.route("/forum")
def show_forum():
    posts_with_answers = get_visible_posts_orm()
    return render_template("forum.html", posts=posts_with_answers)

@forum.route("/post/new", methods=["GET", "POST"])
def new_post():
    if not current_user.is_authenticated:
        return "Vui lòng đăng nhập", 403

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        privacy = request.form.get("privacy", "public")

        # 1️⃣ Filter toxic text
        if is_toxic(title) or is_toxic(content):
            return render_template("new_post.html",
                                   error="Nội dung bài viết không phù hợp.")

        images = request.files.getlist("images")

        if len(images) > 3:
            return render_template("new_post.html",
                                   error="Chỉ được upload tối đa 3 ảnh!")

        saved_filenames = []

        for img in images:
            if not img.filename:
                continue

            safe_name = secure_filename(img.filename)
            temp_path = os.path.join("static/checkImage", safe_name)
            os.makedirs("static/checkImage", exist_ok=True)
            img.save(temp_path)

            # 2️⃣ NSFW Filter (only for public posts)
            if privacy == "public":
                blocked, info = is_nsfw_image(temp_path)
                print("NSFW check:", info)

                if blocked:
                    os.remove(temp_path)
                    return render_template(
                        "new_post.html",
                        error=f"Ảnh không hợp lệ: NSFW score {info['nsfw_score']:.2f}"
                    )

            # 3️⃣ Save safe image to final folder
            base, ext = os.path.splitext(safe_name)
            final_path = os.path.join(UPLOAD_FOLDER, safe_name)
            counter = 1
            while os.path.exists(final_path):
                safe_name = f"{base}_{counter}{ext}"
                final_path = os.path.join(UPLOAD_FOLDER, safe_name)
                counter += 1

            os.rename(temp_path, final_path)
            saved_filenames.append(safe_name)

        # 4️⃣ Insert post into DB
        new_post = Post(
            title=title,
            content=content,
            privacy=privacy,
            questioner_id=current_user.id,
            images=json.dumps(saved_filenames)
        )

        db.session.add(new_post)
        db.session.commit()
        flash("Đăng bài thành công!", "success")

        return redirect("/forum")

    return render_template("new_post.html")



@forum.route("/post/<int:post_id>/reply", methods=["GET","POST"])
def reply_post(post_id):
    if not current_user.is_authenticated:
        return "Bạn không có quyền trả lời!", 403

    post = Post.query.get(post_id)
    if not post:
        return "Bài viết không tồn tại", 404

    if request.method == "POST":
        content = request.form["content"]
        
        new_answer = Answer(
            content=content, 
            answerer_id=current_user.id, # Dùng current_user thống nhất
            post_id=post_id
        )
        db.session.add(new_answer)
        
        post.tag = "answered"
        db.session.commit()
        return redirect(f"/forum/post/{post_id}")


    # Convert object -> dict cho template
    post_dict = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "questioner_id": post.questioner_id,
        "tag": post.tag,
        "created_at": str(post.created_at)
    }
    return render_template("reply_post.html", post=post_dict)

@forum.route("/search_forum")
def search_forum():
    query = request.args.get("q", "").strip()
    if not query:
        return render_template("search_results.html", query=query, posts=[])

    # Chỉ search trong những bài được phép xem
    posts = get_visible_posts_orm()
    
    top_results = compute_similarity(query, posts)
    filtered_results = [p for p in top_results if not is_toxic(p["content"])]

    return render_template("search_results.html", posts=filtered_results, query=query)

# chi tiet bai viet
@forum.route("/forum/post/<int:post_id>")
def view_post(post_id):
    post = Post.query.get_or_404(post_id)

    post_dict = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "username": post.questioner.username,
        "created_at": str(post.created_at),
        "privacy": post.privacy,
        "images": json.loads(post.images) if post.images else [],
        "answers": [
            {
                "content": a.content,
                "answerer_username": a.answerer.username
            } for a in post.answers
        ]
    }

    return render_template("post_detail.html", post=post_dict)

@forum.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    if not current_user.is_authenticated:
        return "Bạn không có quyền xóa bài!", 403

    post = Post.query.get_or_404(post_id)

    # Chỉ người đăng mới được xóa
    if post.questioner_id != current_user.id and not current_user.is_admin:
        return "Bạn không được phép xóa bài viết này!", 403

    # Xóa ảnh vật lý
    if post.images:
        try:
            filenames = json.loads(post.images)
            for fname in filenames:
                img_path = os.path.join("static/post_images", fname)
                if os.path.exists(img_path):
                    os.remove(img_path)
        except:
            pass

    # Xóa post → Answer sẽ tự xóa theo cascade
    db.session.delete(post)
    db.session.commit()

    return redirect("/forum")

@forum.route("/forum/myposts")
def my_posts():
    if not current_user.is_authenticated:
        return redirect("/login")

    posts = Post.query.filter_by(questioner_id=current_user.id).order_by(Post.created_at.desc()).all()

    result = []
    for post in posts:
        result.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "created_at": str(post.created_at),
            "privacy": post.privacy,
            "username": current_user.username,
            "images": json.loads(post.images) if post.images else []
        })

    return render_template("my_posts.html", posts=result)

# --- ROUTE LẤY POSTS CỦA BẠN BÈ (API MỚI) ---
@forum.route("/posts/<int:user_id>", methods=["GET"])
def get_friend_posts(user_id):
    """
    Lấy 3 post gần nhất của người dùng, giới hạn privacy là public hoặc friends.
    Route này sẽ được truy cập qua URL prefix của forum (ví dụ: /forum/posts/<id>).
    """
    try:
        posts_query = (
            db.session.query(Post)
            # .options(joinedload(Post.images)) # Load đối tượng images
            .filter(Post.questioner_id == user_id)
            .filter(
                or_(
                    Post.privacy == 'public',
                    Post.privacy == 'friends'
                )
            )
            .order_by(Post.created_at.desc())
            .limit(3)
            # db.session.query(
            #     Post.id, 
            #     Post.title, 
            #     Post.content, 
            #     Post.privacy,
            #     Post.created_at,
            #     Post.images # <--- Truy vấn trực tiếp cột 'images'
            # ) 
            # .filter(Post.questioner_id == user_id)
            # .filter(
            #     or_(
            #         Post.privacy == 'public',
            #         Post.privacy == 'friends'
            #     )
            # )
            # .order_by(Post.created_at.desc())
            # .limit(3)
        )
        posts = posts_query.all()

        if not posts:
            return jsonify({"message": "No visible posts found for this user."}), 200

        results = []
        for post in posts:
            content_snippet = post.content
            if post.content and len(post.content) > 150:
                content_snippet = post.content[:150] + "..."
            
            image_filename = json.loads(post.images) if post.images else []
                
            results.append({
                "id": post.id,
                "title": post.title,
                "content_snippet": content_snippet,
                "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "privacy": post.privacy,
                "image_filename": image_filename[0] if image_filename else None
            })
        # print(results[0].image_filename)
        # print(results[1].image_filename)
        return jsonify(results), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500