from sqlalchemy import create_engine, Column, Integer, String,Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    filename = Column(String)
    tags = Column(String)  
    description = Column(Text)  # Text cho nội dung dài



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
        Image(name="Vinh Ha Long", filename="des1.jpg", tags="place", description= """ịnh Hạ Long được Unesco nhiều lần công nhận là Di sản thiên nhiên của Thế giới 
ngày 16/9/2023, tại thủ đô Riyadh, Ả Rập Xê Út, UNESCO lại một lần nữa vinh danh và công nhận quần thể vịnh Hạ Long – quần đảo Cát Bà là Di sản thiên nhiên thế giới

""")
    ]
    session.add_all(images)
    session.commit()

    print(" Database created!")

