from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import func, Boolean, UniqueConstraint
from datetime import datetime
from flask_login import UserMixin
from extensions import db, bcrypt

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    online = db.Column(Boolean, default=True)
    share_mode = db.Column(db.String(50), default="friends")  # hidden, friends

    # Quan hệ ORM
    posts = db.relationship("Post", back_populates="questioner", cascade="all, delete")
    answers = db.relationship("Answer", back_populates="answerer", cascade="all, delete")
    is_admin = db.Column(db.Boolean, default=False)

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)

    images = db.Column(db.Text)
    questioner_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    tag = db.Column(db.String, default="unanswered")
    privacy = db.Column(db.String(30), default='public', nullable=False)

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
    
class LiveLocation(db.Model):
    __tablename__ = 'live_locations'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Mối quan hệ: Một LiveLocation thuộc về một User
    user = db.relationship('User', backref=db.backref('location', uselist=False))


# === MODELS TỪ createDataBase.py (Cho users.db) ===

class FriendRequest(db.Model):
    __tablename__ = "friend_requests"
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    to_user = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=func.datetime("now", "localtime"))

    __table_args__ = (UniqueConstraint("from_user", "to_user", name="uq_from_to"),)

class Friendship(db.Model):
    __tablename__ = "friendships"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=func.datetime("now", "localtime"))

    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="uq_user_friend"),)

class Image(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    tags = db.Column(db.String)
    filename = db.Column(db.String)
    description = db.Column(db.Text)
    rating = db.Column(db.Float)
    rating_count = db.Column(db.Integer, default=1) # So luong nguoi danh gia
    address = db.Column(db.String)   # <── thêm dòng này

class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=func.datetime("now", "localtime"))

class Favorite(db.Model):
    __tablename__ = "favorites"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_id = db.Column(db.Integer, nullable=False)  # Bỏ ForeignKey
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "image_id", name="uq_user_image"),)

class FaissMapping(db.Model):
    __tablename__ = "faiss_mapping"

    id = db.Column(db.Integer, primary_key=True)    # index trong FAISS
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"))
