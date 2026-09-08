
CREATE DATABASE IF NOT EXISTS orders_db;
USE orders_db;

CREATE TABLE IF NOT EXISTS orders (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_name varchar(255) NOT NULL,
    user_email varchar(255) NOT NULL,
    total decimal(10,2) NOT NULL,
    status varchar(255) DEFAULT 'completada',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    order_id int NOT NULL,
    product_id int NOT NULL,
    quantity int NOT NULL,
    unitprice decimal(10,2) NOT NULL,
    subtotal decimal(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

