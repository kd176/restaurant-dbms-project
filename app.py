from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import database
import os
import random

app = Flask(__name__)
app.secret_key = 'restaurant_dbms_secret_key_ultra_secure'

# Ensure database exists
if not os.path.exists(database.DB_PATH):
    database.init_database()
    database.seed_database()

def get_dropdown_data():
    categories = database.query_all("SELECT category_id, category_name FROM menu_categories ORDER BY category_name;")
    tables = database.query_all("SELECT table_id, table_number, seating_capacity, status, location_area FROM dining_tables ORDER BY table_number;")
    waiters = database.query_all("SELECT staff_id, first_name || ' ' || last_name AS name, role FROM staff WHERE role IN ('Waiter', 'Manager') ORDER BY first_name;")
    customers = database.query_all("SELECT customer_id, name, phone, loyalty_points FROM customers ORDER BY name;")
    dishes = database.query_all("SELECT item_id, item_name, price, food_type FROM menu_items WHERE is_available = 1 ORDER BY item_name;")
    return {
        'categories': categories,
        'tables': tables,
        'waiters': waiters,
        'customers': customers,
        'menu_items': dishes
    }

# -------------------------------------------------------------------
# 1. Dashboard
# -------------------------------------------------------------------
@app.route('/')
def index():
    stats = {
        'total_revenue': database.query_one("SELECT COALESCE(SUM(total_amount), 0.0) AS rev FROM orders WHERE payment_status = 'Paid';")['rev'],
        'total_orders': database.query_one("SELECT COUNT(*) AS c FROM orders;")['c'],
        'active_tables': database.query_one("SELECT COUNT(*) AS c FROM dining_tables WHERE status = 'Occupied';")['c'],
        'total_tables': database.query_one("SELECT COUNT(*) AS c FROM dining_tables;")['c'],
        'total_items': database.query_one("SELECT COUNT(*) AS c FROM menu_items;")['c'],
        'total_staff': database.query_one("SELECT COUNT(*) AS c FROM staff;")['c'],
        'total_customers': database.query_one("SELECT COUNT(*) AS c FROM customers;")['c']
    }

    # Live dining tables status
    tables = database.query_all("SELECT * FROM dining_tables ORDER BY table_number;")

    # Category Revenue Breakdown (GROUP BY)
    category_sales = database.query_all("""
        SELECT 
            mc.category_name,
            COUNT(DISTINCT mi.item_id) AS total_items,
            COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
            COALESCE(SUM(oi.subtotal), 0.0) AS category_revenue
        FROM menu_categories mc
        LEFT JOIN menu_items mi ON mc.category_id = mi.category_id
        LEFT JOIN order_items oi ON mi.item_id = oi.item_id
        GROUP BY mc.category_id
        ORDER BY category_revenue DESC;
    """)

    # Top 5 Best-Selling Dishes
    top_dishes = database.query_all("""
        SELECT 
            m.item_name,
            mc.category_name,
            m.price,
            m.food_type,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            COALESCE(SUM(oi.subtotal), 0.0) AS revenue
        FROM menu_items m
        JOIN menu_categories mc ON m.category_id = mc.category_id
        JOIN order_items oi ON m.item_id = oi.item_id
        GROUP BY m.item_id
        ORDER BY units_sold DESC
        LIMIT 5;
    """)

    # Recent Audit Logs (populated by triggers)
    recent_logs = database.query_all("SELECT * FROM audit_logs ORDER BY logged_at DESC LIMIT 6;")

    return render_template(
        'index.html', 
        stats=stats, 
        tables=tables, 
        category_sales=category_sales, 
        top_dishes=top_dishes, 
        recent_logs=recent_logs
    )

