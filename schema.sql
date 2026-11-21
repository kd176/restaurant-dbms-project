-- ====================================================================
-- Academic DBMS Project: Restaurant Management System (RMS)
-- Dialect: SQLite 3 (Standard SQL compatible with MySQL/MariaDB)
-- Normalization: 3rd Normal Form (3NF)
-- ====================================================================

PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------
-- 1. Dining Tables Entity
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dining_tables (
    table_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_number VARCHAR(10) UNIQUE NOT NULL,
    seating_capacity INTEGER CHECK(seating_capacity BETWEEN 1 AND 20) NOT NULL,
    location_area VARCHAR(50) DEFAULT 'Main Dining Hall',
    status VARCHAR(20) CHECK(status IN ('Available', 'Occupied', 'Reserved', 'Cleaning')) DEFAULT 'Available'
);

-- --------------------------------------------------------------------
-- 2. Staff / Employees Entity
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staff (
    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(30) CHECK(role IN ('Manager', 'Head Chef', 'Sous Chef', 'Waiter', 'Cashier', 'Bartender')) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    salary DECIMAL(10, 2) CHECK(salary > 0) NOT NULL,
    hire_date DATE DEFAULT (DATE('now')),
    shift VARCHAR(20) CHECK(shift IN ('Morning', 'Evening', 'Night', 'Full Day')) DEFAULT 'Evening'
);

-- --------------------------------------------------------------------
-- 3. Menu Categories Entity
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- --------------------------------------------------------------------
-- 4. Menu Items Entity
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name VARCHAR(100) NOT NULL,
    category_id INTEGER NOT NULL,
    price DECIMAL(8, 2) CHECK(price > 0) NOT NULL,
    food_type VARCHAR(15) CHECK(food_type IN ('Veg', 'Non-Veg', 'Vegan', 'Beverage')) DEFAULT 'Veg',
    prep_time_minutes INTEGER CHECK(prep_time_minutes > 0) DEFAULT 15,
    is_available INTEGER CHECK(is_available IN (0, 1)) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES menu_categories(category_id) ON DELETE RESTRICT
);

-- --------------------------------------------------------------------
-- 5. Customers Entity
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    loyalty_points INTEGER CHECK(loyalty_points >= 0) DEFAULT 0,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 6. Orders Master Table
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(25) UNIQUE NOT NULL,
    customer_id INTEGER,
    table_id INTEGER,
    staff_id INTEGER,
    order_type VARCHAR(20) CHECK(order_type IN ('Dine-in', 'Takeaway', 'Delivery')) DEFAULT 'Dine-in',
    order_status VARCHAR(20) CHECK(order_status IN ('Pending', 'In Kitchen', 'Served', 'Completed', 'Cancelled')) DEFAULT 'Pending',
    payment_status VARCHAR(20) CHECK(payment_status IN ('Unpaid', 'Paid', 'Refunded')) DEFAULT 'Unpaid',
    payment_method VARCHAR(20) CHECK(payment_method IN ('Cash', 'Card', 'UPI', 'Pending')) DEFAULT 'Pending',
    total_amount DECIMAL(10, 2) DEFAULT 0.0 CHECK(total_amount >= 0),
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (table_id) REFERENCES dining_tables(table_id) ON DELETE SET NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE SET NULL
);

-- --------------------------------------------------------------------
-- 7. Order Items Table (M:N Relationship between Orders & Menu Items)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER CHECK(quantity > 0) NOT NULL,
    unit_price DECIMAL(8, 2) CHECK(unit_price > 0) NOT NULL,
    subtotal DECIMAL(10, 2) CHECK(subtotal >= 0) NOT NULL,
    special_instructions TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES menu_items(item_id) ON DELETE RESTRICT,
    UNIQUE(order_id, item_id)
);

-- --------------------------------------------------------------------
-- 8. Audit Logs Table (Automated Trigger Event Capture)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(50) NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    record_id INTEGER,
    action_details TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- Performance Indexes
