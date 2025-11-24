from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Place(Base):
    __tablename__ = 'places'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String)
    tags = Column(String)
    rating = Column(Float)
    description = Column(Text)

# Tạo database SQLite
engine = create_engine('sqlite:///places.db')
Base.metadata.create_all(engine)

# Thêm dữ liệu mẫu
Session = sessionmaker(bind=engine)
session = Session()

sample_places = [
    Place(
        name="Thung Lũng Tình Yêu",
        city="Đà Lạt",
        tags="thiên nhiên, yên tĩnh, lãng mạn",
        rating=4.7,
        description="Khu du lịch nổi tiếng với hồ và cảnh rừng thông tuyệt đẹp."
    ),
    Place(
        name="Bãi biển Mỹ Khê",
        city="Đà Nẵng",
        tags="biển, thư giãn, năng động",
        rating=4.6,
        description="Bãi biển dài, sạch và trong xanh, lý tưởng để nghỉ dưỡng."
    ),
    Place(
        name="Chợ Bến Thành",
        city="TP.HCM",
        tags="mua sắm, văn hóa, truyền thống",
        rating=4.3,
        description="Biểu tượng của Sài Gòn, nơi mua sắm và khám phá ẩm thực địa phương."
    ),
    Place(
        name="Vịnh Hạ Long",
        city="Quảng Ninh",
        tags="thiên nhiên, di sản, du thuyền",
        rating=4.9,
        description="Kỳ quan thiên nhiên thế giới với hàng nghìn hòn đảo đá vôi tuyệt đẹp."
    ),
]

session.add_all(sample_places)
session.commit()
print("✅ Database 'places.db' đã được tạo và thêm dữ liệu mẫu!")
