from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import query

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return wrap


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrap(*args, **kwargs):
            if session.get("role") not in roles:
                flash("Bạn không có quyền truy cập.", "danger")
                return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)

        return wrap

    return decorator


def _has_placeholder_passwords():
    row = query(
        "SELECT COUNT(*) AS c FROM Users WHERE PasswordHash='REPLACE_WITH_HASH'",
        one=True,
    )
    return bool(row and row["c"] > 0)


@auth_bp.route("/")
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = query("SELECT * FROM Users WHERE Username=%s", (username,), one=True)
        if user and user["PasswordHash"] != "REPLACE_WITH_HASH":
            try:
                password_ok = check_password_hash(user["PasswordHash"], password)
            except ValueError:
                password_ok = False
            if password_ok:
                session.clear()
                session["user_id"] = user["UserID"]
                session["username"] = user["Username"]
                session["full_name"] = user["FullName"]
                session["role"] = user["Role"]
                flash(f"Xin chào, {user['FullName']}!", "success")
                return redirect(url_for("dashboard.index"))

        if _has_placeholder_passwords():
            flash("Tài khoản seed chưa có mật khẩu hash. Hãy chạy /setup.", "warning")
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất thành công.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    count_row = query("SELECT COUNT(*) AS c FROM Users", one=True)
    count = count_row["c"] if count_row else 0
    has_placeholders = _has_placeholder_passwords() if count > 0 else False

    if count > 0 and not has_placeholders:
        flash("Hệ thống đã được khởi tạo. Hãy đăng nhập.", "info")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if len(password) < 8:
            flash("Mat khau setup phai co it nhat 8 ky tu.", "danger")
            return render_template("auth/setup.html", has_placeholders=has_placeholders)

        if password != password_confirm:
            flash("Mat khau xac nhan khong khop.", "danger")
            return render_template("auth/setup.html", has_placeholders=has_placeholders)

        users = [
            ("admin", "Quản trị viên", "admin"),
            ("cashier", "Thu ngân", "cashier"),
            ("waiter1", "Phục vụ", "waiter"),
        ]
        for username, fullname, role in users:
            password_hash = generate_password_hash(password)
            existing = query("SELECT UserID FROM Users WHERE Username=%s", (username,), one=True)
            if existing:
                query(
                    "UPDATE Users SET PasswordHash=%s, FullName=%s, Role=%s WHERE UserID=%s",
                    (password_hash, fullname, role, existing["UserID"]),
                    commit=True,
                )
            else:
                query(
                    "INSERT INTO Users (Username, PasswordHash, FullName, Role) VALUES (%s, %s, %s, %s)",
                    (username, password_hash, fullname, role),
                    commit=True,
                )
        flash("Khoi tao xong. Hay dang nhap bang mat khau vua thiet lap.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/setup.html", has_placeholders=has_placeholders)
