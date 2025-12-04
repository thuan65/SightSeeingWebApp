# create_db.py
import csv
from __init__ import create_app
from extensions import db
from app import app

from models import Image, FriendRequest, Friendship, User, Feedback, User, Post, Answer, ConversationHistory, LiveLocation

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///FlaskDataBase.db'

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


def addSingle(row):
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
        db.session.add(img)
        db.session.commit()
        print(f"Da them {img.name}")
    except Exception as e:
        db.session.rollback()
        print(f"Loi khi them {row}: {e}")


def addData(csvPath):
    rows = readCsv(csvPath)
    for row in rows:
        addSingle(row)
    print("Database done.")


if __name__ == "__main__":
    csvPath = "data.csv"
    print(f"Doc du lieu tu '{csvPath}'")

    # Khi chạy ngoài Flask route, cần app context
    with app.app_context():
        db.create_all()
        addData(csvPath)