from flask import Flask

from .config import Config
from .db import close_db


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.teardown_appcontext(close_db)

    @app.context_processor
    def inject_ui_labels():
        return {
            "ui_labels": {
                "roles": {
                    "admin": "Quản trị viên",
                    "cashier": "Thu ngân",
                    "waiter": "Phục vụ",
                },
                "table_statuses": {
                    "available": "Sẵn sàng",
                    "reserved": "Đã giữ",
                    "occupied": "Đang phục vụ",
                    "maintenance": "Bảo trì",
                },
                "table_locations": {
                    "indoor": "Trong nhà",
                    "outdoor": "Ngoài trời",
                    "vip": "VIP",
                },
                "menu_availability": {
                    "available": "Còn bán",
                    "unavailable": "Tạm ngưng",
                },
                "reservation_statuses": {
                    "pending": "Chờ xác nhận",
                    "confirmed": "Đã xác nhận",
                    "completed": "Hoàn tất",
                    "cancelled": "Đã hủy",
                },
                "invoice_statuses": {
                    "paid": "Đã thanh toán",
                    "unpaid": "Chưa thanh toán",
                    "cancelled": "Đã hủy",
                },
                "payment_methods": {
                    "cash": "Tiền mặt",
                    "card": "Thẻ",
                    "transfer": "Chuyển khoản",
                },
            }
        }

    from .routes.auth import auth_bp
    from .routes.customers import customers_bp
    from .routes.dashboard import dashboard_bp
    from .routes.invoices import invoices_bp
    from .routes.menu import menu_bp
    from .routes.reports import reports_bp
    from .routes.reservations import reservations_bp
    from .routes.tables import tables_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(tables_bp, url_prefix="/tables")
    app.register_blueprint(menu_bp, url_prefix="/menu")
    app.register_blueprint(reservations_bp, url_prefix="/reservations")
    app.register_blueprint(invoices_bp, url_prefix="/invoices")
    app.register_blueprint(reports_bp, url_prefix="/reports")

    return app
