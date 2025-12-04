import os
import csv
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, DateTime,
    ForeignKey, Boolean, UniqueConstraint, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref


# =========================================================
#  FIX: ĐƯỜNG DẪN CHUẨN CHO DATABASE (KHÔNG DÙNG current_app)
# =========================================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

os.makedirs(INSTANCE_DIR, exist_ok=True)

DB_IMAGES = os.path.join(INSTANCE_DIR, "images.db")
DB_USERS = os.path.join(INSTANCE_DIR, "users.db")


# =========================================================
#  DATABASE ẢNH (images.db)
# =========================================================
Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tags = Column(String)
    filename = Column(String)
    description = Column(Text)
    rating = Column(Float)
    rating_count = Column(Integer, default=1)
    address = Column(String)

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    timestamp = Column(DateTime, default=func.datetime("now", "localtime"))

engine = create_engine(f"sqlite:///{DB_IMAGES}", echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


# =========================================================
#  DATABASE USER (users.db)
# =========================================================
UserBase = declarative_base()

class User(UserBase):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String(200), nullable=False)
    online = Column(Boolean, default=True)
    share_mode = Column(String(50), default="friends")

class Post(UserBase):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    content = Column(Text)
    questioner_id = Column(Integer, ForeignKey("user.id"))
    tag = Column(String, default="unanswered")
    created_at = Column(DateTime, server_default=func.datetime("now", "localtime"))

    answers = relationship("Answer", back_populates="post", cascade="all, delete")
    questioner = relationship("User", backref=backref("posts", lazy=True))

class Answer(UserBase):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    answerer_id = Column(Integer, ForeignKey("user.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, server_default=func.datetime("now", "localtime"))

    post = relationship("Post", back_populates="answers")
    answerer = relationship("User", backref=backref("answers", lazy=True))

class FriendRequest(UserBase):
    __tablename__ = "friend_requests"
    id = Column(Integer, primary_key=True)
    from_user = Column(Integer, ForeignKey("user.id"))
    to_user = Column(Integer, ForeignKey("user.id"))
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("from_user", "to_user", name="uq_from_to"),)

class Friendship(UserBase):
    __tablename__ = "friendships"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    friend_id = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="uq_user_friend"),)

class Favorite(UserBase):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    image_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "image_id", name="uq_user_image"),)

class ConversationHistory(UserBase):
    __tablename__ = "conversation_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_type = Column(String(50), nullable=False)
    user_message = Column(Text)
    system_response = Column(Text)
    timestamp = Column(DateTime, default=func.now())

class LiveLocation(UserBase):
    __tablename__ = "live_locations"
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    lat = Column(Float)
    lng = Column(Float)
    timestamp = Column(DateTime, default=func.now(), onupdate=func.now())
    user = relationship("User", backref=backref("location", uselist=False))

engine_users = create_engine(f"sqlite:///{DB_USERS}", echo=False)
UserSession = sessionmaker(bind=engine_users)
UserBase.metadata.create_all(engine_users)


# =========================================================
#  CSV IMPORT FUNCTION
# =========================================================
def readCsv(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=';')
        next(reader, None)
        for row in reader:
            data.append(row)
    return data

def normalizeTags(tagStr):
    if not tagStr: return ""
    tags = [t.strip() for t in tagStr.replace(";", ",").split(",") if t.strip()]
    return ", ".join(tags)

def addSingle(row, session):
    try:
        img = Image(
            id=int(row[0]) if row[0].isdigit() else None,
            name=row[1].strip(),
            tags=normalizeTags(row[2]),
            filename=row[3].strip(),
            description=row[4].strip(),
            rating=float(row[5]) if len(row) > 5 and row[5] else 0.0,
            rating_count=int(row[6]) if len(row) > 6 and row[6].isdigit() else 1
        )
        session.add(img)
        session.commit()
        print(f"Đã thêm {img.name}")
    except Exception as e:
        session.rollback()
        print(f"Lỗi thêm {row}: {e}")

def addData(csvPath):
    session = Session()
    for row in readCsv(csvPath):
        addSingle(row, session)
    session.close()
    print("Import CSV hoàn tất.")

if __name__ == "__main__":
    addData("data.csv")