-- --------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_menu_category ON menu_items(category_id);
CREATE INDEX IF NOT EXISTS idx_order_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_table ON orders(table_id);
CREATE INDEX IF NOT EXISTS idx_order_staff ON orders(staff_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_item ON order_items(item_id);

-- --------------------------------------------------------------------
-- SQL Stored Views
-- --------------------------------------------------------------------

-- View 1: Complete Order Billing & Customer Summary View
CREATE VIEW IF NOT EXISTS v_order_billing_summary AS
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
    COALESCE(s.first_name || ' ' || s.last_name, 'Unassigned') AS waiter_name,
    COUNT(oi.order_item_id) AS distinct_items_count,
    COALESCE(SUM(oi.quantity), 0) AS total_items_quantity
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN dining_tables t ON o.table_id = t.table_id
LEFT JOIN staff s ON o.staff_id = s.staff_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id;

-- View 2: Popular Dishes & Sales Analytics View
CREATE VIEW IF NOT EXISTS v_popular_dishes_analytics AS
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
GROUP BY m.item_id;

-- View 3: Waiter & Staff Performance Analytics View
CREATE VIEW IF NOT EXISTS v_staff_waiter_performance AS
SELECT 
    s.staff_id,
    s.first_name || ' ' || s.last_name AS staff_name,
    s.role,
    s.shift,
    COUNT(o.order_id) AS total_orders_handled,
    COALESCE(SUM(o.total_amount), 0.0) AS total_sales_volume,
    ROUND(COALESCE(AVG(o.total_amount), 0.0), 2) AS average_order_value
FROM staff s
LEFT JOIN orders o ON s.staff_id = o.staff_id AND o.order_status != 'Cancelled'
GROUP BY s.staff_id;

-- --------------------------------------------------------------------
-- Database Triggers (Automated Business Logic Enforcement)
-- --------------------------------------------------------------------

-- Trigger 1: When a Dine-in Order is placed, automatically occupy the dining table
CREATE TRIGGER IF NOT EXISTS trg_after_order_insert_occupy_table
AFTER INSERT ON orders
WHEN NEW.table_id IS NOT NULL AND NEW.order_type = 'Dine-in'
BEGIN
    UPDATE dining_tables 
    SET status = 'Occupied' 
    WHERE table_id = NEW.table_id;

    INSERT INTO audit_logs (table_name, action_type, record_id, action_details)
    VALUES (
        'orders', 
        'INSERT', 
        NEW.order_id, 
        'New ' || NEW.order_type || ' Order #' || NEW.order_number || ' placed. Table #' || NEW.table_id || ' marked Occupied.'
    );
END;

-- Trigger 2: When an item is added to an order, automatically update order total
CREATE TRIGGER IF NOT EXISTS trg_after_order_item_insert_calc_total
AFTER INSERT ON order_items
BEGIN
    UPDATE orders 
    SET total_amount = (
        SELECT COALESCE(SUM(subtotal), 0.0) 
        FROM order_items 
        WHERE order_id = NEW.order_id
    )
    WHERE order_id = NEW.order_id;

    INSERT INTO audit_logs (table_name, action_type, record_id, action_details)
    VALUES (
        'order_items', 
        'INSERT', 
        NEW.order_item_id, 
        'Added ' || NEW.quantity || 'x Item ID #' || NEW.item_id || ' (Rs ' || NEW.subtotal || ') to Order #' || NEW.order_id
    );
END;

-- Trigger 3: When Order is Completed, free the dining table and credit loyalty points
CREATE TRIGGER IF NOT EXISTS trg_after_order_status_complete
AFTER UPDATE ON orders
WHEN OLD.order_status != 'Completed' AND NEW.order_status = 'Completed'
BEGIN
    -- Free table if dine-in
    UPDATE dining_tables 
    SET status = 'Available' 
    WHERE table_id = NEW.table_id;

    -- Award 1 loyalty point per 100 spent if customer is registered
    UPDATE customers 
    SET loyalty_points = loyalty_points + CAST(NEW.total_amount / 100 AS INTEGER)
    WHERE customer_id = NEW.customer_id;

    INSERT INTO audit_logs (table_name, action_type, record_id, action_details)
    VALUES (
        'orders', 
        'UPDATE', 
        NEW.order_id, 
        'Order #' || NEW.order_number || ' completed. Bill Total: Rs ' || NEW.total_amount || '. Table freed & loyalty points awarded.'
    );
END;

-- Trigger 4: Log Order Deletion
CREATE TRIGGER IF NOT EXISTS trg_after_order_delete
AFTER DELETE ON orders
BEGIN
    INSERT INTO audit_logs (table_name, action_type, record_id, action_details)
    VALUES (
        'orders', 
        'DELETE', 
        OLD.order_id, 
        'Order #' || OLD.order_number || ' deleted. Associated order_items removed via CASCADE.'
    );
END;
