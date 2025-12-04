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


from flask import Blueprint, render_template, request, redirect, session
from sentence_transformers import SentenceTransformer, util
from .toxic_filter import is_toxic
from models_loader import sbert_model
# SỬ DỤNG ORM VÀ MODELS MỚI
from models import User, Post, Answer
from extensions import  db

forum = Blueprint("forum", __name__, template_folder='template')

sbert_model = SentenceTransformer("keepitreal/vietnamese-sbert")

def compute_similarity(query_text, posts, top_k=5):
    """So sánh độ tương đồng giữa query và posts trong DB"""
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

def get_all_forum_posts_orm():
    """
    Lấy tất cả posts, trả về dict có đủ fields:
    id, title, content, questioner_id, username, tag, created_at, answers
    Sử dụng SQLAlchemy ORM.
    """
    # Eager load questioner và answers (kèm answerer)
    posts = Post.query.options(
        db.joinedload(Post.questioner),
        db.joinedload(Post.answers).joinedload(Answer.answerer)
    ).order_by(Post.created_at.desc()).all()

    result = []
    for post in posts:
        # Chuyển đổi sang định dạng dictionary để tương thích với logic cũ/template
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
            "answers": answers_list
        })
    return result


@forum.route("/forum")
def show_forum():
    # Thay thế logic sqlite3 bằng ORM
    posts_with_answers = get_all_forum_posts_orm()
    return render_template("forum.html", posts=posts_with_answers)

@forum.route("/post/new", methods=["GET","POST"])
def new_post():
    if "questioner_id" not in session:
        # Kiểm tra session của người dùng (Giả sử id người dùng là 'questioner_id')
        return "Không phải người dùng", 403

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if is_toxic(content) or is_toxic(title):
            return render_template("new_post.html", error="Nội dung câu hỏi/tiêu đề không phù hợp. Vui lòng viết lại.")
        
        # Thay thế logic sqlite3 bằng ORM
        new_post_entry = Post(
            title=title, 
            content=content, 
            questioner_id=session["questioner_id"]
        )
        db.session.add(new_post_entry)
        db.session.commit()
        
        return redirect("/forum")

    return render_template("new_post.html")

@forum.route("/post/<int:post_id>/reply", methods=["GET","POST"])
def reply_post(post_id):
    if "questioner_id" not in session:
        return "Bạn không có quyền trả lời!", 403

    # Thay thế logic sqlite3 bằng ORM
    post = Post.query.get(post_id)
    if not post:
        return "Bài viết không tồn tại", 404

    if request.method == "POST":
        content = request.form["content"]
        
        # Thêm câu trả lời
        new_answer = Answer(
            content=content, 
            answerer_id=session["questioner_id"], 
            post_id=post_id
        )
        db.session.add(new_answer)
        
        # Cập nhật trạng thái post
        post.tag = "answered"
        
        db.session.commit()
        return redirect("/forum")

    # Chuyển đối tượng ORM thành dictionary để tương thích với template
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

    # Lấy tất cả post (kèm answers) bằng ORM
    posts = get_all_forum_posts_orm() 
    
    top_results = compute_similarity(query, posts)
    filtered_results = [p for p in top_results if not is_toxic(p["content"])]
    
    # Logic lấy answers thủ công đã được loại bỏ vì get_all_forum_posts_orm() đã bao gồm

    return render_template("search_results.html", posts=filtered_results, query=query)