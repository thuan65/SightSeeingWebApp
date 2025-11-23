import csv
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

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
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    timestamp = Column(DateTime, default=func.now())


engine = create_engine("sqlite:///images.db")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def readCsv(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=';')
        next(reader, None)
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
