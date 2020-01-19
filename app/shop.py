from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from flask_mail import Message
from .models import Product, BasketItem, Order, OrderItem
from . import db, mail

shop = Blueprint("shop", __name__)


@shop.route("/shop")
@login_required
def shop_main():
    products = Product.query.filter_by(archived=False).all()

    return render_template("shop_main.html", products=products)


@shop.route("/shop/product/<product_id>")
@login_required
def products(product_id):
    product = Product.query.filter_by(id=product_id, archived=False).first()

    if not current_user.isadmin:
        if not product:
            flash("Not a valid product.", category="is-danger")

            return redirect(url_for("shop.shop_main"))

        else:
            return render_template("shop_product.html", product=product)
    else:
        flash("User status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@shop.route("/shop/product/<product_id>", methods=["POST"])
@login_required
def product_post(product_id):
    quantityupdated = False

    quantity = int(request.form.get("quantity"))

    basket = BasketItem.query.filter_by(user_id=current_user.id).all()

    for item in basket:
        if int(item.product_id) == int(product_id):
            item.quantity = (int(item.quantity) + quantity)

            db.session.commit()

            quantityupdated = True

    if quantityupdated == False:
        new_basketitem = BasketItem(user_id=current_user.id, product_id=product_id, quantity=quantity)

        db.session.add(new_basketitem)
        db.session.commit()

    flash("Product added to your basket successfully.", category="is-success")

    return redirect(url_for("shop.shop_main"))


@shop.route("/shop/search/<searchterm>")
@login_required
def shop_search(searchterm):
    searchresults = Product.query.filter(Product.name.like(searchterm + "%")).filter_by(archived=False).all()

    if not searchresults:
        flash("No products matched your search.", category="is-danger")

    return redirect(url_for("shop.shop_main", products=searchresults))


@shop.route("/shop/search", methods=["POST"])
@login_required
def shop_search_post():
    searchterm = request.form.get("searchterm")
    searchresults = Product.query.filter(Product.name.like("%" + searchterm + "%")).filter_by(archived=False).all()

    if not searchresults:
        flash("No products matched your search.", category="is-danger")

    return redirect(url_for("shop.shop_main", products=searchresults))


@shop.route("/orders")
@login_required
def orders():
    if not current_user.isadmin:
        userorders = Order.query.filter_by(user_id=current_user.id).all()

        return render_template("user_orders.html", userorders=userorders)
    else:
        flash("User status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@shop.route("/orders/manage/<order_id>")
@login_required
def usermanageorder(order_id):
    if not current_user.isadmin:
        order = Order.query.filter_by(id=order_id).first()

        if order == None:
            flash("Order does not exist.", category="is-danger")

        else:
            if order.user_id == current_user.id:
                orderitems = OrderItem.query.filter_by(order_id=order_id).all()

                return render_template("user_manageorder.html", order=order, orderitems=orderitems)

            else:
                flash("Order does not belong to your account.", category="is-danger")

        return redirect(url_for("shop.orders"))
    else:
        flash("User status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@shop.route("/orders/manage/<order_id>", methods=["POST"])
@login_required
def usermanageorder_post(order_id):
    order = Order.query.filter_by(id=order_id).first()

    if not current_user.isadmin:
        addressfirstname = request.form.get("addressfirstname")
        addresslastname = request.form.get("addresslastname")
        address1 = request.form.get("address1")
        address2 = request.form.get("address2")
        city = request.form.get("city")
        county = request.form.get("county")
        postcode = request.form.get("postcode")

        order.address_firstname = addressfirstname
        order.address_lastname = addresslastname
        order.address_line1 = address1
        order.address_line2 = address2
        order.address_city = city
        order.address_county = county
        order.address_postcode = postcode


        db.session.commit()

        flash("Your changes have successfully been made.", category="is-success")

        return redirect(url_for("shop.orders"))

    else:
        flash("User status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@shop.route("/orders/manage/delete/<order_id>", methods=["POST"])
@login_required
def userdeleteorder_post(order_id):
    order = Order.query.filter_by(id=order_id).first()
    orderitems = OrderItem.query.filter_by(order_id=order_id).all()

    if not current_user.isadmin:
        for item in orderitems:
            db.session.delete(item)

        db.session.delete(order)
        db.session.commit()

        flash("Order successfully deleted.", category="is-success")

        return redirect(url_for("shop.orders"))

    else:
        flash("User status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@shop.route("/basket")
@login_required
def basket():
    if not current_user.isadmin:
        basket = BasketItem.query.filter_by(user_id=current_user.id).all()
        itemsremoved = False

        totalprice = 0
        items = 0
        for item in basket:
            if item.basketproduct.archived == False:
                totalprice += (item.basketproduct.price * item.quantity)
                items += item.quantity
            else:
                itemsremoved = True
                db.session.delete(item)
                db.session.commit()

        if itemsremoved:
            flash("Item(s) were removed from your basket.", category="is-danger")

        return render_template("shop_basket.html", items=items, basket=basket, totalprice=totalprice)

    else:
        flash("User status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@shop.route("/<page>/editbasket/<product_id>", methods=["POST"])
@login_required
def editbasket_post(page, product_id):
    basketitem = BasketItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    db.session.delete(basketitem)
    db.session.commit()

    if page == "basket":
        return redirect(url_for("shop.basket"))

    elif page == "checkout":
        return redirect(url_for("shop.checkout"))


@shop.route("/checkout")
@login_required
def checkout():
    if not current_user.isadmin:
        basket = BasketItem.query.filter_by(user_id=current_user.id).all()
        itemsremoved = False

        if basket == []:
            flash("Unable to proceed to checkout. Your basket is empty.", category="is-danger")
            return redirect(request.referrer)

        totalprice = 0
        items = 0
        for item in basket:
            if item.basketproduct.archived == False:
                totalprice += (item.basketproduct.price * item.quantity)
                items += item.quantity

            else:
                itemsremoved = True

                db.session.delete(item)
                db.session.commit()

        if itemsremoved:
            flash("Item(s) were removed from your basket.", category="is-danger")

        return render_template("shop_checkout.html", items=items, basket=basket, totalprice=totalprice)

    else:
        flash("User status required to visit this page.", category="is-danger")

        return redirect(url_for("main.index"))


@shop.route("/checkout", methods=["POST"])
@login_required
def checkout_post():
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    address1 = request.form.get("address1")
    address2 = request.form.get("address2")
    city = request.form.get("city")
    county = request.form.get("county")
    postcode = request.form.get("postcode")

    basket = BasketItem.query.filter_by(user_id=current_user.id).all()
    totalprice = 0
    ordersuccessfull = True

    new_order = Order(user_id=current_user.id, address_firstname=firstname, address_lastname=lastname, address_line1=address1, address_line2=address2, address_city=city, address_county=county, address_postcode=postcode)
    db.session.add(new_order)
    db.session.commit()

    for item in basket:
        if item.basketproduct.stock - item.quantity >= 0:
            totalprice += (item.basketproduct.price * item.quantity)

            orderitem = OrderItem(order_id=new_order.id, product_id=item.basketproduct.id, quantity=item.quantity)

            product = Product.query.get(item.basketproduct.id)
            product.stock = (item.basketproduct.stock - item.quantity)

            db.session.add(orderitem)
            db.session.delete(item)
        else:
            ordersuccessfull = False

            item.quantity = item.basketproduct.stock

    if ordersuccessfull:
        order = Order.query.get(new_order.id)
        order.total = totalprice

        db.session.commit()

        msg = Message(recipients=[current_user.email], subject="Order #%s Confirmation" %(order.id))
        msg.body = "Order Confirmation"
        msg.html = render_template("email_orderconfirmation.html", order=new_order, orderitems=OrderItem.query.filter_by(order_id=(new_order.id)).all())
        mail.send(msg)

        flash("Your order has been placed successfully.", category="is-success")

        return redirect(url_for("shop.orders"))

    else:
        db.session.delete(new_order)
        db.session.commit()

        flash("Your order could not be placed. Insufficient stock available.", category="is-danger")

        return redirect(url_for("shop.checkout"))