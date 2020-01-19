from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import check_password_hash
from flask_login import login_required, current_user
from .models import Order, OrderItem
from . import db

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/profile")
@login_required
def profile():
    if current_user.isadmin:
        return render_template("admin_profile.html")

    else:
        return render_template("user_profile.html")


@main.route("/profile/edit", methods=["POST"])
@login_required
def profile_post():
    if current_user.isadmin:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        password = request.form.get("password")

        if not check_password_hash(current_user.password, password):
            flash("Please check your password and try again.", category="is-danger")

        else:
            current_user.firstname = firstname
            current_user.lastname = lastname

            db.session.commit()

            flash("Your changes have successfully been made.", category='is-success')

        return redirect(url_for("admin.profile"))

    else:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        password = request.form.get("password")
        address1 = request.form.get("address1")
        address2 = request.form.get("address2")
        city = request.form.get("city")
        county = request.form.get("county")
        postcode = request.form.get("postcode")

        if not check_password_hash(current_user.password, password):
            flash("Please check your password and try again.", category="is-danger")

        else:
            current_user.firstname = firstname
            current_user.lastname = lastname
            current_user.address_line1 = address1
            current_user.address_line2 = address2
            current_user.address_city = city
            current_user.address_county = county
            current_user.address_postcode = postcode

            db.session.commit()

            flash("Your changes have successfully been made.", category='is-success')

        return redirect(url_for("main.profile"))


@main.route("/testing")
@login_required
def test():
    order_id = 3
    order = Order.query.filter_by(id=order_id).first()
    orderitems = OrderItem.query.filter_by(order_id=order_id).all()

    return render_template("email_orderconfirmation.html", order=order, orderitems=orderitems)