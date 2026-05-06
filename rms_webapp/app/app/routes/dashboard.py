from flask import Blueprint, render_template

from .auth import login_required
from ..db import query

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    stats = {
        "customers": query("SELECT COUNT(*) AS c FROM Customers", one=True)["c"],
        "tables_free": query(
            "SELECT COUNT(*) AS c FROM `Tables` WHERE Status='available'",
            one=True,
        )["c"],
        "reservations": query(
            "SELECT COUNT(*) AS c FROM Reservations WHERE DATE(ReservationDate)=CURDATE() AND Status!='cancelled'",
            one=True,
        )["c"],
        "revenue_today": query(
            """
            SELECT COALESCE(
                NULLIF((
                    SELECT COALESCE(SUM(TotalAmount), 0)
                    FROM Invoices
                    WHERE DATE(PaymentDate)=CURDATE()
                      AND Status='paid'
                ), 0),
                (
                    SELECT COALESCE(SUM(TotalAmount), 0)
                    FROM Invoices
                    WHERE Status='paid'
                      AND DATE(PaymentDate)=(
                          SELECT MAX(DATE(PaymentDate))
                          FROM Invoices
                          WHERE Status='paid'
                      )
                ),
                0
            ) AS r
            """,
            one=True,
        )["r"],
    }

    today_res = query(
        """
        SELECT r.ReservationID, c.CustomerName, c.PhoneNumber,
               t.TableNumber, t.Location, r.ReservationDate,
               r.GuestCount, r.Status
        FROM Reservations r
        JOIN Customers c ON r.CustomerID = c.CustomerID
        JOIN `Tables` t ON r.TableID = t.TableID
        WHERE DATE(r.ReservationDate) = CURDATE()
        ORDER BY r.ReservationDate
        LIMIT 8
        """
    )

    top_dishes = query(
        """
        SELECT d.DishName, SUM(ii.Quantity) AS TotalSold,
               SUM(ii.Quantity * ii.UnitPrice) AS Revenue
        FROM InvoiceItems ii
        JOIN DishVariants v ON ii.VariantID = v.VariantID
        JOIN Dishes d ON v.DishID = d.DishID
        JOIN Invoices i ON ii.InvoiceID = i.InvoiceID
        WHERE i.Status = 'paid'
        GROUP BY d.DishID, d.DishName
        ORDER BY TotalSold DESC
        LIMIT 5
        """
    )

    revenue_7d = query(
        """
        SELECT DATE(PaymentDate) AS d,
               COALESCE(SUM(TotalAmount), 0) AS r
        FROM Invoices
        WHERE Status='paid'
          AND PaymentDate >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(PaymentDate)
        ORDER BY d
        """
    )

    return render_template(
        "dashboard/index.html",
        stats=stats,
        today_res=today_res,
        top_dishes=top_dishes,
        revenue_7d=revenue_7d,
    )
