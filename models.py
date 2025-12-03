from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import func
from datetime import datetime
from flask_login import UserMixin


db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
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


class ConversationHistory(db.Model):
    __tablename__ = "conversation_history"

    id = db.Column(db.Integer, primary_key=True)
    
    # ID của người dùng (để biết lịch sử này của ai)
    user_id = db.Column(db.Integer, nullable=False) 
    
    # Phân biệt là chat với 'chatbot' hay 'user'
    session_type = db.Column(db.String(50), nullable=False) 
    
    # Nội dung người dùng gửi
    user_message = db.Column(db.Text, nullable=True)
    
    # Nội dung hệ thống (bot/chuyên gia) trả lời
    system_response = db.Column(db.Text, nullable=True)
    
    # Dấu thời gian
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Chuyển đổi object sang dictionary để trả về JSON"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_type': self.session_type,
            'user_message': self.user_message,
            'system_response': self.system_response,
            'timestamp': self.timestamp.isoformat()
        }