from flask import Flask, flash, url_for, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()

app = Flask(__name__)

app.config["SECRET_KEY"] = "4QGeCtv1sDWokq9Rn8MF"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"

UPLOAD_FOLDER = "/Users/thomaspegler/OneDrive - Warwick Independent Schools Foundation/T.Pegler/Documents/Senior School/A-Level/Computer Science/NEA/NEA Python Project/app/static/Shop Images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

mail = Mail()
app.config["MAIL_SERVER"] = "priorsfieldhouse.co.uk"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = 1
app.config["MAIL_USERNAME"] = "wms@priorsfieldhouse.co.uk"
app.config["MAIL_PASSWORD"] = "Davies2018"
app.config["MAIL_DEFAULT_SENDER"] = ("Prior's Field WMS", "wms@priorsfieldhouse.co.uk")

db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

from .models import User, Order, Product, OrderItem, BasketItem, UserPassReset


with app.app_context():
    db.create_all()

from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from .main import main as main_blueprint
app.register_blueprint(main_blueprint)

from .admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint)

from .shop import shop as shop_blueprint
app.register_blueprint(shop_blueprint)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def handle_needs_login():
    flash("You have to be logged in to access this page.", category="is-danger")

    return redirect(url_for('auth.login', next=request.endpoint))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")