from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def init_extensions(app):
# Khởi tạo database, bcrypt và login manager
    db.init_app(app)
    bcrypt.init_app(app)
    