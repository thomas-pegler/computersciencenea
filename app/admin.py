from flask import flash, Blueprint, render_template, redirect, url_for, request
import os
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from .models import User, UserPassReset, Product, Order, OrderItem, BasketItem
from . import db, app

admin = Blueprint("admin", __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg']


@admin.route("/dashboard")
@login_required
def dashboard():
    if current_user.isadmin:
        numusers = len(User.query.all())
        numproducts = len(Product.query.all())
        numorders = len(Order.query.all())
        products = Product.query.all()

        return render_template("admin_dashboard.html", numusers=numusers, numproducts=numproducts, numorders=numorders, products=products)

    else:
        return redirect(url_for("main.index"))


@admin.route("/ordersearch", methods=["POST"])
def ordersearch_post():
    print(Order.query.filter_by(id=request.form.get("order_id")).first())

    return redirect(url_for("admin.dashboard"))


@admin.route("/productsearch", methods=["POST"])
def productsearch_post():
    print(Product.query.filter_by(id=request.form.get("product_id")).first())

    return redirect(url_for("admin.dashboard"))


@admin.route("/usermanager")
@login_required
def usermanager():
    if current_user.isadmin:
        users = User.query.all()

        return render_template("admin_usermanager.html", users=users)

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/usermanager/<user_id>")
@login_required
def manageuser(user_id):
    user = User.query.filter_by(id=user_id).first()

    if current_user.isadmin:
        if not user:
            flash("Not a valid user ID.", category="is-danger")

            return redirect(url_for("admin.usermanager"))

        else:
            return render_template("admin_manageuser.html", user=user)
    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/usermanager/<user_id>", methods=["POST"])
@login_required
def manageuser_post(user_id):
    user = User.query.filter_by(id=user_id).first()

    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    password = request.form.get("password")
    isadmin = True if request.form.get("isadmin") else False

    if not user.isadmin:
        address1 = request.form.get("address1")
        address2 = request.form.get("address2")
        city = request.form.get("city")
        county = request.form.get("county")
        postcode = request.form.get("postcode")

        user.address_line1 = address1
        user.address_line2 = address2
        user.address_city = city
        user.address_county = county
        user.address_postcode = postcode

    user.firstname = firstname
    user.lastname = lastname
    user.isadmin = isadmin

    if password != "":
        if len(password) < 8:
            flash("Password needs to be at least 8 characters long.", category="is-danger")

            return redirect(url_for("admin.manageuser", user_id=user_id))

    db.session.commit()

    flash("Your changes have successfully been made.", category='is-success')

    return redirect(url_for("admin.usermanager"))


@admin.route("/usermanager/add")
@login_required
def adduser():
    if current_user.isadmin:
        return render_template("admin_adduser.html")

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/usermanager/add", methods=["POST"])
@login_required
def adduser_post():
    if current_user.isadmin:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        isadmin = True if request.form.get("isadmin") else False

        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email address already exists", category="is-danger")

            return redirect(url_for("admin.adduser"))

        new_user = User(email=email, firstname=firstname, lastname=lastname, password=generate_password_hash(password, method="sha256"), isadmin=isadmin)

        db.session.add(new_user)
        db.session.commit()

        flash("Account successfully created.", category="is-success")

        return redirect(url_for("admin.usermanager"))

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/usermanager/delete/<user_id>", methods=["POST"])
@login_required
def deleteuser_post(user_id):
    user = User.query.filter_by(id=user_id).first()
    orders = Order.query.filter_by(user_id=user_id).all()
    passreset = UserPassReset.query.filter_by(user_id=user.id).first()
    basketitems = BasketItem.query.filter_by(user_id=user.id).all()

    if current_user.isadmin:
        for item in basketitems:
            db.session.delete(item)

        for order in orders:
            orderitems = OrderItem.query.filter_by(order_id=order.id).all()

            for item in orderitems:
                db.session.delete(item)

            db.session.delete(order)

        if passreset:
            db.session.delete(passreset)

        db.session.delete(user)

        db.session.commit()

        flash("Account successfully deleted.", category="is-success")

        return redirect(url_for("admin.usermanager"))

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/productmanager")
@login_required
def productmanager():
    if current_user.isadmin:
        products = Product.query.all()

        return render_template("admin_productmanager.html", products=products)

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/productmanager/<product_id>")
@login_required
def manageproduct(product_id):
    product = Product.query.filter_by(id=product_id).first()

    if current_user.isadmin:
        if not product:
            flash("Not a valid product ID.", category="is-danger")

            return redirect(url_for("admin.productmanager"))

        else:
            return render_template("admin_manageproduct.html", product=product)
    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/productmanager/<product_id>", methods=["POST"])
@login_required
def manageproduct_post(product_id):
    product = Product.query.filter_by(id=product_id).first()

    if current_user.isadmin:
        productname = request.form.get("productname")
        shortdesc = request.form.get("shortdesc")
        longdesc = request.form.get("longdesc")
        price = request.form.get("price")
        stock = request.form.get("stock")
        mainimage = request.files['mainimage']
        archived = True if request.form.get("archived") else False

        if mainimage and allowed_file(mainimage.filename):
            filename = secure_filename(mainimage.filename)
            mainimage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            product.mainimage = filename

        product.name = productname
        product.shortdesc = shortdesc
        product.longdesc = longdesc
        product.price = price
        product.stock = stock
        product.archived = archived

        db.session.commit()

        flash("Your changes have successfully been made.", category="is-success")

        return redirect(url_for("admin.productmanager"))

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/productmanager/add")
@login_required
def addproduct():
    if current_user.isadmin:
        return render_template("admin_addproduct.html")

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/productmanager/add", methods=["POST"])
@login_required
def addproduct_post():
    if current_user.isadmin:
        productname = request.form.get("productname")
        shortdesc = request.form.get("shortdesc")
        longdesc = request.form.get("longdesc")
        price = request.form.get("price")
        stock = request.form.get("stock")
        mainimage = request.files['mainimage']

        new_product = Product(name=productname, shortdesc=shortdesc, longdesc=longdesc, price=price, stock=stock)
        db.session.add(new_product)
        db.session.commit()

        if mainimage and allowed_file(mainimage.filename):
            filename = secure_filename(mainimage.filename)
            mainimage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            new_product.mainimage = mainimage
            db.session.commit()

        flash("Product successfully added.", category="is-success")

        return redirect(url_for("admin.productmanager"))

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/productmanager/archive/<product_id>", methods=["POST"])
@login_required
def archiveproduct_post(product_id):
    product = Product.query.filter_by(id=product_id).first()

    if current_user.isadmin:
        print('hello')
        product.archived = True
        db.session.commit()

        flash("Product successfully archived.", category="is-success")

        return redirect(url_for("admin.productmanager"))

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/stocklevels")
@login_required
def stocklevels():
    if current_user.isadmin:
        products = Product.query.all()

        return render_template("admin_stocklevels.html", products=products)

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/ordermanager")
@login_required
def ordermanager():
    if current_user.isadmin:
        orders = Order.query.all()

        return render_template("admin_ordermanager.html", orders=orders)

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/ordermanager/<order_id>")
@login_required
def manageorder(order_id):
    order = Order.query.filter_by(id=order_id).first()
    orderitems = OrderItem.query.filter_by(order_id=order_id).all()

    if current_user.isadmin:
        if not order:
            return redirect(url_for("admin.ordermanager"))

        else:
            return render_template("admin_manageorder.html", order=order, orderitems=orderitems)
    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/ordermanager/<order_id>", methods=["POST"])
@login_required
def manageorder_post(order_id):
    order = Order.query.filter_by(id=order_id).first()

    if current_user.isadmin:
        status = request.form.get("status")
        addressfirstname = request.form.get("addressfirstname")
        addresslastname = request.form.get("addresslastname")
        address1 = request.form.get("address1")
        address2 = request.form.get("address2")
        city = request.form.get("city")
        county = request.form.get("county")
        postcode = request.form.get("postcode")

        order.status = status
        order.address_firstname = addressfirstname
        order.address_lastname = addresslastname
        order.address_line1 = address1
        order.address_line2 = address2
        order.address_city = city
        order.address_county = county
        order.address_postcode = postcode


        db.session.commit()

        flash("Your changes have successfully been made.", category="is-success")

        return redirect(url_for("admin.ordermanager"))

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@admin.route("/ordermanager/delete/<order_id>", methods=["POST"])
@login_required
def deleteorder_post(order_id):
    order = Order.query.filter_by(id=order_id).first()
    orderitems = OrderItem.query.filter_by(order_id=order_id).all()

    if current_user.isadmin:
        for item in orderitems:
            db.session.delete(item)

        db.session.delete(order)
        db.session.commit()

        flash("Order successfully deleted.", category="is-success")

        return redirect(url_for("admin.ordermanager"))

    else:
        flash("Admin status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))