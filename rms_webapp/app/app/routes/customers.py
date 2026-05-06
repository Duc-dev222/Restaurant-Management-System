from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import login_required, role_required
from ..db import query

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    if q:
        rows = query(
            """
            SELECT *
            FROM Customers
            WHERE CustomerName LIKE %s OR PhoneNumber LIKE %s
            ORDER BY CustomerID DESC
            """,
            (f"%{q}%", f"%{q}%"),
        )
    else:
        rows = query("SELECT * FROM Customers ORDER BY CustomerID DESC")
    return render_template("customers/index.html", customers=rows, search=q)


@customers_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        addr = request.form.get("address", "").strip()
        email = request.form.get("email", "").strip()

        if query("SELECT CustomerID FROM Customers WHERE PhoneNumber=%s", (phone,), one=True):
            flash("So dien thoai da ton tai.", "danger")
            return render_template("customers/form.html", action="add", customer=None)

        query(
            "INSERT INTO Customers (CustomerName, PhoneNumber, Address, Email) VALUES (%s, %s, %s, %s)",
            (name, phone, addr or None, email or None),
            commit=True,
        )
        flash(f"Da them khach hang {name}.", "success")
        return redirect(url_for("customers.index"))

    return render_template("customers/form.html", action="add", customer=None)


@customers_bp.route("/edit/<int:cid>", methods=["GET", "POST"])
@login_required
def edit(cid):
    customer = query("SELECT * FROM Customers WHERE CustomerID=%s", (cid,), one=True)
    if not customer:
        flash("Khong tim thay khach hang.", "danger")
        return redirect(url_for("customers.index"))

    if request.method == "POST":
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        addr = request.form.get("address", "").strip()
        email = request.form.get("email", "").strip()

        dup = query(
            "SELECT CustomerID FROM Customers WHERE PhoneNumber=%s AND CustomerID!=%s",
            (phone, cid),
            one=True,
        )
        if dup:
            flash("So dien thoai da duoc dung boi khach hang khac.", "danger")
            customer = {
                "CustomerID": cid,
                "CustomerName": name,
                "PhoneNumber": phone,
                "Address": addr,
                "Email": email,
            }
            return render_template("customers/form.html", action="edit", customer=customer)

        query(
            """
            UPDATE Customers
            SET CustomerName=%s, PhoneNumber=%s, Address=%s, Email=%s
            WHERE CustomerID=%s
            """,
            (name, phone, addr or None, email or None, cid),
            commit=True,
        )
        flash("Da cap nhat thong tin.", "success")
        return redirect(url_for("customers.index"))

    return render_template("customers/form.html", action="edit", customer=customer)


@customers_bp.route("/delete/<int:cid>", methods=["POST"])
@role_required("admin")
def delete(cid):
    has_invoice = query(
        "SELECT COUNT(*) AS c FROM Invoices WHERE CustomerID=%s",
        (cid,),
        one=True,
    )["c"]
    if has_invoice:
        flash("Khong the xoa vi khach hang dang co hoa don lien quan.", "danger")
        return redirect(url_for("customers.index"))

    query("DELETE FROM Customers WHERE CustomerID=%s", (cid,), commit=True)
    flash("Da xoa khach hang.", "success")
    return redirect(url_for("customers.index"))


@customers_bp.route("/view/<int:cid>")
@login_required
def view(cid):
    customer = query("SELECT * FROM Customers WHERE CustomerID=%s", (cid,), one=True)
    if not customer:
        flash("Khong tim thay khach hang.", "danger")
        return redirect(url_for("customers.index"))

    invoices = query(
        """
        SELECT i.*, t.TableNumber
        FROM Invoices i
        JOIN `Tables` t ON i.TableID = t.TableID
        WHERE i.CustomerID=%s
        ORDER BY i.PaymentDate DESC
        LIMIT 10
        """,
        (cid,),
    )

    reservations = query(
        """
        SELECT r.*, t.TableNumber
        FROM Reservations r
        JOIN `Tables` t ON r.TableID = t.TableID
        WHERE r.CustomerID=%s
        ORDER BY r.ReservationDate DESC
        LIMIT 10
        """,
        (cid,),
    )

    total_spent = query(
        """
        SELECT COALESCE(SUM(TotalAmount), 0) AS t
        FROM Invoices
        WHERE CustomerID=%s AND Status='paid'
        """,
        (cid,),
        one=True,
    )["t"]

    return render_template(
        "customers/view.html",
        customer=customer,
        invoices=invoices,
        reservations=reservations,
        total_spent=total_spent,
    )
