from flask import Flask
from flask_migrate import Migrate
from extensions import init_extensions

from faiss_loader import load_faiss_index

from Login.login import login_bp  
from Forum.forum import forum
from ChatBot.ChatBotRoute import chatBot_bp
from MapRouting.MapRoutingRoute import MapRouting_bp
from Search_Filter.search_filter import search_filter
from Search_Text.search_text import search_text
from imageSearch.imageSearchRoute import search_image_bp
from Weather.Weather import weatherForecast_bp
from SuggestionsFeedback.feedback import feedback_bp
from friends import friends_bp
from add_favorites.routes import favorite_bp
from place_module.nearby_import import nearby_import_bp


def create_app(config_class="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # app.config['SECRET_KEY'] = 'mysecretkey'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///FlaskDataBase.db'
    # app.config['UPLOAD_FOLDER'] = 'static/uploads'
    # app.config['JSON_AS_ASCII'] = False
    
    # app.config.from_object(config_class)

    # Khởi tạo extensions
    init_extensions(app)

    with app.app_context():
        load_faiss_index()


    # ---------------------------------------------------------
    # KẾT NỐI DB ẢNH VÀ REGISTER BLUEPRINT
    #  ---------------------------------------------------------
    app.register_blueprint(search_filter)
    app.register_blueprint(search_text)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(chatBot_bp)
    app.register_blueprint(forum)
    app.register_blueprint(search_image_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(weatherForecast_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(MapRouting_bp, url_prefix= "/MapRouting")
    app.register_blueprint(nearby_import_bp)

    return app
