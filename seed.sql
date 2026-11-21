-- ====================================================================
-- Academic DBMS Project: Restaurant Sample Seed Data
-- ====================================================================

DELETE FROM audit_logs;
DELETE FROM order_items;
DELETE FROM orders;
DELETE FROM customers;
DELETE FROM menu_items;
DELETE FROM menu_categories;
DELETE FROM staff;
DELETE FROM dining_tables;

DELETE FROM sqlite_sequence WHERE name IN ('dining_tables', 'staff', 'menu_categories', 'menu_items', 'customers', 'orders', 'order_items', 'audit_logs');

-- --------------------------------------------------------------------
-- 1. Dining Tables
-- --------------------------------------------------------------------
INSERT INTO dining_tables (table_id, table_number, seating_capacity, location_area, status) VALUES
(1, 'T-01', 2, 'Window View', 'Available'),
(2, 'T-02', 4, 'Main Dining Hall', 'Available'),
(3, 'T-03', 4, 'Main Dining Hall', 'Occupied'),
(4, 'T-04', 6, 'Family Section', 'Occupied'),
(5, 'T-05', 8, 'Private Dining Room', 'Reserved'),
(6, 'T-06', 2, 'Rooftop Lounge', 'Available'),
(7, 'T-07', 4, 'Rooftop Lounge', 'Available'),
(8, 'T-08', 4, 'Outdoor Garden', 'Cleaning');

-- --------------------------------------------------------------------
-- 2. Staff Members
-- --------------------------------------------------------------------
INSERT INTO staff (staff_id, first_name, last_name, role, phone, email, salary, hire_date, shift) VALUES
(1, 'Rajesh', 'Khanna', 'Manager', '+91-9811122201', 'rajesh.k@bistro.com', 55000.00, '2022-03-01', 'Full Day'),
(2, 'Sanjeev', 'Kapoor', 'Head Chef', '+91-9811122202', 'sanjeev.chef@bistro.com', 65000.00, '2021-06-15', 'Morning'),
(3, 'Vikas', 'Gupta', 'Sous Chef', '+91-9811122203', 'vikas.g@bistro.com', 42000.00, '2023-01-10', 'Evening'),
(4, 'Amit', 'Sharma', 'Waiter', '+91-9811122204', 'amit.s@bistro.com', 22000.00, '2023-05-12', 'Morning'),
(5, 'Pooja', 'Verma', 'Waiter', '+91-9811122205', 'pooja.v@bistro.com', 22000.00, '2023-07-20', 'Evening'),
(6, 'Rohan', 'Mehta', 'Waiter', '+91-9811122206', 'rohan.m@bistro.com', 21000.00, '2024-02-01', 'Night'),
(7, 'Sneha', 'Roy', 'Cashier', '+91-9811122207', 'sneha.r@bistro.com', 26000.00, '2022-11-15', 'Full Day');

-- --------------------------------------------------------------------
-- 3. Menu Categories
-- --------------------------------------------------------------------
INSERT INTO menu_categories (category_id, category_name, description) VALUES
(1, 'Starters & Appetizers', 'Crispy, sizzling bites and chef special finger food'),
(2, 'Main Course - North Indian', 'Rich curries, gravies, and slow-cooked tandoori favorites'),
(3, 'Italian & Pastas', 'Artisanal thin-crust pizzas, pastas, and garlic delights'),
(4, 'Breads & Rice', 'Fresh naan, parathas, and aromatic dum biryanis'),
(5, 'Beverages & Mocktails', 'Refreshing iced coolers, shakes, and signature mocktails'),
(6, 'Desserts & Sweets', 'Artisan ice creams, gulab jamun, and chocolate sundaes');

-- --------------------------------------------------------------------
-- 4. Menu Items
-- --------------------------------------------------------------------
INSERT INTO menu_items (item_id, item_name, category_id, price, food_type, prep_time_minutes, is_available) VALUES
(1, 'Paneer Tikka Angara', 1, 320.00, 'Veg', 15, 1),
(2, 'Crispy Corn & Water Chestnut', 1, 260.00, 'Veg', 12, 1),
(3, 'Tandoori Chicken (Half)', 1, 380.00, 'Non-Veg', 20, 1),
(4, 'Paneer Butter Masala', 2, 360.00, 'Veg', 18, 1),
(5, 'Dal Makhani Special', 2, 310.00, 'Veg', 20, 1),
(6, 'Butter Chicken Delhi Style', 2, 440.00, 'Non-Veg', 22, 1),
(7, 'Margherita Pizza (11-inch)', 3, 390.00, 'Veg', 18, 1),
(8, 'Creamy Alfredo Penne Pasta', 3, 340.00, 'Veg', 15, 1),
(9, 'Hyderabadi Dum Biryani (Veg)', 4, 290.00, 'Veg', 25, 1),
(10, 'Hyderabadi Chicken Biryani', 4, 390.00, 'Non-Veg', 25, 1),
(11, 'Butter Garlic Naan', 4, 75.00, 'Veg', 5, 1),
(12, 'Virgin Mojito Mint Cooler', 5, 160.00, 'Beverage', 5, 1),
(13, 'Cold Coffee with Ice Cream', 5, 180.00, 'Beverage', 7, 1),
(14, 'Sizzling Hot Brownie with Vanilla', 6, 240.00, 'Veg', 10, 1),
(15, 'Gulab Jamun (2 pcs)', 6, 120.00, 'Veg', 5, 1),
(16, 'Lobster Thermidor (Special Order)', 2, 1250.00, 'Non-Veg', 40, 1); -- Intentionally 0 sales to demonstrate LEFT JOIN