# -------------------------------------------------------------------
# 2. Menu Catalog CRUD
# -------------------------------------------------------------------
@app.route('/menu')
def menu():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '').strip()
    food_type = request.args.get('food_type', '').strip()

    sql = """
        SELECT 
            m.*,
            mc.category_name,
            COALESCE(SUM(oi.quantity), 0) AS total_sold
        FROM menu_items m
        JOIN menu_categories mc ON m.category_id = mc.category_id
        LEFT JOIN order_items oi ON m.item_id = oi.item_id
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (m.item_name LIKE ? OR mc.category_name LIKE ?)"
        like_str = f"%{search}%"
        params.extend([like_str, like_str])
    if category_id:
        sql += " AND m.category_id = ?"
        params.append(category_id)
    if food_type:
        sql += " AND m.food_type = ?"
        params.append(food_type)

    sql += " GROUP BY m.item_id ORDER BY mc.category_name, m.item_name ASC;"

    menu_list = database.query_all(sql, params)
    dropdowns = get_dropdown_data()

    return render_template(
        'menu.html', 
        menu_items=menu_list, 
        dropdowns=dropdowns, 
        search=search, 
        category_id=category_id, 
        food_type=food_type,
        sql_used=sql
    )

@app.route('/menu/add', methods=['POST'])
def add_menu_item():
    name = request.form['item_name'].strip()
    category_id = int(request.form['category_id'])
    price = float(request.form['price'])
    food_type = request.form['food_type']
    prep_time = int(request.form.get('prep_time_minutes', 15))
    is_available = 1 if request.form.get('is_available') == '1' else 0

    sql = """
        INSERT INTO menu_items (item_name, category_id, price, food_type, prep_time_minutes, is_available)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    success, res = database.execute_commit(sql, (name, category_id, price, food_type, prep_time, is_available))
    if success:
        flash(f"Dish '{name}' (Rs {price:.2f}) added to the menu!", "success")
    else:
        flash(f"Error adding dish: {res}", "danger")
    return redirect(url_for('menu'))

@app.route('/menu/edit/<int:item_id>', methods=['POST'])
def edit_menu_item(item_id):
    name = request.form['item_name'].strip()
    category_id = int(request.form['category_id'])
    price = float(request.form['price'])
    food_type = request.form['food_type']
    prep_time = int(request.form.get('prep_time_minutes', 15))
    is_available = int(request.form.get('is_available', 1))

    sql = """
        UPDATE menu_items 
        SET item_name = ?, category_id = ?, price = ?, food_type = ?, prep_time_minutes = ?, is_available = ?
        WHERE item_id = ?;
    """
    success, res = database.execute_commit(sql, (name, category_id, price, food_type, prep_time, is_available, item_id))
    if success:
        flash(f"Menu item #{item_id} updated successfully!", "success")
    else:
        flash(f"Error updating dish: {res}", "danger")
    return redirect(url_for('menu'))

