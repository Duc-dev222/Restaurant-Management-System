import mysql.connector
from mysql.connector import Error
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset="utf8mb4",
            autocommit=False,
        )
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db and db.is_connected():
        db.close()


def query(sql, params=None, one=False, commit=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if commit:
            db.commit()
            return cursor.lastrowid
        rows = cursor.fetchall()
        return (rows[0] if rows else None) if one else rows
    except Error:
        if commit:
            db.rollback()
        raise
    finally:
        cursor.close()
