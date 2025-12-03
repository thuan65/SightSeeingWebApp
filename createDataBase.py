import csv
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tags = Column(String)
    filename = Column(String)
    description = Column(Text)
    rating = Column(Float)
    rating_count = Column(Integer, default=1) # So luong nguoi danh gia

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    timestamp = Column(DateTime, default=func.datetime("now", "localtime"))

engine = create_engine("sqlite:///instance/images.db")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

UserBase = declarative_base()

class User(UserBase):
    __tablename__ = "user"  
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    # nếu có thêm cột password, email... giữ nguyên

# Bảng lưu lời mời (pending / accepted / rejected / cancelled)
class FriendRequest(UserBase):
    __tablename__ = "friend_requests"
    id = Column(Integer, primary_key=True)
    from_user = Column(Integer, ForeignKey("user.id"), nullable=False)
    to_user = Column(Integer, ForeignKey("user.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending|accepted|rejected|cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    # tránh duplicate pending requests
    __table_args__ = (UniqueConstraint("from_user", "to_user", name="uq_from_to"),)

# Bảng lưu quan hệ bạn bè (một dòng thể hiện 1 kết bạn)
class Friendship(UserBase):
    __tablename__ = "friendships"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="uq_user_friend"),)

class Favorite(UserBase):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    image_id = Column(Integer, nullable=False)  # Bỏ ForeignKey
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "image_id", name="uq_user_image"),)
    
# Kết nối tới users.db (instance)
engine_users = create_engine("sqlite:///instance/users.db", echo=False)
UserSession = sessionmaker(bind=engine_users)

# Tạo tables (chạy 1 lần)
UserBase.metadata.create_all(engine_users)

def readCsv(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=';')
        next(reader, None)  # Bỏ header
        for row in reader:
            data.append(row)
    return data


def normalizeTags(tagStr):
    if not tagStr:
        return ""
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
        print(f"Da them {img.name}")
    except Exception as e:
        session.rollback()
        print(f"Loi khi them {row}: {e}")


def addData(csvPath):
    session = Session()
    rows = readCsv(csvPath)
    for row in rows:
        addSingle(row, session)
    session.close()
    print("Database done.")


if __name__ == "__main__":
    csvPath = "data.csv"
    print(f"Doc du lieu tu '{csvPath}'")
    addData(csvPath)