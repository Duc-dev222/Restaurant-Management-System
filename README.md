# 🍽️ Restaurant Management System

### Project 05 – Introduction to Database System

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.x-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-UI-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Status](https://img.shields.io/badge/Status-Academic%20Demo-success?style=for-the-badge)

**Student:** Ninh Duy Đức
**Student ID:** 11245860
**Class:** DSEB 66
**GitHub Repository:** https://github.com/Duc-dev222/Restaurant-Management-System
**YouTube Presentation:** *(to be added before submission)*

---

## 📌 Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Main Features](#2-main-features)
- [3. Technology Stack](#3-technology-stack)
- [4. Project Structure](#4-project-structure)
- [5. Database Design Summary](#5-database-design-summary)
- [6. SQL Deliverables](#6-sql-deliverables)
- [7. Advanced Database Objects](#7-advanced-database-objects)
- [8. Local Setup Instructions](#8-local-setup-instructions)
- [9. Demo Data Summary](#9-demo-data-summary)
- [10. Testing and Validation](#10-testing-and-validation)
- [11. Known Limitations](#11-known-limitations)
- [12. Future Improvements](#12-future-improvements)
- [13. Submission Links](#13-submission-links)
- [14. References](#14-references)

---

## 1. Project Overview

**Restaurant Management System** is a web-based application developed for **Project 05 – Introduction to Database System**. The system helps restaurant staff manage day-to-day operations, including:

- customer records and contact tracking,
- table management with location zones,
- a categorized dish menu with size/style variants,
- table reservation booking with conflict detection,
- invoice generation with itemized billing and service charge,
- role-based staff access control,
- dashboard analytics and revenue reporting.

The project is built with **Python, Flask, MySQL, and Bootstrap**. It demonstrates how relational database design, SQL scripting, and Python web development work together in a complete restaurant management application.

> This system is designed for academic demonstration and local use. It does not connect to real payment gateways or external booking platforms.

---

## 2. Main Features

### 🔐 Authentication & Role-Based Access

- Session-based login and logout using Werkzeug password hashing.
- Three staff roles with differentiated access:

| Role | Access |
|------|--------|
| `admin` | Full access including customer deletion and user setup. |
| `cashier` | Access to invoices, customers (read/add/edit), reservations, and menu viewing. |
| `waiter` | Access to reservations, table status updates, and menu viewing. |

### 📊 Dashboard

- Four summary cards: total customers, available tables, today's reservations, today's revenue.
- Revenue falls back to the most recent active day if no transactions exist today.
- Top 5 best-selling dishes ranked by quantity sold (powered by `v_top_selling_dishes` view).
- 7-day daily revenue bar chart.
- Today's upcoming reservation list.

### 👥 Customer Management

- Add, edit, search (by name or phone), and delete customers.
- Delete is restricted to `admin` role and blocked if the customer has existing invoices.
- Customer detail view showing last 10 invoices, last 10 reservations, and total spending.

### 🪑 Table Management

- Tables organized into three location zones:
  - **Indoor**: tables 1–450
  - **Outdoor**: tables 451–500
  - **VIP**: tables 501–510
- Status management: `available`, `reserved`, `occupied`, `maintenance`.
- Table status updated **automatically** via database triggers when reservations are confirmed or invoices are paid.

### 🍜 Menu Management

- Dishes organized by category (Appetizer, Main Course, Hot Pot & Grill, Noodle Dishes, Beverages).
- Each dish supports multiple **variants** with individual prices (e.g., Phở bò in small/regular/large).
- Toggle dish availability on/off.
- Full CRUD for dishes and variants.

### 📅 Reservation Management

- List and filter reservations by status, date, and customer.
- Add reservation form with:
  - existing or new customer registration in one step,
  - zone-based table filtering by guest count,
  - **2-hour conflict detection** — only tables with no overlapping bookings are shown.

### 🧾 Invoice Management

- Invoice listing with multi-field filtering: status, payment method, date range, customer search.
- Summary cards: total paid / unpaid / cancelled counts and overall revenue.
- Payment breakdown by method: cash, card, bank transfer.

### 📈 Reports

- Top-selling dishes by quantity and revenue.
- Daily and monthly revenue summaries.
- Customer visit frequency.
- Powered by the `v_top_selling_dishes` view and direct SQL aggregation.

---

## 3. Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | MySQL 8.x |
| Frontend | HTML, CSS, Bootstrap 5, JavaScript |
| Database Driver | mysql-connector-python |
| Password Hashing | Werkzeug |
| Data Generation | Python Faker (vi_VN locale) |
| Version Control | Git, GitHub |
| Database Design | ERDPlus, MySQL Workbench |

---

## 4. Project Structure

```
Restaurant-Management-System/
│
├── rms_webapp/
│   └── app/
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py          # Login, logout, setup, role decorators
│       │   ├── dashboard.py     # Summary stats, top dishes, revenue chart
│       │   ├── customers.py     # Customer CRUD and detail view
│       │   ├── reservations.py  # Reservation booking with conflict detection
│       │   ├── invoices.py      # Invoice listing and filtering
│       │   ├── tables.py        # Table management by zone
│       │   ├── menu.py          # Dish and variant management
│       │   └── reports.py       # Revenue and sales reports
│       │
│       ├── templates/
│       │   ├── auth/            # Login and setup pages
│       │   ├── dashboard/       # Main dashboard
│       │   ├── customers/       # Customer list, form, detail
│       │   ├── reservations/    # Reservation list and form
│       │   ├── invoices/        # Invoice list
│       │   ├── tables/          # Table management
│       │   ├── menu/            # Menu and variants
│       │   └── reports/         # Reports pages
│       │
│       ├── static/              # CSS, JS, images
│       ├── db.py                # Database connection and query helper
│       ├── config.py            # Flask app configuration
│       └── .env                 # Environment variables (not committed)
│
├── CODE.sql                     # Full schema + advanced database objects
├── insert_510_rows.sql          # 510-row sample data
├── generate_data.py             # Sample data generation script
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 5. Database Design Summary

The assignment specification (Project 05) requires the following conceptual entities:

```
Customers — Tables — MenuItems — Reservations — Invoices
```

The implemented application extends this into a normalized 9-table MySQL schema:

| Table | Purpose |
|-------|---------|
| `MenuCategories` | Classifies dishes into named categories with a sort order. |
| `Tables` | Stores physical tables with capacity, status, and location zone. |
| `Customers` | Stores customer identity: name, phone, address, email. |
| `Dishes` | Stores dish records linked to a category, with availability flag. |
| `DishVariants` | Stores size/style variants for each dish with individual prices. |
| `Users` | Stores staff accounts with hashed passwords and role. |
| `Reservations` | Stores table bookings with date/time, guest count, and status. |
| `Invoices` | Stores billing records with subtotal, service charge, and total. |
| `InvoiceItems` | Line items linking invoices to specific dish variants. |

### Why Dishes + DishVariants?

Instead of a single-price `MenuItems` table, the implemented schema splits the menu into:
- `Dishes` — holds dish name, category, and availability,
- `DishVariants` — holds specific variants (e.g., small/regular/large) each with its own price.

This allows the system to represent real-world menu complexity without duplicating dish metadata.

---

## 6. SQL Deliverables

| File | Purpose |
|------|---------|
| `CODE.sql` | Creates the database, all 9 tables, constraints, indexes, views, stored procedures, user-defined functions, and triggers. |
| `insert_510_rows.sql` | Inserts 510 rows of realistic sample data generated by `generate_data.py`. |
| `generate_data.py` | Python script that generates `insert_510_rows.sql` using the Faker library (vi_VN locale). |

---

## 7. Advanced Database Objects

All advanced objects are defined in `CODE.sql`.

### Indexes (8 total)
Targeting frequent query patterns: category lookups, variant rendering, reservation conflict detection, invoice filtering, and sales reporting.

### Views (3 total)

| View | Purpose |
|------|---------|
| `v_daily_bookings` | Joins reservations with customer and table data for daily booking schedules. |
| `v_table_availability` | Shows table status and upcoming reservation count for real-time availability. |
| `v_top_selling_dishes` | Aggregates paid invoice items to rank dishes by quantity sold and revenue. |

### Stored Procedure (1)
- `sp_confirm_reservation` — confirms a reservation from `pending` to `confirmed` with a status guard.

### User-Defined Function (1)
- `fn_service_charge(subtotal)` — returns 5% of the subtotal as the service charge, keeping the business rule consistent across the database and application.

### Triggers (4 total)

| Trigger | Behavior |
|---------|---------|
| `trg_reservation_insert_table` | Sets table to `reserved` when a new reservation is inserted. |
| `trg_reservation_confirm_table` | Sets table to `reserved` when a reservation is confirmed. |
| `trg_invoice_paid_table_available` | Sets table back to `available` when an invoice is updated to paid. |
| `trg_invoice_insert_paid_table_available` | Sets table to `available` when a new invoice is inserted as paid. |

---

## 8. Local Setup Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/Duc-dev222/Restaurant-Management-System.git
cd Restaurant-Management-System
```

### Step 2: Create and Activate Virtual Environment

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file inside `rms_webapp/app/` with your MySQL settings:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=restaurantmanagement
SECRET_KEY=your_flask_secret_key
```

> Do not upload your real `.env` file to GitHub.

### Step 5: Create the MySQL Database and Schema

```bash
mysql -u root -p < CODE.sql
```

### Step 6: Load Sample Data

```bash
mysql -u root -p < insert_510_rows.sql
```

Or regenerate the sample data yourself:

```bash
python generate_data.py
mysql -u root -p < insert_510_rows.sql
```

### Step 7: Initialize User Passwords

Start the Flask application and visit:

```
http://127.0.0.1:5000/setup
```

Set a password for the three seeded accounts: `admin`, `cashier`, `waiter1`.

### Step 8: Run the Application

```bash
flask --app rms_webapp/app run
```

Open the website:
```
http://127.0.0.1:5000/
```

---

## 9. Demo Data Summary

The `insert_510_rows.sql` dataset includes:

- **510 tables** across indoor (1–450), outdoor (451–500), and VIP (501–510) zones.
- **510 customers** with unique Vietnamese names, phone numbers, addresses, and emails.
- **5 menu categories**: Khai vị, Món chính, Lẩu & Nướng, Món nước, Đồ uống.
- **25 dishes** covering classic Vietnamese cuisine (Phở bò, Bún chả, Cơm tấm, Lẩu Thái...).
- **Multiple variants per dish** with individual pricing.
- **510 reservations** spanning 90 days back to 30 days forward.
- **510 invoices** (all paid) with 2–5 line items each, automatic service charge (5%) and occasional discounts.
- **3 user accounts**: `admin`, `cashier`, `waiter1`.

---

## 10. Testing and Validation

The project was tested for:

- Login and logout with all three role accounts.
- Customer add, edit, search, and delete (with invoice protection check).
- Reservation creation with zone-based table filtering and conflict detection.
- Reservation confirmation via `sp_confirm_reservation` stored procedure.
- Invoice listing with all filter combinations.
- Dashboard stats verified against direct SQL COUNT and SUM queries.
- Trigger behavior: table status updates automatically on reservation and invoice events.
- `fn_service_charge` output matches 5% of subtotal for all test invoices.
- Customer deletion blocked when associated invoices exist.

---

## 11. Known Limitations

- Designed for local academic demonstration only.
- Does not connect to real payment gateways or external booking platforms.
- No automated unit tests or CI/CD pipeline.
- No production WSGI server configuration or cloud deployment.

---

## 12. Future Improvements

- Add online ordering — allow customers to pre-order dishes when booking a table.
- Implement a loyalty program — track visit frequency and spending for reward points.
- Add QR-based table check-in for a smoother front-of-house experience.
- Introduce kitchen order tickets (KOT) for kitchen staff to view and update order status.
- Deploy with Docker for easier setup and sharing.
- Add automated backup scheduling and database health monitoring.

---

## 13. Submission Links

| Item | Link |
|------|------|
| GitHub Repository | https://github.com/Duc-dev222/Restaurant-Management-System |
| YouTube Presentation | *(to be added before submission)* |

---

## 14. References

- Flask Documentation: https://flask.palletsprojects.com/
- MySQL 8.0 Reference Manual: https://dev.mysql.com/doc/
- Bootstrap 5 Documentation: https://getbootstrap.com/docs/5.0/
- Python Documentation: https://docs.python.org/3/
- Werkzeug Documentation: https://werkzeug.palletsprojects.com/
- mysql-connector-python: https://dev.mysql.com/doc/connector-python/en/
- Faker Library: https://faker.readthedocs.io/
- ERDPlus: https://erdplus.com/
- MySQL Workbench Manual: https://dev.mysql.com/doc/workbench/en/
- GitHub Docs: https://docs.github.com/

---

### ✅ Project 05 – Restaurant Management System
**Relational database design + SQL scripting + Flask web application**