-- --------------------------------------------------------------------
-- 5. Customers
-- --------------------------------------------------------------------
INSERT INTO customers (customer_id, name, phone, email, loyalty_points) VALUES
(1, 'Aditya Malhotra', '+91-9988776601', 'aditya.m@gmail.com', 120),
(2, 'Neha Sen', '+91-9988776602', 'neha.sen@yahoo.com', 250),
(3, 'Kunal Kapoor', '+91-9988776603', 'kunal.k@outlook.com', 45),
(4, 'Simran Kaur', '+91-9988776604', 'simran.kaur@gmail.com', 310),
(5, 'Gaurav Jain', '+91-9988776605', 'gaurav.jain@gmail.com', 80),
(6, 'Priya Nair', '+91-9988776606', 'priya.nair@corp.com', 0);

-- --------------------------------------------------------------------
-- 6. Orders Master
-- --------------------------------------------------------------------
INSERT INTO orders (order_id, order_number, customer_id, table_id, staff_id, order_type, order_status, payment_status, payment_method, total_amount, order_time) VALUES
(1, 'ORD-2024-001', 1, 1, 4, 'Dine-in', 'Completed', 'Paid', 'Card', 970.00, '2024-11-20 13:15:00'),
(2, 'ORD-2024-002', 2, 2, 5, 'Dine-in', 'Completed', 'Paid', 'UPI', 1265.00, '2024-11-20 14:00:00'),
(3, 'ORD-2024-003', 3, NULL, 4, 'Takeaway', 'Completed', 'Paid', 'Cash', 650.00, '2024-11-20 18:30:00'),
(4, 'ORD-2024-004', 4, 3, 5, 'Dine-in', 'In Kitchen', 'Unpaid', 'Pending', 890.00, '2024-11-21 19:10:00'),
(5, 'ORD-2024-005', 5, 4, 6, 'Dine-in', 'Served', 'Unpaid', 'Pending', 1580.00, '2024-11-21 19:35:00'),
(6, 'ORD-2024-006', 1, NULL, 5, 'Delivery', 'Pending', 'Unpaid', 'Pending', 550.00, '2024-11-21 20:00:00');

-- --------------------------------------------------------------------
-- 7. Order Items (M:N Links)
-- --------------------------------------------------------------------
INSERT INTO order_items (order_item_id, order_id, item_id, quantity, unit_price, subtotal, special_instructions) VALUES
-- Order 1 (Aditya)
(1, 1, 1, 1, 320.00, 320.00, 'Extra spicy green chutney'),
(2, 1, 4, 1, 360.00, 360.00, 'Less oil'),
(3, 1, 11, 2, 75.00, 150.00, 'Crispy butter naan'),
(4, 1, 15, 1, 120.00, 120.00, 'Warm serving'),

-- Order 2 (Neha)
(5, 2, 3, 1, 380.00, 380.00, 'Well roasted tandoori'),
(6, 2, 6, 1, 440.00, 440.00, 'Creamy boneless'),
(7, 2, 11, 3, 75.00, 225.00, 'Garlic naan'),
(8, 2, 12, 1, 160.00, 160.00, 'Extra mint and lemon'),

-- Order 3 (Kunal - Takeaway)
(9, 3, 9, 1, 290.00, 290.00, 'Extra raita packed'),
(10, 3, 4, 1, 360.00, 360.00, 'Packed tightly'),

-- Order 4 (Simran - Live)
(11, 4, 7, 1, 390.00, 390.00, 'Add jalapenos if possible'),
(12, 4, 8, 1, 340.00, 340.00, 'Cheesy penne'),
(13, 4, 12, 1, 160.00, 160.00, 'Chilled'),

-- Order 5 (Gaurav - Live Table 4)
(14, 5, 1, 2, 320.00, 640.00, 'For 4 guests'),
(15, 5, 5, 1, 310.00, 310.00, 'Slow cooked dal'),
(16, 5, 10, 1, 390.00, 390.00, 'Spicy Hyderabadi chicken'),
(17, 5, 14, 1, 240.00, 240.00, 'With vanilla ice cream'),

-- Order 6 (Delivery)
(18, 6, 2, 1, 260.00, 260.00, 'Crispy corn'),
(19, 6, 9, 1, 290.00, 290.00, 'Veg biryani');

-- Initial System Audit entry
INSERT INTO audit_logs (table_name, action_type, record_id, action_details)
VALUES ('SYSTEM', 'INITIALIZE', 0, 'Restaurant Database initialized with 3NF Schema, categories, dishes, staff, tables, and seed orders.');
