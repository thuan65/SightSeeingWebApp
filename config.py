class Config:
    SECRET_KEY = "mysecretkey"
    SQLALCHEMY_DATABASE_URI = "sqlite:///FlaskDataBase.db"
    UPLOAD_FOLDER = "static/uploads"
    JSON_AS_ASCII = False

class DevelopmentConfig(Config):
    DEBUG = True
