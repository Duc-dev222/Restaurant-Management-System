from flask import Blueprint, render_template, request

from .auth import login_required
from ..db import query

tables_bp = Blueprint("tables", __name__)

TABLE_LEVELS = [
    *(("floor-" + str(i), f"Tầng {i}", (i - 1) * 50 + 1, i * 50) for i in range(1, 10)),
    ("outdoor", "Ngoài trời", 451, 500),
    ("vip", "VIP", 501, 510),
]


def get_level_meta(level_key):
    return next((level for level in TABLE_LEVELS if level[0] == level_key), TABLE_LEVELS[0])


def table_level_name(table_number):
    for _key, label, start, end in TABLE_LEVELS:
        if start <= table_number <= end:
            return label
    return "Khác"


@tables_bp.route("/")
@login_required
def index():
    status = request.args.get("status", "").strip()
    level = request.args.get("level", TABLE_LEVELS[0][0]).strip()
    q = request.args.get("q", "").strip()
    selected_level = get_level_meta(level)
    selected_key, selected_label, level_start, level_end = selected_level

    conditions = []
    params = [level_start, level_end]
    conditions.append("t.TableNumber BETWEEN %s AND %s")

    if status:
        conditions.append("t.Status = %s")
        params.append(status)
    if q:
        conditions.append("CAST(t.TableNumber AS CHAR) LIKE %s")
        params.append(f"%{q}%")

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    tables = query(
        f"""
        SELECT
            t.TableID,
            t.TableNumber,
            t.Capacity,
            t.Status,
            t.Location,
            (
                SELECT COUNT(*)
                FROM Reservations r
                WHERE r.TableID = t.TableID
                  AND r.Status IN ('pending', 'confirmed')
                  AND r.ReservationDate >= NOW()
            ) AS upcoming_reservations,
            (
                SELECT MAX(r.ReservationDate)
                FROM Reservations r
                WHERE r.TableID = t.TableID
            ) AS last_reservation
        FROM `Tables` t
        {where_sql}
        ORDER BY t.TableNumber
        """,
        tuple(params),
    )

    level_tables = query(
        """
        SELECT TableID, TableNumber, Capacity, Status, Location
        FROM `Tables`
        WHERE TableNumber BETWEEN %s AND %s
        ORDER BY TableNumber
        """,
        (level_start, level_end),
    )

    for row in tables:
        row["LevelName"] = table_level_name(row["TableNumber"])
    for row in level_tables:
        row["LevelName"] = table_level_name(row["TableNumber"])

    level_stats = {
        "available": sum(1 for row in level_tables if row["Status"] == "available"),
        "unavailable": sum(1 for row in level_tables if row["Status"] != "available"),
        "total": len(level_tables),
    }

    stats = {
        "total": query("SELECT COUNT(*) AS c FROM `Tables`", one=True)["c"],
        "available": query(
            "SELECT COUNT(*) AS c FROM `Tables` WHERE Status='available'",
            one=True,
        )["c"],
        "occupied": query(
            "SELECT COUNT(*) AS c FROM `Tables` WHERE Status='occupied'",
            one=True,
        )["c"],
        "maintenance": query(
            "SELECT COUNT(*) AS c FROM `Tables` WHERE Status='maintenance'",
            one=True,
        )["c"],
    }

    return render_template(
        "tables/index.html",
        tables=tables,
        level_tables=level_tables,
        table_levels=TABLE_LEVELS,
        selected_level={"key": selected_key, "label": selected_label},
        level_stats=level_stats,
        stats=stats,
        filters={"status": status, "level": selected_key, "q": q},
    )
