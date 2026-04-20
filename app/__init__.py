import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Railway provides a persistent volume path, or fallback to local
    data_dir = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "db"))
    os.makedirs(data_dir, exist_ok=True)

    db_path = os.path.join(data_dir, "portal.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-in-prod")

    db.init_app(app)

    from app.routes.clients import clients_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp

    app.register_blueprint(clients_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

    return app
