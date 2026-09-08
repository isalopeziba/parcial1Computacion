from db.db import db


class OrderModel(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255), nullable=False)
    user_email = db.Column(db.String(255), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(255), default='Pendiente')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    items = db.relationship('OrderItemModel', back_populates='order', cascade='all, delete-orphan')


    def __init__(self, user_name, user_email, total, status='Pendiente'):
        self.user_name = user_name
        self.user_email = user_email
        self.total = total
        self.status = status


class OrderItemModel(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unitprice = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    order = db.relationship('OrderModel', back_populates='items')

    def __init__(self, product_id, quantity, unitprice, subtotal, order_id=None):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.unitprice = unitprice
        self.subtotal = subtotal