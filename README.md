# Restaurant Management System (DBMS Project) - BistroDB

An end-to-end relational database web application developed for Database Management System (DBMS) college coursework, lab practical examinations, and project viva presentations.

---

## 🌟 Key Database Highlights

Built strictly on **Relational Database Management System (RDBMS)** principles:

1. **3NF Normalized Relational Schema**:
   - `dining_tables` (Seating capacity, area, occupancy status)
   - `staff` (Employees, roles, shifts, salary tracking)
   - `menu_categories` (Master categories for dishes)
   - `menu_items` (Dishes with price, dietary type, preparation time)
   - `customers` (Diners directory with loyalty points tracking)
   - `orders` (Master order header linked to table, customer, waiter)
   - `order_items` (Many-to-Many junction table between `orders` and `menu_items`)
   - `audit_logs` (Automated audit trail populated by database triggers)

2. **Integrity & Constraints**:
   - **Primary Keys** (`AUTOINCREMENT`)
   - **Foreign Keys** with enforcement (`PRAGMA foreign_keys = ON;`)
   - **Referential Integrity Actions**: `ON DELETE CASCADE` (for `order_items`), `ON DELETE RESTRICT` (for categories & items), `ON DELETE SET NULL` (for staff & tables)
   - **Composite Unique Constraint**: `UNIQUE(order_id, item_id)` preventing duplicate items in the same order.
   - **CHECK Constraints**: `price > 0`, `quantity > 0`, `seating_capacity BETWEEN 1 AND 20`, `total_amount >= 0`, `food_type IN ('Veg', 'Non-Veg', 'Vegan', 'Beverage')`.

3. **Database Views (`CREATE VIEW`)**:
   - `v_order_billing_summary`: Joins orders, customers, tables, and waiters for itemized billing.
   - `v_popular_dishes_analytics`: Aggregates dishes with total quantity sold, revenue, and order frequency.
   - `v_staff_waiter_performance`: Sales volume, total orders, and average bill size handled by each waiter.

4. **Automated Database Triggers (`CREATE TRIGGER`)**:
   - `trg_after_order_insert_occupy_table`: Automatically updates dining table status to `Occupied` upon placing a Dine-in order.
   - `trg_after_order_item_insert_calc_total`: Automatically calculates and updates `orders.total_amount` whenever a dish is added.
   - `trg_after_order_status_complete`: When an order is completed, frees the table (`Available`) and automatically credits customer loyalty points (1 point per ₹100 spent).
   - `trg_after_order_delete`: Automatically logs deletions.

5. **Interactive Live SQL Query Lab**:
   - Web SQL console to type any SQL command (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`).
   - 8 Academic preset queries covering:
     - 5-table `INNER JOIN` (Itemized billing)
     - `LEFT OUTER JOIN` (Finding dishes with 0 orders)
     - `GROUP BY` with `HAVING` (Top categories with sales > ₹800)
     - Nested subquery with `NOT IN` (Strict vegetarian diners)
     - Correlated subquery (Dishes priced higher than category average)
     - Set operations (`UNION`)
     - Real-time execution benchmark timer in milliseconds
     - One-click CSV export of query results

---

## 🚀 How to Run the Project

### Prerequisites:
- Python 3.8+ (Python 3.14+ supported)
- Flask (`pip install flask`)

### Steps:
1. Open terminal / command prompt in this directory:
   ```powershell
   cd "C:\Users\KHUSHI DAHIYA\.gemini\antigravity\scratch\restaurant_dbms_project"
   ```
2. Run the application:
   ```powershell
   python app.py
   ```
   *(Or simply double click `run.bat` on Windows)*

3. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 📁 Project Structure

```text
restaurant_dbms_project/
│── app.py                 # Flask server & route handlers with raw SQL
│── database.py            # SQLite connection manager & query execution engine
│── schema.sql             # SQLite DDL script (tables, views, triggers, indexes)
│── seed.sql               # Clean sample restaurant data for demo
│── mysql_schema.sql       # MySQL / MariaDB compatible DDL script for XAMPP
│── run.bat                # Windows 1-click startup batch script
│── README.md              # Project report & documentation
└── templates/
    ├── base.html          # Main layout, Tailwind CSS, FontAwesome, navbar
    ├── index.html         # Dashboard with metrics, live tables floor, top dishes
    ├── menu.html          # Menu catalog CRUD + live SQL preview
    ├── orders.html        # Orders & billing module (triggers active)
    ├── tables.html        # Dining tables floor management
    ├── staff.html         # Staff & waiters operations
    ├── customers.html     # Customers & loyalty rewards
    ├── query_lab.html     # Interactive SQL terminal & 8 academic query presets
    ├── schema_viewer.html # ER diagram, table columns, PK/FK viewer, SQL downloads
    └── audit_logs.html    # Automated trigger logs viewer
```

---

## 🎯 Academic SQL Queries Showcase

| Query Type | Concept Demonstrated | Example Target |
|---|---|---|
| **DQL (Select)** | Filter & Sort | `SELECT * FROM menu_items WHERE price < 300 ORDER BY price;` |
| **Multi-Table JOIN** | 5-table `INNER JOIN` | Orders + Customers + Tables + Staff + OrderItems + MenuItems |
| **Outer Join** | `LEFT JOIN` with `IS NULL` | Find menu items that have zero sales / never ordered |
| **Aggregates** | `COUNT`, `SUM`, `AVG`, `MAX`, `MIN` | Category revenue breakdown and average dish prices |
| **Grouping & Filter** | `GROUP BY` with `HAVING` | Filter categories with total revenue > ₹800 |
| **Subqueries** | `NOT IN (SELECT ...)` | Identify customers who have never ordered a Non-Veg dish |
| **Correlated Query** | Scalar subquery comparison | Dishes priced higher than the average price in their category |
| **Set Operations** | `UNION` | Unified phone directory of both diners and staff members |
| **Stored Views** | `CREATE VIEW` abstraction | Read from `v_popular_dishes_analytics` |
| **Triggers** | `AFTER UPDATE ON orders` | Automatically frees dining table & awards customer points |

---

## 🎓 Viva Questions & Answers (For Evaluation)

**Q1: Why is an `order_items` table needed in addition to the `orders` table?**
> **Answer:** An order can contain multiple menu items, and a single menu item can appear across multiple orders. This creates a Many-to-Many (M:N) relationship. The `order_items` junction table resolves this into two 1:N relationships (`orders` 1:N `order_items` and `menu_items` 1:N `order_items`) and stores line-item specific data such as `quantity`, `unit_price`, and `subtotal`.

**Q2: What is the benefit of the database trigger on `orders`?**
> **Answer:** The trigger `trg_after_order_insert_occupy_table` automatically updates the table status in `dining_tables` to 'Occupied' whenever a Dine-in order is recorded. Similarly, when the order is marked 'Completed', `trg_after_order_status_complete` frees the table back to 'Available' and calculates loyalty points directly at the database engine level.

**Q3: How is referential integrity enforced on dish deletion?**
> **Answer:** `menu_items` has `ON DELETE RESTRICT` foreign key references from `order_items`. This prevents historical accounting corruption by ensuring that dishes already part of paid customer orders cannot be accidentally deleted.
