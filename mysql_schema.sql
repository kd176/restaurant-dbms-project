-- ====================================================================
-- Academic DBMS Project: Restaurant Management System (MySQL Dialect)
-- Compatible with MySQL 8.x / MariaDB / phpMyAdmin / XAMPP
-- ====================================================================

CREATE DATABASE IF NOT EXISTS restaurant_db;
USE restaurant_db;

-- 1. Dining Tables
CREATE TABLE IF NOT EXISTS dining_tables (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    table_number VARCHAR(10) NOT NULL UNIQUE,
    seating_capacity INT NOT NULL CHECK(seating_capacity BETWEEN 1 AND 20),
    location_area VARCHAR(50) DEFAULT 'Main Dining Hall',
    status ENUM('Available', 'Occupied', 'Reserved', 'Cleaning') DEFAULT 'Available'
) ENGINE=InnoDB;

-- 2. Staff / Employees
CREATE TABLE IF NOT EXISTS staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role ENUM('Manager', 'Head Chef', 'Sous Chef', 'Waiter', 'Cashier', 'Bartender') NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    salary DECIMAL(10, 2) NOT NULL CHECK(salary > 0),
    hire_date DATE DEFAULT (CURRENT_DATE),
    shift ENUM('Morning', 'Evening', 'Night', 'Full Day') DEFAULT 'Evening'
) ENGINE=InnoDB;

-- 3. Menu Categories
CREATE TABLE IF NOT EXISTS menu_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
) ENGINE=InnoDB;

-- 4. Menu Items
CREATE TABLE IF NOT EXISTS menu_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    category_id INT NOT NULL,
    price DECIMAL(8, 2) NOT NULL CHECK(price > 0),
    food_type ENUM('Veg', 'Non-Veg', 'Vegan', 'Beverage') DEFAULT 'Veg',
    prep_time_minutes INT NOT NULL DEFAULT 15 CHECK(prep_time_minutes > 0),
    is_available TINYINT(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES menu_categories(category_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    loyalty_points INT DEFAULT 0 CHECK(loyalty_points >= 0),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 6. Orders Master
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(25) NOT NULL UNIQUE,
    customer_id INT,
    table_id INT,
    staff_id INT,
    order_type ENUM('Dine-in', 'Takeaway', 'Delivery') DEFAULT 'Dine-in',
    order_status ENUM('Pending', 'In Kitchen', 'Served', 'Completed', 'Cancelled') DEFAULT 'Pending',
    payment_status ENUM('Unpaid', 'Paid', 'Refunded') DEFAULT 'Unpaid',
    payment_method ENUM('Cash', 'Card', 'UPI', 'Pending') DEFAULT 'Pending',
    total_amount DECIMAL(10, 2) DEFAULT 0.0 CHECK(total_amount >= 0),
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (table_id) REFERENCES dining_tables(table_id) ON DELETE SET NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 7. Order Items (M:N Relationship)
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL CHECK(quantity > 0),
    unit_price DECIMAL(8, 2) NOT NULL CHECK(unit_price > 0),
    subtotal DECIMAL(10, 2) NOT NULL CHECK(subtotal >= 0),
    special_instructions TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES menu_items(item_id) ON DELETE RESTRICT,
    UNIQUE KEY uq_order_item (order_id, item_id)
) ENGINE=InnoDB;

-- 8. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    record_id INT,
    action_details TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Views
CREATE OR REPLACE VIEW v_order_billing_summary AS
SELECT 
    o.order_id,
    o.order_number,
    o.order_type,
    o.order_status,
    o.payment_status,
    o.payment_method,
    o.total_amount,
    o.order_time,
    COALESCE(c.name, 'Walk-in Guest') AS customer_name,
    COALESCE(c.phone, 'N/A') AS customer_phone,
    COALESCE(t.table_number, 'N/A') AS table_number,
    t.location_area,
    COALESCE(CONCAT(s.first_name, ' ', s.last_name), 'Unassigned') AS waiter_name,
    COUNT(oi.order_item_id) AS distinct_items_count,
    COALESCE(SUM(oi.quantity), 0) AS total_items_quantity
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN dining_tables t ON o.table_id = t.table_id
LEFT JOIN staff s ON o.staff_id = s.staff_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.order_number, o.order_type, o.order_status, o.payment_status, o.payment_method, o.total_amount, o.order_time, c.name, c.phone, t.table_number, t.location_area, s.first_name, s.last_name;

CREATE OR REPLACE VIEW v_popular_dishes_analytics AS
SELECT 
    m.item_id,
    m.item_name,
    mc.category_name,
    m.food_type,
    m.price,
    COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
    COALESCE(SUM(oi.subtotal), 0.0) AS total_revenue_generated,
    COUNT(DISTINCT oi.order_id) AS orders_count
FROM menu_items m
JOIN menu_categories mc ON m.category_id = mc.category_id
LEFT JOIN order_items oi ON m.item_id = oi.item_id
GROUP BY m.item_id, m.item_name, mc.category_name, m.food_type, m.price;
