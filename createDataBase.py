from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    filename = Column(String)
    tags = Column(String)  
    description = Column(Text)  # Text cho nội dung dài

class Place(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)
    tags = Column(String)
    rating = Column(Float)
    description = Column(Text)

engine = create_engine("sqlite:///images.db") #tạo file
Base.metadata.create_all(engine)

if __name__ == "__main__":

    Session = sessionmaker(bind=engine)
    session = Session()

    # Thêm dữ liệu mẫu
    images = [
        Image(name="Cute Cat", filename="cat1.jpg", tags="cat, cute, animal"),
        Image(name="Black Virgin Mountain ", filename="mountain.jpg", tags="mountain, nature, landscape"),
        Image(name="Golden Retriever", filename="dog1.jpg", tags="dog, animal, pet",description="""Golden Retriever là một giống chó thân thiện, trung thành và rất thông minh. 
        Chúng thường được sử dụng làm chó dẫn đường, chó trị liệu và chó cứu hộ. 
        Với bộ lông vàng óng mượt và tính cách hiền hòa, chúng là người bạn tuyệt vời trong mỗi gia đình."""
        ),
        Image(name="Vinh Ha Long", filename="des1.jpg", tags="place", description= """Vịnh Hạ Long được Unesco nhiều lần công nhận là Di sản thiên nhiên của Thế giới 
ngày 16/9/2023, tại thủ đô Riyadh, Ả Rập Xê Út, UNESCO lại một lần nữa vinh danh và công nhận quần thể vịnh Hạ Long – quần đảo Cát Bà là Di sản thiên nhiên thế giới

""")
    ]
    session.add_all(images)
    session.commit()

    print(" Database created!")

    engine_places = create_engine("sqlite:///places.db")
    Base.metadata.create_all(engine_places)

    SessionPlaces = sessionmaker(bind=engine_places)
    session_places = SessionPlaces()

    places = [
        Place(
            name="Vịnh Hạ Long",
            city="Quảng Ninh",
            tags="biển, thiên nhiên, di sản",
            rating=4.9,
            description="Vịnh Hạ Long là Di sản thiên nhiên thế giới nổi tiếng với hàng nghìn hòn đảo đá vôi kỳ vĩ."
        ),
        Place(
            name="Núi Bà Đen",
            city="Tây Ninh",
            tags="núi, tâm linh, thiên nhiên",
            rating=4.7,
            description="Núi Bà Đen là ngọn núi cao nhất Nam Bộ, nổi tiếng với cáp treo và lễ hội chùa Bà Đen."
        ),
        Place(
            name="Phố cổ Hội An",
            city="Quảng Nam",
            tags="văn hóa, di sản, phố cổ",
            rating=4.8,
            description="Hội An là đô thị cổ được UNESCO công nhận là Di sản văn hóa thế giới, nổi tiếng với đèn lồng và kiến trúc cổ."
        ),
        Place(
            name="Sa Pa",
            city="Lào Cai",
            tags="núi, du lịch, thiên nhiên",
            rating=4.6,
            description="Sa Pa là thị trấn vùng cao nổi tiếng với ruộng bậc thang và đỉnh Fansipan – nóc nhà Đông Dương."
        ),
        Place(
            name="Đà Lạt",
            city="Lâm Đồng",
            tags="hoa, núi, nghỉ dưỡng",
            rating=4.8,
            description="Đà Lạt là thành phố ngàn hoa với khí hậu mát mẻ quanh năm, thích hợp cho nghỉ dưỡng và tham quan."
        ),
    ]

    session_places.add_all(places)
    session_places.commit()
    print("✅ Database places.db created!")

    print("\n🎉 Tất cả database đã được tạo thành công!")