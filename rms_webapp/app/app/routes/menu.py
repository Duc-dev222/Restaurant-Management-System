import re
import unicodedata

from flask import Blueprint, render_template, request

from .auth import login_required
from ..db import query

menu_bp = Blueprint("menu", __name__)

IMAGE_OVERRIDES = {
    "Canh chua tôm": "canh_kho_tom.jpg",
    "Lẩu bò nhúng mắm": "lau_bo_nhung_nam.jpg",
}


def slugify(text):
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
    return text.lower().replace(" ", "_")


@menu_bp.route("/")
@login_required
def index():
    category_id = request.args.get("category", "").strip()
    availability = request.args.get("availability", "").strip()
    q = request.args.get("q", "").strip()

    conditions = []
    params = []

    if category_id:
        conditions.append("d.CategoryID = %s")
        params.append(category_id)

    if availability == "available":
        conditions.append("d.IsAvailable = 1")
    elif availability == "unavailable":
        conditions.append("d.IsAvailable = 0")

    if q:
        conditions.append("d.DishName LIKE %s")
        params.append(f"%{q}%")

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    items = query(
        f"""
        SELECT
            d.DishID,
            d.DishName,
            MIN(v.Price)                     AS MinPrice,
            MAX(v.Price)                     AS MaxPrice,
            COUNT(v.VariantID)               AS VariantCount,
            d.IsAvailable,
            c.CategoryName,
            c.CategoryID,
            COALESCE(sold.TotalSold, 0)      AS TotalSold
        FROM Dishes d
        JOIN MenuCategories c ON d.CategoryID = c.CategoryID
        LEFT JOIN DishVariants v ON v.DishID = d.DishID
        LEFT JOIN (
            SELECT dv.DishID, SUM(ii.Quantity) AS TotalSold
            FROM InvoiceItems ii
            JOIN DishVariants dv ON dv.VariantID = ii.VariantID
            GROUP BY dv.DishID
        ) sold ON sold.DishID = d.DishID
        {where_sql}
        GROUP BY d.DishID, d.DishName, d.IsAvailable, c.CategoryName, c.CategoryID, c.SortOrder, sold.TotalSold
        ORDER BY c.SortOrder, d.DishName
        """,
        tuple(params),
    )

    for item in items:
        item["Image"] = IMAGE_OVERRIDES.get(item["DishName"], slugify(item["DishName"]) + ".jpg")
        if item["MinPrice"] == item["MaxPrice"]:
            item["PriceText"] = f"{item['MinPrice']:,.0f}" if item["MinPrice"] else "0"
        else:
            item["PriceText"] = f"{item['MinPrice']:,.0f} - {item['MaxPrice']:,.0f}"

    categories = query(
        """
        SELECT
            c.CategoryID,
            c.CategoryName,
            c.SortOrder,
            COUNT(d.DishID) AS DishCount
        FROM MenuCategories c
        LEFT JOIN Dishes d ON d.CategoryID = c.CategoryID
        GROUP BY c.CategoryID, c.CategoryName, c.SortOrder
        ORDER BY c.SortOrder
        """
    )

    stats = {
        "total_items": query("SELECT COUNT(*) AS c FROM Dishes", one=True)["c"],
        "available": query(
            "SELECT COUNT(*) AS c FROM Dishes WHERE IsAvailable = 1",
            one=True,
        )["c"],
        "categories": query("SELECT COUNT(*) AS c FROM MenuCategories", one=True)["c"],
        "avg_price": query("SELECT AVG(Price) AS v FROM DishVariants", one=True)["v"] or 0,
    }

    return render_template(
        "menu/index.html",
        items=items,
        categories=categories,
        stats=stats,
        filters={"category": category_id, "availability": availability, "q": q},
    )
