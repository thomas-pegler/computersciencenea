from flask_login import UserMixin
from datetime import datetime
from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    isadmin = db.Column(db.Boolean, nullable=False, default=0)
    address_line1 = db.Column(db.String)
    address_line2 = db.Column(db.String)
    address_city = db.Column(db.String)
    address_county = db.Column(db.String)
    address_postcode = db.Column(db.String)

    orders = db.relationship('Order', backref="orderuser", lazy=True)
    basketitems = db.relationship('BasketItem', backref="basketuser", lazy=True)
    passreset = db.relationship('UserPassReset', backref="passresetuser", lazy=True)

    def __repr__(self):
        return f"('User #{self.id}', '{self.firstname}', '{self.lastname}', '{self.email}', '{self.isadmin}')"


class UserPassReset(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reset_key = db.Column(db.String, unique=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    has_activated = db.Column(db.Boolean, default=False)


class Order(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float)
    address_firstname = db.Column(db.String, nullable=False)
    address_lastname = db.Column(db.String, nullable=False)
    address_line1 = db.Column(db.String, nullable=False)
    address_line2 = db.Column(db.String)
    address_city = db.Column(db.String, nullable=False)
    address_county = db.Column(db.String)
    address_postcode = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False,  default='Unfulfilled')

    def __repr__(self):
        return f"('Order #{self.id}', '{self.orderuser.firstname}', '{self.orderuser.lastname}', '{self.date}', '{self.total}', '{self.status}')"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    shortdesc = db.Column(db.String)
    longdesc = db.Column(db.String)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer)
    mainimage = db.Column(db.String, nullable=False, default='Stock Image.svg')
    archived = db.Column(db.Boolean, default=False)

    orderitems = db.relationship('OrderItem', backref="orderproduct", lazy=True)
    basketitems = db.relationship('BasketItem', backref="basketproduct", lazy=True)

    def __repr__(self):
        return f"('Product #{self.id}', '{self.name}', '{self.shortdesc}', '{self.price}', '{self.stock}')"


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer)


class BasketItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer)
