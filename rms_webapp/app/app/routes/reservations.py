from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import login_required
from .tables import TABLE_LEVELS, get_level_meta, table_level_name
from ..db import query

reservations_bp = Blueprint("reservations", __name__)


def parse_datetime_local(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def datetime_local_value(value):
    return value.strftime("%Y-%m-%dT%H:%M")


def load_available_tables(level_key, guest_count, reservation_dt):
    _key, _label, start, end = get_level_meta(level_key)
    if not reservation_dt or guest_count < 1:
        return []

    return query(
        """
        SELECT t.TableID, t.TableNumber, t.Capacity, t.Status, t.Location
        FROM `Tables` t
        WHERE t.TableNumber BETWEEN %s AND %s
          AND t.Capacity >= %s
          AND t.Status != 'maintenance'
          AND NOT EXISTS (
            SELECT 1
            FROM Reservations r
            WHERE r.TableID = t.TableID
              AND r.Status IN ('pending', 'confirmed')
              AND ABS(TIMESTAMPDIFF(MINUTE, r.ReservationDate, %s)) < 120
          )
        ORDER BY t.Capacity, t.TableNumber
        """,
        (start, end, guest_count, reservation_dt.strftime("%Y-%m-%d %H:%M:%S")),
    )


@reservations_bp.route("/")
@login_required
def index():
    status = request.args.get("status", "").strip()
    reservation_date = request.args.get("date", "").strip()
    q = request.args.get("q", "").strip()

    conditions = []
    params = []
    if status:
        conditions.append("r.Status = %s")
        params.append(status)
    if reservation_date:
        conditions.append("DATE(r.ReservationDate) = %s")
        params.append(reservation_date)
    if q:
        conditions.append("(c.CustomerName LIKE %s OR c.PhoneNumber LIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    reservations = query(
        f"""
        SELECT
            r.ReservationID,
            r.ReservationDate,
            r.GuestCount,
            r.Status,
            c.CustomerName,
            c.PhoneNumber,
            t.TableNumber,
            t.Location,
            t.Capacity
        FROM Reservations r
        JOIN Customers c ON r.CustomerID = c.CustomerID
        JOIN `Tables` t ON r.TableID = t.TableID
        {where_sql}
        ORDER BY r.ReservationDate DESC
        LIMIT 200
        """,
        tuple(params),
    )

    stats = {
        "today": query(
            "SELECT COUNT(*) AS c FROM Reservations WHERE DATE(ReservationDate) = CURDATE()",
            one=True,
        )["c"],
        "pending": query(
            "SELECT COUNT(*) AS c FROM Reservations WHERE Status='pending'",
            one=True,
        )["c"],
        "confirmed": query(
            "SELECT COUNT(*) AS c FROM Reservations WHERE Status='confirmed'",
            one=True,
        )["c"],
        "completed": query(
            "SELECT COUNT(*) AS c FROM Reservations WHERE Status='completed'",
            one=True,
        )["c"],
    }

    upcoming = query(
        """
        SELECT
            r.ReservationID,
            c.CustomerName,
            t.TableNumber,
            r.ReservationDate,
            r.GuestCount,
            r.Status
        FROM Reservations r
        JOIN Customers c ON r.CustomerID = c.CustomerID
        JOIN `Tables` t ON r.TableID = t.TableID
        WHERE r.ReservationDate >= NOW()
          AND r.Status IN ('pending', 'confirmed')
        ORDER BY r.ReservationDate
        LIMIT 6
        """
    )

    return render_template(
        "reservations/index.html",
        reservations=reservations,
        stats=stats,
        upcoming=upcoming,
        filters={"status": status, "date": reservation_date, "q": q},
    )


@reservations_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    default_dt = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=1)
    customers = query(
        """
        SELECT CustomerID, CustomerName, PhoneNumber
        FROM Customers
        ORDER BY CustomerName
        """
    )

    if request.method == "POST":
        form = {
            "customer_id": request.form.get("customer_id", "").strip(),
            "customer_name": request.form.get("customer_name", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "reservation_date": request.form.get("reservation_date", "").strip(),
            "guest_count": request.form.get("guest_count", "1").strip(),
            "level": request.form.get("level", TABLE_LEVELS[0][0]).strip(),
            "table_id": request.form.get("table_id", "").strip(),
            "status": request.form.get("status", "confirmed").strip(),
        }
        reservation_dt = parse_datetime_local(form["reservation_date"])

        try:
            guest_count = int(form["guest_count"])
        except ValueError:
            guest_count = 0

        errors = []
        if not reservation_dt:
            errors.append("Thời gian đặt bàn không hợp lệ.")
        if guest_count < 1:
            errors.append("Số khách phải lớn hơn 0.")
        if form["status"] not in {"pending", "confirmed"}:
            errors.append("Trạng thái tạo mới không hợp lệ.")
        if not form["table_id"]:
            errors.append("Hãy chọn bàn còn trống.")

        customer_id = form["customer_id"]
        new_customer = None
        if customer_id:
            if not query("SELECT CustomerID FROM Customers WHERE CustomerID=%s", (customer_id,), one=True):
                errors.append("Khách đã chọn không tồn tại.")
        else:
            if not form["customer_name"] or not form["phone"]:
                errors.append("Chọn khách có sẵn hoặc nhập tên và số điện thoại khách mới.")
            else:
                existing = query(
                    "SELECT CustomerID FROM Customers WHERE PhoneNumber=%s",
                    (form["phone"],),
                    one=True,
                )
                if existing:
                    customer_id = existing["CustomerID"]
                else:
                    new_customer = (form["customer_name"], form["phone"])

        available_tables = load_available_tables(form["level"], guest_count, reservation_dt)
        available_ids = {str(row["TableID"]) for row in available_tables}
        if form["table_id"] and form["table_id"] not in available_ids:
            errors.append("Bàn đã được đặt trong khung giờ này hoặc không phù hợp số khách.")

        if errors:
            for message in errors:
                flash(message, "danger")
            for row in available_tables:
                row["LevelName"] = table_level_name(row["TableNumber"])
            return render_template(
                "reservations/form.html",
                customers=customers,
                table_levels=TABLE_LEVELS,
                available_tables=available_tables,
                form=form,
            )

        if new_customer:
            customer_id = query(
                "INSERT INTO Customers (CustomerName, PhoneNumber) VALUES (%s, %s)",
                new_customer,
                commit=True,
            )

        query(
            """
            INSERT INTO Reservations (CustomerID, TableID, ReservationDate, GuestCount, Status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                customer_id,
                form["table_id"],
                reservation_dt.strftime("%Y-%m-%d %H:%M:%S"),
                guest_count,
                form["status"],
            ),
            commit=True,
        )
        if form["status"] == "confirmed":
            query(
                "UPDATE `Tables` SET Status='reserved' WHERE TableID=%s",
                (form["table_id"],),
                commit=True,
            )
        flash("Đã tạo đặt bàn.", "success")
        return redirect(url_for("reservations.index"))

    level = request.args.get("level", TABLE_LEVELS[0][0]).strip()
    date_value = request.args.get("reservation_date", datetime_local_value(default_dt)).strip()
    guest_value = request.args.get("guest_count", "2").strip()
    reservation_dt = parse_datetime_local(date_value) or default_dt
    try:
        guest_count = max(int(guest_value), 1)
    except ValueError:
        guest_count = 2

    available_tables = load_available_tables(level, guest_count, reservation_dt)
    for row in available_tables:
        row["LevelName"] = table_level_name(row["TableNumber"])

    return render_template(
        "reservations/form.html",
        customers=customers,
        table_levels=TABLE_LEVELS,
        available_tables=available_tables,
        form={
            "customer_id": "",
            "customer_name": "",
            "phone": "",
            "reservation_date": datetime_local_value(reservation_dt),
            "guest_count": str(guest_count),
            "level": get_level_meta(level)[0],
            "table_id": "",
            "status": "confirmed",
        },
    )
