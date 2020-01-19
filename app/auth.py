from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from datetime import datetime, timedelta
import uuid
from .models import User, UserPassReset
from . import db, mail

auth = Blueprint("auth", __name__)


def make_key():
    return uuid.uuid4()


def redirect_dest(fallback):
    dest = request.args.get('next')

    try:
        dest_url = url_for(dest)

    except:
        return redirect(fallback)

    return redirect(dest_url)


@auth.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    else:
        return render_template("login.html")


@auth.route("/login", methods=["GET", "POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")
    remember = True if request.form.get("remember") else False
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password): 
        flash("Please check your login details and try again.", category="is-danger")

        return redirect(url_for("auth.login"))

    login_user(user, remember=remember)

    flash("Login successful.", category="is-success")

    if current_user.isadmin:
        return redirect_dest(fallback=url_for('admin.dashboard'))
    else:
        return redirect_dest(fallback=url_for('shop.shop_main'))


@auth.route("/signup")
def signup():
    return render_template("signup.html")


@auth.route("/signup", methods=["POST"])
def signup_post():
    email = request.form.get("email")
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    password = request.form.get("password")

    user = User.query.filter_by(email=email).first()

    if user:
        flash("Email address already exists", category="is-danger")

        return redirect(url_for("auth.signup"))

    if len(password) < 8:
        flash("Password needs to be at least 8 characters long.", category="is-danger")

        return redirect(url_for("auth.signup"))

    new_user = User(email=email, firstname=firstname, lastname=lastname, password=generate_password_hash(password, method="sha256"))

    db.session.add(new_user)
    db.session.commit()

    flash("Account successfully created. Please login.", category="is-success")

    return redirect(url_for("auth.login"))


@auth.route("/logout")
@login_required
def logout():
    logout_user()

    flash("Logout successfull.", category="is-success")

    return redirect(url_for("main.index"))


@auth.route("/passreset/request")
def passresetrequest():
    return render_template("passreset_request.html")


@auth.route("/passreset/request", methods=["POST"])
def passresetrequest_post():
    email = request.form.get("email")

    if User.query.filter_by(email=email).first():
        user = User.query.filter_by(email=email).one()

        if UserPassReset.query.filter_by(user_id=user.id).first():
            pwalready = UserPassReset.query.filter_by(user_id=user.id).first()

            if pwalready.has_activated == False:
                pwalready.datetime = datetime.now()

                key = pwalready.reset_key
            else:
                key = make_key()
                pwalready.reset_key = str(key)
                pwalready.datetime = datetime.now()
                pwalready.has_activated = False
        else:
            key = make_key()
            user_reset = UserPassReset(user_id=user.id, reset_key=str(key))
            db.session.add(user_reset)

        db.session.commit()

        link = ("http://127.0.0.1:5000/passreset/" + str(key))

        msg = Message(recipients=[user.email], subject="Password Reset")
        msg.body = "Password Reset"
        msg.html = render_template("email_passreset.html", user=user, link=link)
        mail.send(msg)

        flash("Check your email for a link to reset your password. Link expires in 24 hours.", category="is-success")

        return redirect(url_for("main.index"))
    else:
        flash("This email is not registered.", category="is-danger")

        return redirect(url_for("auth.passresetrequest"))


@auth.route("/passreset/<key>")
def passreset(key):
    passresetkey = UserPassReset.query.filter_by(reset_key=key).one()
    generated_by = datetime.utcnow() - timedelta(hours=24)

    if passresetkey.has_activated is True:
        flash("Please request a new link, reset link has previously been used.", category="is-danger")

        return redirect(url_for("auth.passresetrequest"))

    if passresetkey.datetime < generated_by:
        flash("Please request a new link, password reset link has expired.", category="is-danger")

        return redirect(url_for("auth.passresetrequest"))

    return render_template('passreset.html', key=key)


@auth.route("/passreset/<key>", methods=["POST"])
def passreset_post(key):
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")

    if password1 != password2:
        flash("Your passwords didn't match.", category="is-danger")

        return redirect(url_for("auth.passreset", key=key))

    if len(password1) < 8:
        flash("Password needs to be at least 8 characters long.", category="is-danger")

        return redirect(url_for("auth.passreset", key=key))

    user_reset = UserPassReset.query.filter_by(reset_key=key).one()

    user = User.query.filter_by(id=user_reset.user_id).first()
    user.password = generate_password_hash(password1, method="sha256")

    db.session.commit()

    try:
        user = User.query.filter_by(id=user_reset.user_id).first()
        user.password = generate_password_hash(password1, method="sha256")

        db.session.commit()
    except:
        flash("An error occurred while changing your password.", category="is-danger")

        db.session.rollback()

        return redirect(url_for("auth.passreset", key=key))

    user_reset.has_activated = True

    db.session.commit()

    flash("Your password has been reset successfully.", category="is-success")

    return redirect(url_for("auth.login"))