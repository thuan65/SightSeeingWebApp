from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import func

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Quan hệ ORM
    posts = db.relationship("Post", back_populates="questioner", cascade="all, delete")
    answers = db.relationship("Answer", back_populates="answerer", cascade="all, delete")

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    questioner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    tag = db.Column(db.String, default="unanswered")
    created_at = db.Column(db.DateTime, server_default=func.datetime("now", "localtime"))

    # Quan hệ ORM
    answers = db.relationship("Answer", back_populates="post", cascade="all, delete")
    questioner = db.relationship("User", back_populates="posts")


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)
    answerer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    created_at = db.Column(db.DateTime, server_default=func.datetime("now", "localtime"))

    # Quan hệ ORM
    post = db.relationship("Post", back_populates="answers")
    answerer = db.relationship("User", back_populates="answers")