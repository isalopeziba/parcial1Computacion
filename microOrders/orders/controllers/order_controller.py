from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, jsonify, session
from orders.models.order_model import OrderModel as Order, OrderItemModel as OrderItem
from db.db import db
import requests
import os


order_controller = Blueprint(
    'order_controller',
      __name__)


# todas las ordenes realizadas
@order_controller.route('/api/orders', methods=['GET']) 
def get_all_orders(): 

    #esto es   validacion de errores, manejo de errores si no hay incio valido
    username = session.get('username')
    if not username:
        return jsonify({'message': 'NO hay un inicio de sesión valido'}), 401


    order = Order.query.filter_by(user_name=username).all()
    result = [
        {
            "id": current_order.id,
            "user_name": current_order.user_name,
            "user_email": current_order.user_email,
            "total": str(current_order.total),
            "status": current_order.status,
            "created_at": current_order.created_at.isoformat() if current_order.created_at else None
        }
        for current_order in order
    ]

    return jsonify(result), 200


# obtener una los items de una orden por su id
  
@order_controller.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    username = session.get('username')
    if not username:
        return jsonify({'message': 'No hay un inicio de sesión válido'}), 401

    order = Order.query.get_or_404(order_id)
    if order.user_name != username:
        return jsonify({'message': 'Orden no encontrada'}), 404

    try:
        products_base = discover_service('products')
        products_response = requests.get(f'{products_base}/api/products', timeout=5)
        products_response.raise_for_status()
        product_names = {
            product['id']: product['name']
            for product in products_response.json()
        }
    except (requests.RequestException, KeyError, TypeError, ValueError, RuntimeError):
        return jsonify({'message': 'No fue posible consultar los productos'}), 502

    items = OrderItem.query.filter_by(order_id=order.id).all()
    items_list = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product_names.get(item.product_id, 'Producto no disponible'),
            "quantity": item.quantity,
            "unit_price": str(item.unitprice),
            "subtotal": str(item.subtotal)
        }
        for item in items
    ]

    return jsonify({
        "id": order.id,
        "user_name": order.user_name,
        "user_email": order.user_email,
        "total": str(order.total),
        "status": order.status,
        "created_at": order.created_at,
        "items": items_list
    }), 200



  
def discover_service(service_name):
    consul_url = f"http://consul:8500/v1/health/service/{service_name}?passing"
    resp = requests.get(consul_url, timeout=3)
    resp.raise_for_status()
    instances = resp.json()
    if not instances:
        raise RuntimeError(f"No hay instancias saludables de {service_name} en Consul")
    service = instances[0]['Service']
    return f"http://{service['Address']}:{service['Port']}"




# crear una orden
@order_controller.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'message': 'Petición mal formada'}), 400

    user_name = session.get('username')
    user_email = session.get('email')
    if not user_name or not user_email:
        return jsonify({'message': 'No hay sesión de usuario válida'}), 401


    products = data.get('products')
    if not isinstance(products, list) or not products:
        return jsonify({'message': 'Información de productos inválida'}), 400

    requested = {}
    for item in products:
        if not isinstance(item, dict):
            return jsonify({'message': 'Información de productos inválida'}), 400
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        if (
            isinstance(product_id, bool) or not isinstance(product_id, int)
            or isinstance(quantity, bool) or not isinstance(quantity, int)
            or quantity <= 0
        ):
            return jsonify({'message': 'Las cantidades deben ser mayores a cero'}), 400
        requested[product_id] = requested.get(product_id, 0) + quantity

    #  Descubrimiento dinámico vía Consul  
    try:
        products_base = discover_service('products')
    except (requests.RequestException, RuntimeError):
        return jsonify({'message': 'No fue posible descubrir el servicio de productos'}), 500
    products_url = products_base + '/api/products'

    validated_items = []
    total_sale = Decimal('0.00')

    try:
        for product_id, quantity in requested.items():
            response = requests.get(f'{products_url}/{product_id}', timeout=5)  # se llama a productos gracias al consul
            if response.status_code == 404:
                return jsonify({'message': f'Producto con ID {product_id} no existe'}), 404
            response.raise_for_status()
            product = response.json()
            stock = int(product['stock'])
            price = Decimal(str(product['price']))
            if stock < quantity:
                return jsonify({'message': f'Inventario insuficiente para el producto {product_id}'}), 409
            subtotal = price * quantity
            total_sale += subtotal
            validated_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': price,
                'subtotal': subtotal,
                'stock': stock,
                'product': product
            })
    except (requests.RequestException, KeyError, TypeError, ValueError, InvalidOperation):
        return jsonify({'message': 'No fue posible consultar el servicio de productos'}), 500

    updated_items = []
    try:
        for item in validated_items:
            product = item['product']
            response = requests.put(
                f"{products_url}/{item['product_id']}",
                json={
                    'name': product['name'],
                    'description': product.get('description'),
                    'price': product['price'],
                    'stock': item['stock'] - item['quantity']
                },
                timeout=5
            )
            response.raise_for_status()
            updated_items.append(item)
    except (requests.RequestException, KeyError):
        for item in updated_items:
            product = item['product']
            try:
                requests.put(
                    f"{products_url}/{item['product_id']}",
                    json={
                        'name': product['name'],
                        'description': product.get('description'),
                        'price': product['price'],
                        'stock': item['stock']
                    },
                    timeout=5
                )
            except requests.RequestException:
                pass
        return jsonify({'message': 'No fue posible actualizar el inventario'}), 500

    try:
        new_order = Order(user_name=user_name, user_email=user_email, total=total_sale, status='completada')
        for item in validated_items:
            new_order.items.append(OrderItem(
                product_id=item['product_id'],
                quantity=item['quantity'],
                unitprice=item['unit_price'],
                subtotal=item['subtotal']
            ))
        db.session.add(new_order)
        db.session.commit()
    except Exception:
        db.session.rollback()
        for item in validated_items:
            product = item['product']
            try:
                requests.put(
                    f"{products_url}/{item['product_id']}",
                    json={
                        'name': product['name'],
                        'description': product.get('description'),
                        'price': product['price'],
                        'stock': item['stock']
                    },
                    timeout=5
                )
            except requests.RequestException:
                pass
        return jsonify({'message': 'No fue posible guardar la orden'}), 500

    return jsonify({'message': 'Orden creada exitosamente', 'order_id': new_order.id}), 201