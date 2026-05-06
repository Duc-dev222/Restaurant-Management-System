from flask import Blueprint, render_template, request

from .auth import login_required
from ..db import query

invoices_bp = Blueprint("invoices", __name__)


@invoices_bp.route("/")
@login_required
def index():
    status = request.args.get("status", "").strip()
    payment_method = request.args.get("payment_method", "").strip()
    q = request.args.get("q", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    conditions = []
    params = []
    if status:
        conditions.append("i.Status = %s")
        params.append(status)
    if payment_method:
        conditions.append("i.PaymentMethod = %s")
        params.append(payment_method)
    if date_from:
        conditions.append("DATE(i.PaymentDate) >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("DATE(i.PaymentDate) <= %s")
        params.append(date_to)
    if q:
        conditions.append(
            "(c.CustomerName LIKE %s OR c.PhoneNumber LIKE %s OR CAST(i.InvoiceID AS CHAR) LIKE %s)"
        )
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    invoices = query(
        f"""
        SELECT
            i.InvoiceID,
            i.SubTotal,
            i.ServiceCharge,
            i.Discount,
            i.TotalAmount,
            i.PaymentMethod,
            i.PaymentDate,
            i.Status,
            c.CustomerName,
            c.PhoneNumber,
            t.TableNumber,
            COALESCE(items.ItemCount, 0) AS ItemCount
        FROM Invoices i
        JOIN Customers c ON i.CustomerID = c.CustomerID
        JOIN `Tables` t ON i.TableID = t.TableID
        LEFT JOIN (
            SELECT InvoiceID, COUNT(*) AS ItemCount
            FROM InvoiceItems
            GROUP BY InvoiceID
        ) items ON items.InvoiceID = i.InvoiceID
        {where_sql}
        ORDER BY i.PaymentDate DESC
        LIMIT 200
        """,
        tuple(params),
    )

    stats = {
        "paid": query("SELECT COUNT(*) AS c FROM Invoices WHERE Status='paid'", one=True)["c"],
        "unpaid": query("SELECT COUNT(*) AS c FROM Invoices WHERE Status='unpaid'", one=True)["c"],
        "cancelled": query(
            "SELECT COUNT(*) AS c FROM Invoices WHERE Status='cancelled'",
            one=True,
        )["c"],
        "revenue": query(
            "SELECT COALESCE(SUM(TotalAmount), 0) AS v FROM Invoices WHERE Status='paid'",
            one=True,
        )["v"],
    }

    payment_breakdown = query(
        """
        SELECT PaymentMethod, COUNT(*) AS c, COALESCE(SUM(TotalAmount), 0) AS amount
        FROM Invoices
        WHERE Status='paid'
        GROUP BY PaymentMethod
        ORDER BY amount DESC
        """
    )

    return render_template(
        "invoices/index.html",
        invoices=invoices,
        stats=stats,
        payment_breakdown=payment_breakdown,
        filters={
            "status": status,
            "payment_method": payment_method,
            "q": q,
            "date_from": date_from,
            "date_to": date_to,
        },
    )
