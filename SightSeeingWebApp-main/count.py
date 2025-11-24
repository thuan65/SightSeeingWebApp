from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createDataBase import Image

engine = create_engine("sqlite:///images.db")
Session = sessionmaker(bind=engine)
session = Session()

print(session.query(Image).count())  # Đếm tổng số ảnh
for img in session.query(Image).all():
    print(img.id, img.name, img.filename, img.tags)
