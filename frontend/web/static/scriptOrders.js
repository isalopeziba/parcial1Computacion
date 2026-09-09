const PRODUCTS_API = 'http://192.168.100.3:5003/api/products';
const ORDERS_API = 'http://192.168.100.3:5004/api/orders';

let products = [];
let orderItems = [];

function showMessage(message, type) {
    const messageElement = document.getElementById('order-message');
    messageElement.textContent = message;
    messageElement.className = `alert alert-${type}`;
    messageElement.style.display = 'block';
}

async function loadProducts() {
    const productSelect = document.getElementById('product-id');

    try {
        const response = await fetch(PRODUCTS_API);
        if (!response.ok) {
            throw new Error('No fue posible cargar los productos');
        }

        products = await response.json();
        productSelect.innerHTML = '<option value="">Seleccione un producto</option>';

        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} - $${Number(product.price).toFixed(2)} (stock: ${product.stock})`;
            option.disabled = Number(product.stock) < 1;
            productSelect.appendChild(option);
        });
    } catch (error) {
        productSelect.innerHTML = '<option value="">No hay productos disponibles</option>';
        showMessage(error.message, 'danger');
    }
}

function renderOrderItems() {
    const tableBody = document.querySelector('#order-items tbody');
    const totalElement = document.getElementById('order-total');
    tableBody.innerHTML = '';

    let total = 0;
    orderItems.forEach((item, index) => {
        const subtotal = Number(item.product.price) * item.quantity;
        total += subtotal;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.product.name}</td>
            <td>$${Number(item.product.price).toFixed(2)}</td>
            <td>${item.quantity}</td>
            <td>$${subtotal.toFixed(2)}</td>
            <td><button type="button" class="btn btn-danger btn-sm" data-index="${index}">Remove</button></td>
        `;
        row.querySelector('button').addEventListener('click', () => {
            orderItems.splice(index, 1);
            renderOrderItems();
        });
        tableBody.appendChild(row);
    });

    totalElement.textContent = total.toFixed(2);
}

function addOrderItem(event) {
    event.preventDefault();

    const productId = Number(document.getElementById('product-id').value);
    const quantity = Number(document.getElementById('quantity').value);
    const product = products.find(currentProduct => currentProduct.id === productId);

    if (!product || !Number.isInteger(quantity) || quantity <= 0) {
        showMessage('Seleccione un producto y una cantidad válida.', 'warning');
        return;
    }

    const existingItem = orderItems.find(item => item.product.id === productId);
    const requestedQuantity = (existingItem ? existingItem.quantity : 0) + quantity;
    if (requestedQuantity > Number(product.stock)) {
        showMessage('La cantidad solicitada supera el inventario disponible.', 'warning');
        return;
    }

    if (existingItem) {
        existingItem.quantity = requestedQuantity;
    } else {
        orderItems.push({ product, quantity });
    }

    renderOrderItems();
    document.getElementById('add-order-item-form').reset();
}

async function createOrder() {
    if (orderItems.length === 0) {
        showMessage('Agregue al menos un producto a la orden.', 'warning');
        return;
    }

    try {
        const response = await fetch(ORDERS_API, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                products: orderItems.map(item => ({
                    product_id: item.product.id,
                    quantity: item.quantity
                }))
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || 'No fue posible crear la orden');
        }

        showMessage(`Orden creada exitosamente. ID: ${data.order_id}`, 'success');
        orderItems = [];
        renderOrderItems();
        await loadProducts();
        await loadOrders();
    } catch (error) {
        showMessage(error.message, 'danger');
    }
}

async function loadOrders() {
    try {
        const response = await fetch(ORDERS_API, { credentials: 'include' });
        if (!response.ok) {
            throw new Error('No fue posible cargar las órdenes');
        }

        const orders = await response.json();
        const tableBody = document.querySelector('#orders-list tbody');
        tableBody.innerHTML = '';

        orders.forEach(order => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${order.id}</td>
                <td>$${Number(order.total).toFixed(2)}</td>
                <td>${order.status}</td>
                <td>${order.created_at ? new Date(order.created_at).toLocaleString() : ''}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (error) {
        showMessage(error.message, 'danger');
    }
}

document.getElementById('add-order-item-form').addEventListener('submit', addOrderItem);
document.getElementById('create-order-button').addEventListener('click', createOrder);
loadProducts();
loadOrders();


// para obtener lso items de una orden en especifico

async function searchOrderById() {
    const orderId = document.getElementById('search-order-id').value.trim();
    const resultBox = document.getElementById('order-search-result');

    if (!orderId || Number(orderId) < 1) {
        showMessage('Ingresa un ID de orden válido.', 'warning');
        return;
    }

    try {
        const response = await fetch(`${ORDERS_API}/${orderId}`, { credentials: 'include' });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Orden no encontrada');
        }

        const itemsText = data.items
            .map(item => `Producto #${item.product_id} - ${item.product_name} x${item.quantity} ($${Number(item.subtotal).toFixed(2)})`)
            .join('<br>');

        resultBox.innerHTML = `
            <strong>Orden #${data.id}</strong> — Total: $${Number(data.total).toFixed(2)} — Estado: ${data.status}<br>
            ${itemsText}
        `;
        resultBox.className = 'mt-2 alert alert-info';
        resultBox.style.display = 'block';
    } catch (error) {
        resultBox.className = 'mt-2 alert alert-danger';
        resultBox.textContent = error.message;
        resultBox.style.display = 'block';
    }
}

document.getElementById('search-order-button').addEventListener('click', searchOrderById);