@app.route('/menu/delete/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    sql = "DELETE FROM menu_items WHERE item_id = ?;"
    success, res = database.execute_commit(sql, (item_id,))
    if success:
        flash(f"Menu item #{item_id} removed from the menu.", "info")
    else:
        flash(f"Cannot delete dish: {res} (This dish has existing order references protected by ON DELETE RESTRICT).", "danger")
    return redirect(url_for('menu'))

# -------------------------------------------------------------------
# 3. Orders & Billing System (Core Transaction Module)
# -------------------------------------------------------------------
@app.route('/orders')
def orders():
    status_filter = request.args.get('status', '').strip()
    type_filter = request.args.get('type', '').strip()

    sql = """
        SELECT 
            o.*,
            COALESCE(c.name, 'Walk-in Guest') AS customer_name,
            c.phone AS customer_phone,
            t.table_number,
            t.location_area,
            COALESCE(s.first_name || ' ' || s.last_name, 'Unassigned') AS waiter_name,
            COUNT(oi.order_item_id) AS items_count
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN dining_tables t ON o.table_id = t.table_id
        LEFT JOIN staff s ON o.staff_id = s.staff_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        WHERE 1=1
    """
    params = []
    if status_filter:
        sql += " AND o.order_status = ?"
        params.append(status_filter)
    if type_filter:
        sql += " AND o.order_type = ?"
        params.append(type_filter)

    sql += " GROUP BY o.order_id ORDER BY o.order_id DESC;"

    orders_list = database.query_all(sql, params)
    dropdowns = get_dropdown_data()

    # Load order items for all active orders for modal preview
    order_items_map = {}
    for o in orders_list:
        items = database.query_all("""
            SELECT oi.*, mi.item_name, mi.food_type 
            FROM order_items oi 
            JOIN menu_items mi ON oi.item_id = mi.item_id 
            WHERE oi.order_id = ?;
        """, (o['order_id'],))
        order_items_map[o['order_id']] = items

    return render_template(
        'orders.html', 
        orders=orders_list, 
        order_items_map=order_items_map,
        dropdowns=dropdowns, 
        status_filter=status_filter, 
        type_filter=type_filter,
        sql_used=sql
    )

@app.route('/orders/create', methods=['POST'])
def create_order():
    order_type = request.form['order_type']
    customer_id = request.form.get('customer_id')
    customer_id = int(customer_id) if customer_id else None
    table_id = request.form.get('table_id')
    table_id = int(table_id) if table_id and order_type == 'Dine-in' else None
    staff_id = request.form.get('staff_id')
    staff_id = int(staff_id) if staff_id else None

    # Generate unique order number
    rand_suffix = random.randint(100, 999)
    order_number = f"ORD-{database.query_one('SELECT COUNT(*) + 1 AS c FROM orders;')['c']:03d}-{rand_suffix}"

    sql = """
        INSERT INTO orders (order_number, customer_id, table_id, staff_id, order_type, order_status, payment_status, total_amount)
        VALUES (?, ?, ?, ?, ?, 'Pending', 'Unpaid', 0.0);
    """
    success, res = database.execute_commit(sql, (order_number, customer_id, table_id, staff_id, order_type))
    if success:
        flash(f"Order #{order_number} created! Database trigger updated table status to Occupied.", "success")
    else:
        flash(f"Error creating order: {res}", "danger")
    return redirect(url_for('orders'))

@app.route('/orders/add-item/<int:order_id>', methods=['POST'])
def add_item_to_order(order_id):
    item_id = int(request.form['item_id'])
    quantity = int(request.form['quantity'])
    instructions = request.form.get('special_instructions', '').strip()

    # Get current item price
    item = database.query_one("SELECT price FROM menu_items WHERE item_id = ?;", (item_id,))
    if not item:
        flash("Invalid menu item selected.", "danger")
        return redirect(url_for('orders'))

    unit_price = item['price']
    subtotal = unit_price * quantity

    sql = """
        INSERT INTO order_items (order_id, item_id, quantity, unit_price, subtotal, special_instructions)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    success, res = database.execute_commit(sql, (order_id, item_id, quantity, unit_price, subtotal, instructions))
    if success:
        flash("Item added to order! Database trigger automatically updated the total bill amount.", "success")
    else:
        flash(f"Error adding item (item might already be in this order): {res}", "danger")
    return redirect(url_for('orders'))

@app.route('/orders/update-status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    new_status = request.form['order_status']
    payment_status = request.form.get('payment_status', 'Unpaid')
    payment_method = request.form.get('payment_method', 'Pending')

    sql = """
        UPDATE orders 
        SET order_status = ?, payment_status = ?, payment_method = ?
        WHERE order_id = ?;
    """
    success, res = database.execute_commit(sql, (new_status, payment_status, payment_method, order_id))
    if success:
        if new_status == 'Completed':
            flash(f"Order #{order_id} Completed & Settled! Trigger automatically freed the table & credited customer loyalty points.", "success")
        else:
            flash(f"Order #{order_id} status updated to '{new_status}'.", "info")
    else:
        flash(f"Error updating order: {res}", "danger")
    return redirect(url_for('orders'))

@app.route('/orders/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    sql = "DELETE FROM orders WHERE order_id = ?;"
    success, res = database.execute_commit(sql, (order_id,))
    if success:
        flash(f"Order #{order_id} deleted. CASCADE deletion cleaned up all line items.", "info")
    else:
        flash(f"Error deleting order: {res}", "danger")
    return redirect(url_for('orders'))

# -------------------------------------------------------------------
# 4. Dining Tables Management
# -------------------------------------------------------------------
@app.route('/tables')
def tables():
    tables_list = database.query_all("""
        SELECT 
            t.*,
            o.order_number,
            o.order_id,
            COALESCE(c.name, 'Walk-in') AS current_customer,
            s.first_name || ' ' || s.last_name AS current_waiter
        FROM dining_tables t
        LEFT JOIN orders o ON t.table_id = o.table_id AND o.order_status NOT IN ('Completed', 'Cancelled')
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN staff s ON o.staff_id = s.staff_id
        ORDER BY t.table_number ASC;
    """)
    return render_template('tables.html', tables=tables_list)

@app.route('/tables/add', methods=['POST'])
def add_table():
    number = request.form['table_number'].strip().upper()
    capacity = int(request.form['seating_capacity'])
    area = request.form.get('location_area', 'Main Dining Hall').strip()

    sql = "INSERT INTO dining_tables (table_number, seating_capacity, location_area, status) VALUES (?, ?, ?, 'Available');"
    success, res = database.execute_commit(sql, (number, capacity, area))
    if success:
        flash(f"Table '{number}' (Seats: {capacity}) added successfully!", "success")
    else:
        flash(f"Error adding table: {res}", "danger")
    return redirect(url_for('tables'))

@app.route('/tables/status/<int:table_id>', methods=['POST'])
def update_table_status(table_id):
    new_status = request.form['status']
    sql = "UPDATE dining_tables SET status = ? WHERE table_id = ?;"
    success, res = database.execute_commit(sql, (new_status, table_id))
    if success:
        flash(f"Table #{table_id} status updated to '{new_status}'.", "info")
    else:
        flash(f"Error updating table: {res}", "danger")
    return redirect(url_for('tables'))

# -------------------------------------------------------------------
# 5. Staff & Employees CRUD
# -------------------------------------------------------------------
@app.route('/staff')
def staff():
    staff_list = database.query_all("""
        SELECT 
            s.*,
            COUNT(o.order_id) AS total_orders_handled,
            COALESCE(SUM(o.total_amount), 0.0) AS total_sales
        FROM staff s
        LEFT JOIN orders o ON s.staff_id = o.staff_id AND o.order_status = 'Completed'
        GROUP BY s.staff_id
        ORDER BY s.role, s.first_name ASC;
    """)
    return render_template('staff.html', staff=staff_list)

@app.route('/staff/add', methods=['POST'])
def add_staff():
    first = request.form['first_name'].strip()
    last = request.form['last_name'].strip()
    role = request.form['role']
    phone = request.form['phone'].strip()
    email = request.form['email'].strip()
    salary = float(request.form['salary'])
    shift = request.form.get('shift', 'Evening')

    sql = """
        INSERT INTO staff (first_name, last_name, role, phone, email, salary, shift)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    success, res = database.execute_commit(sql, (first, last, role, phone, email, salary, shift))
    if success:
        flash(f"Employee '{first} {last}' ({role}) registered successfully!", "success")
    else:
        flash(f"Error adding staff member: {res}", "danger")
    return redirect(url_for('staff'))

# -------------------------------------------------------------------
# 6. Customers & Loyalty Program
# -------------------------------------------------------------------
@app.route('/customers')
def customers():
    customer_list = database.query_all("""
        SELECT 
            c.*,
            COUNT(o.order_id) AS total_visits,
            COALESCE(SUM(o.total_amount), 0.0) AS total_spend
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.payment_status = 'Paid'
        GROUP BY c.customer_id
        ORDER BY total_spend DESC;
    """)
    return render_template('customers.html', customers=customer_list)

@app.route('/customers/add', methods=['POST'])
def add_customer():
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    email = request.form.get('email', '').strip()

    sql = "INSERT INTO customers (name, phone, email, loyalty_points) VALUES (?, ?, ?, 0);"
    success, res = database.execute_commit(sql, (name, phone, email))
    if success:
        flash(f"Customer '{name}' registered in loyalty program!", "success")
    else:
        flash(f"Error adding customer: {res}", "danger")
    return redirect(url_for('customers'))

# -------------------------------------------------------------------
# 7. SQL Query Lab (DBMS Project Core Highlight!)
# -------------------------------------------------------------------
PRESET_RESTAURANT_QUERIES = [
    {
        "id": 1,
        "category": "Multi-Table JOIN",
        "title": "Comprehensive Order Billing Breakdown (5-Table INNER JOIN)",
        "desc": "Joins orders, customers, tables, staff, order_items, and menu_items to output itemized customer bills.",
        "sql": """SELECT 
    o.order_number,
    COALESCE(c.name, 'Walk-in') AS customer_name,
    t.table_number,
    s.first_name || ' ' || s.last_name AS waiter,
    m.item_name,
    oi.quantity,
    oi.unit_price,
    oi.subtotal,
    o.order_status
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN dining_tables t ON o.table_id = t.table_id
JOIN staff s ON o.staff_id = s.staff_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN menu_items m ON oi.item_id = m.item_id
ORDER BY o.order_number, oi.order_item_id;"""
    },
    {
        "id": 2,
        "category": "LEFT OUTER JOIN",
        "title": "Find Unpopular / Un-ordered Menu Items (Zero Sales)",
        "desc": "Uses LEFT JOIN where order_item_id IS NULL to find dishes that have never been ordered by any customer.",
        "sql": """SELECT 
    m.item_id,
    m.item_name,
    mc.category_name,
    m.price,
    m.food_type
FROM menu_items m
JOIN menu_categories mc ON m.category_id = mc.category_id
LEFT JOIN order_items oi ON m.item_id = oi.item_id
WHERE oi.order_item_id IS NULL;"""
    },
    {
        "id": 3,
        "category": "Aggregate with GROUP BY & HAVING",
        "title": "High-Revenue Menu Categories (Revenue > Rs 800)",
        "desc": "Aggregates revenue across categories and uses HAVING to filter only the top performing food sections.",
        "sql": """SELECT 
    mc.category_name,
    COUNT(DISTINCT m.item_id) AS total_dishes,
    SUM(oi.quantity) AS total_units_sold,
    SUM(oi.subtotal) AS total_revenue,
    ROUND(AVG(m.price), 2) AS average_dish_price
FROM menu_categories mc
JOIN menu_items m ON mc.category_id = m.category_id
JOIN order_items oi ON m.item_id = oi.item_id
GROUP BY mc.category_id
HAVING SUM(oi.subtotal) > 800.0
ORDER BY total_revenue DESC;"""
    },
    {
        "id": 4,
        "category": "Nested Subquery (NOT IN)",
        "title": "Strict Vegetarian Customers (Never Ordered Non-Veg)",
        "desc": "Uses NOT IN (subquery) to find customers who have never ordered any dish marked 'Non-Veg'.",
        "sql": """SELECT 
    c.customer_id,
    c.name,
    c.phone,
    c.loyalty_points
FROM customers c
WHERE c.customer_id NOT IN (
    SELECT DISTINCT o.customer_id
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN menu_items m ON oi.item_id = m.item_id
    WHERE m.food_type = 'Non-Veg' AND o.customer_id IS NOT NULL
)
ORDER BY c.loyalty_points DESC;"""
    },
    {
        "id": 5,
        "category": "Correlated Subquery",
        "title": "Premium Dishes: Items Priced Higher Than Category Average",
        "desc": "Correlates each menu item's price against the average price computed for that specific category.",
        "sql": """SELECT 
    m1.item_id,
    m1.item_name,
    mc.category_name,
    m1.price,
    ROUND((SELECT AVG(m2.price) FROM menu_items m2 WHERE m2.category_id = m1.category_id), 2) AS category_avg_price,
    ROUND(m1.price - (SELECT AVG(m2.price) FROM menu_items m2 WHERE m2.category_id = m1.category_id), 2) AS premium_difference
FROM menu_items m1
JOIN menu_categories mc ON m1.category_id = mc.category_id
WHERE m1.price > (
    SELECT AVG(m2.price) 
    FROM menu_items m2 
    WHERE m2.category_id = m1.category_id
)
ORDER BY premium_difference DESC;"""
    },
    {
        "id": 6,
        "category": "Waiter Performance & Efficiency",
        "title": "Waiter Sales Leaderboard (Order Counts & Total Revenue)",
        "desc": "Computes total sales volume and average order size for each dining staff member.",
        "sql": """SELECT 
    s.staff_id,
    s.first_name || ' ' || s.last_name AS waiter_name,
    s.shift,
    COUNT(o.order_id) AS orders_served,
    COALESCE(SUM(o.total_amount), 0.0) AS total_sales_generated,
    ROUND(AVG(o.total_amount), 2) AS avg_bill_size
FROM staff s
JOIN orders o ON s.staff_id = o.staff_id
WHERE o.order_status != 'Cancelled'
GROUP BY s.staff_id
ORDER BY total_sales_generated DESC;"""
    },
    {
        "id": 7,
        "category": "Database Views",
        "title": "Querying Stored Analytics View (v_popular_dishes_analytics)",
        "desc": "Reads from the pre-defined database view abstracting sales and units sold.",
        "sql": """SELECT 
    item_name, 
    category_name, 
    food_type, 
    price, 
    total_units_sold, 
    total_revenue_generated 
FROM v_popular_dishes_analytics
WHERE total_units_sold > 0
ORDER BY total_units_sold DESC;"""
    },
    {
        "id": 8,
        "category": "Set Operations (UNION)",
        "title": "Unified Contact Directory for Restaurant (Staff UNION Customers)",
        "desc": "Demonstrates relational UNION operation combining customer and staff phone books.",
        "sql": """SELECT 
    name AS contact_name, 
    phone, 
    'Customer' AS entity_type 
FROM customers
UNION
SELECT 
    first_name || ' ' || last_name AS contact_name, 
    phone, 
    'Staff (' || role || ')' AS entity_type 
FROM staff
ORDER BY entity_type, contact_name;"""
    }
]

@app.route('/query-lab')
def query_lab():
    return render_template('query_lab.html', presets=PRESET_RESTAURANT_QUERIES)

@app.route('/api/execute-sql', methods=['POST'])
def api_execute_sql():
    data = request.get_json() or {}
    sql_text = data.get('sql', '').strip()
    result = database.run_custom_query(sql_text)
    return jsonify(result)

# -------------------------------------------------------------------
# 8. Schema & ER Diagram Viewer
# -------------------------------------------------------------------
@app.route('/schema')
def schema_viewer():
    metadata = database.get_db_metadata()
    return render_template('schema_viewer.html', metadata=metadata)

@app.route('/download/schema-sqlite')
def download_sqlite_schema():
    return send_file(database.SCHEMA_PATH, as_attachment=True, download_name='restaurant_schema_sqlite.sql')

@app.route('/download/schema-mysql')
def download_mysql_schema():
    mysql_path = os.path.join(database.BASE_DIR, 'mysql_schema.sql')
    return send_file(mysql_path, as_attachment=True, download_name='restaurant_schema_mysql.sql')

# -------------------------------------------------------------------
# 9. Audit Logs (Triggers Feed)
# -------------------------------------------------------------------
@app.route('/audit-logs')
def audit_logs():
    action_filter = request.args.get('action', '').strip()
    table_filter = request.args.get('table', '').strip()

    sql = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    if action_filter:
        sql += " AND action_type = ?"
        params.append(action_filter)
    if table_filter:
        sql += " AND table_name = ?"
        params.append(table_filter)

    sql += " ORDER BY log_id DESC LIMIT 100;"
    logs = database.query_all(sql, params)
    return render_template('audit_logs.html', logs=logs, action_filter=action_filter, table_filter=table_filter, sql_used=sql)

# -------------------------------------------------------------------
# 10. Database Reset
# -------------------------------------------------------------------
@app.route('/reset-db', methods=['POST'])
def reset_db():
    try:
        database.init_database()
        database.seed_database()
        flash("Restaurant Database has been reset and reseeded with clean sample records!", "success")
    except Exception as e:
        flash(f"Reset failed: {e}", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("=================================================================")
    print("Restaurant DBMS Portal running at: http://127.0.0.1:5000")
    print("All SQL queries, CRUD actions, views, and triggers active!")
    print("=================================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
