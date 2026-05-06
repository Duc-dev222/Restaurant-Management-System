from flask import Blueprint, redirect, render_template, request, url_for

from .auth import login_required
from ..db import query

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/")
@login_required
def index():
    return redirect(url_for("reports.revenue"))


@reports_bp.route("/revenue")
@login_required
def revenue():
    days = request.args.get("days", "30").strip()
    if days not in {"7", "30", "90"}:
        days = "30"
    days_int = int(days)

    summary = {
        "paid_revenue": query(
            f"""
            SELECT COALESCE(SUM(TotalAmount), 0) AS v
            FROM Invoices
            WHERE Status='paid'
              AND PaymentDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
            """,
            one=True,
        )["v"],
        "invoice_count": query(
            f"""
            SELECT COUNT(*) AS c
            FROM Invoices
            WHERE PaymentDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
            """,
            one=True,
        )["c"],
        "avg_paid_invoice": query(
            f"""
            SELECT COALESCE(AVG(TotalAmount), 0) AS v
            FROM Invoices
            WHERE Status='paid'
              AND PaymentDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
            """,
            one=True,
        )["v"],
        "active_customers": query(
            f"""
            SELECT COUNT(DISTINCT CustomerID) AS c
            FROM Invoices
            WHERE Status='paid'
              AND PaymentDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
            """,
            one=True,
        )["c"],
    }

    revenue_series = query(
        f"""
        SELECT
            DATE(PaymentDate) AS label,
            COALESCE(SUM(TotalAmount), 0) AS amount
        FROM Invoices
        WHERE Status='paid'
          AND PaymentDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
        GROUP BY DATE(PaymentDate)
        ORDER BY DATE(PaymentDate)
        """
    )

    payment_method_series = query(
        f"""
        SELECT PaymentMethod, COUNT(*) AS invoice_count, COALESCE(SUM(TotalAmount), 0) AS amount
        FROM Invoices
        WHERE Status='paid'
          AND PaymentDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
        GROUP BY PaymentMethod
        ORDER BY amount DESC
        """
    )

    top_dishes = query(
        f"""
        SELECT
            d.DishName,
            SUM(ii.Quantity) AS quantity_sold,
            SUM(ii.Quantity * ii.UnitPrice) AS revenue
        FROM InvoiceItems ii
        JOIN DishVariants v ON ii.VariantID = v.VariantID
        JOIN Dishes d ON v.DishID = d.DishID
        JOIN Invoices i ON i.InvoiceID = ii.InvoiceID
        WHERE i.Status='paid'
          AND i.PaymentDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
        GROUP BY d.DishID, d.DishName
        ORDER BY revenue DESC
        LIMIT 8
        """
    )

    reservation_status = query(
        f"""
        SELECT Status, COUNT(*) AS c
        FROM Reservations
        WHERE ReservationDate >= DATE_SUB(CURDATE(), INTERVAL {days_int} DAY)
        GROUP BY Status
        ORDER BY c DESC
        """
    )

    return render_template(
        "reports/revenue.html",
        days=days,
        summary=summary,
        revenue_series=revenue_series,
        payment_method_series=payment_method_series,
        top_dishes=top_dishes,
        reservation_status=reservation_status,
    )
