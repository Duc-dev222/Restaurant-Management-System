import argparse
import os
import random
import subprocess
from datetime import datetime, timedelta

try:
    from faker import Faker
except ImportError:
    Faker = None

fake = Faker("vi_VN") if Faker else None
random.seed(42)

N = 510
OUTPUT = "insert_510_rows.sql"


def esc(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("'", "''")


def make_unique_phones(count: int):
    used = set()
    phones = []
    prefixes = [
        "032", "033", "034", "035", "036", "037", "038", "039",
        "056", "058", "070", "076", "077", "078", "079", "081",
        "082", "083", "084", "085", "086", "089", "090", "091",
        "093", "094", "096", "097", "098",
    ]
    while len(phones) < count:
        phone = random.choice(prefixes) + str(random.randint(1000000, 9999999))
        if phone not in used:
            used.add(phone)
            phones.append(phone)
    return phones


def rand_dt(days_back=90, days_forward=30):
    day_delta = random.randint(-days_forward, days_back)
    value = datetime.now() - timedelta(
        days=day_delta,
        hours=random.randint(8, 22),
        minutes=random.choice([0, 15, 30, 45]),
    )
    return value.strftime("%Y-%m-%d %H:%M:%S")


CATEGORIES = [
    (1, "Khai vị", 1),
    (2, "Món chính", 2),
    (3, "Lẩu & Nướng", 3),
    (4, "Món nước", 4),
    (5, "Đồ uống", 5),
]

DISHES = [
    (1, "Phở bò tái chín", 4, "pho_bo_tai_chin.jpg", 55000, [
        ("Tô nhỏ", -10000), ("Tô thường", 0), ("Tô lớn", 15000),
        ("Tái", 0), ("Nạm", 5000), ("Gầu", 10000),
    ]),
    (2, "Phở gà", 4, "pho_ga.jpg", 50000, [
        ("Tô nhỏ", -8000), ("Tô thường", 0), ("Tô lớn", 12000), ("Thêm trứng", 7000),
    ]),
    (3, "Bún chả Hà Nội", 2, "bun_cha_ha_noi.jpg", 60000, [
        ("Phần nhỏ", -10000), ("Phần thường", 0), ("Phần lớn", 18000),
    ]),
    (4, "Bún bò Huế", 4, "bun_bo_hue.jpg", 60000, [
        ("Tô nhỏ", -10000), ("Tô thường", 0), ("Tô lớn", 15000), ("Thêm chả", 10000),
    ]),
    (5, "Cơm tấm sườn bì", 2, "com_tam_suon_bi.jpg", 65000, [
        ("Sườn bì", 0), ("Thêm trứng", 8000), ("Thêm sườn", 25000),
    ]),
    (6, "Cơm gà Hội An", 2, "com_ga_hoi_an.jpg", 62000, [
        ("Cánh", -5000), ("Đùi", 0), ("Phần lớn", 15000),
    ]),
    (7, "Mì Quảng tôm thịt", 4, "mi_quang_tom_thit.jpg", 58000, [
        ("Tô thường", 0), ("Ít mì", -5000), ("Nhiều tôm thịt", 18000),
    ]),
    (8, "Bánh mì thịt nướng", 2, "banh_mi_thit_nuong.jpg", 30000, [
        ("Ổ thường", 0), ("Thêm trứng", 7000), ("Thêm pate", 5000),
    ]),
    (9, "Gỏi cuốn tôm thịt", 1, "goi_cuon_tom_thit.jpg", 36000, [
        ("3 cuốn", 0), ("5 cuốn", 22000),
    ]),
    (10, "Chả giò chiên", 1, "cha_gio_chien.jpg", 45000, [
        ("5 cái", 0), ("10 cái", 40000),
    ]),
    (11, "Nem chua rán", 1, "nem_chua_ran.jpg", 40000, [
        ("Phần nhỏ", -8000), ("Phần thường", 0), ("Phần lớn", 15000),
    ]),
    (12, "Lẩu Thái hải sản", 3, "lau_thai_hai_san.jpg", 220000, [
        ("Size nhỏ", 0), ("Size lớn", 90000),
    ]),
    (13, "Lẩu bò nhúng mắm", 3, "lau_bo_nhung_nam.jpg", 230000, [
        ("Size nhỏ", 0), ("Size lớn", 95000),
    ]),
    (14, "Bò lúc lắc", 2, "bo_luc_lac.jpg", 95000, [
        ("Phần nhỏ", -15000), ("Phần thường", 0), ("Phần lớn", 30000),
    ]),
    (15, "Cá kho tộ", 2, "ca_kho_to.jpg", 85000, [
        ("Phần nhỏ", -15000), ("Phần thường", 0), ("Phần lớn", 25000),
    ]),
    (16, "Canh chua tôm", 2, "canh_kho_tom.jpg", 75000, [
        ("Phần nhỏ", -12000), ("Phần thường", 0), ("Phần lớn", 25000),
    ]),
    (17, "Tôm rang muối", 2, "tom_rang_muoi.jpg", 120000, [
        ("Phần nhỏ", -25000), ("Phần thường", 0), ("Phần lớn", 45000),
    ]),
    (18, "Mực chiên giòn", 1, "muc_chien_gion.jpg", 105000, [
        ("Phần nhỏ", -20000), ("Phần thường", 0), ("Phần lớn", 40000),
    ]),
    (19, "Gà nướng mật ong", 3, "ga_nuong_mat_ong.jpg", 180000, [
        ("Nửa con", 0), ("1 con", 160000),
    ]),
    (20, "Vịt quay Bắc Kinh", 3, "vit_quay_bac_kinh.jpg", 210000, [
        ("Nửa con", 0), ("1 con", 190000),
    ]),
    (21, "Sườn nướng BBQ", 3, "suon_nuong_bbq.jpg", 130000, [
        ("Phần nhỏ", -25000), ("Phần thường", 0), ("Phần lớn", 45000),
    ]),
    (22, "Cơm chiên Dương Châu", 2, "com_chien_duong_chau.jpg", 70000, [
        ("Đĩa nhỏ", -15000), ("Đĩa thường", 0), ("Đĩa lớn", 25000),
    ]),
    (23, "Bún thịt nướng", 2, "bun_thit_nuong.jpg", 55000, [
        ("Tô thường", 0), ("Ít bún", -5000), ("Nhiều thịt", 18000),
    ]),
    (24, "Bánh xèo miền Nam", 1, "banh_xeo_mien_nam.jpg", 45000, [
        ("1 cái", 0), ("2 cái", 42000),
    ]),
    (25, "Hủ tiếu Nam Vang", 4, "hu_tieu_nam_vang.jpg", 58000, [
        ("Tô nhỏ", -10000), ("Tô thường", 0), ("Tô lớn", 15000),
    ]),
]


def write_seed(output_path):
    phones = make_unique_phones(N)
    used_reservation_slots = set()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("USE restaurantmanagement;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
        f.write(
            """
TRUNCATE TABLE InvoiceItems;
TRUNCATE TABLE Invoices;
TRUNCATE TABLE Reservations;
TRUNCATE TABLE DishVariants;
TRUNCATE TABLE Dishes;
TRUNCATE TABLE Customers;
TRUNCATE TABLE `Tables`;
TRUNCATE TABLE Users;
TRUNCATE TABLE MenuCategories;
"""
        )

        for cid, name, order in CATEGORIES:
            f.write(f"INSERT INTO MenuCategories VALUES ({cid}, '{esc(name)}', {order});\n")

        for i in range(1, N + 1):
            cap = random.choice([2, 4, 4, 6, 8])
            if i <= 450:
                location = "indoor"
            elif i <= 500:
                location = "outdoor"
            else:
                location = "vip"
            status = random.choice(["available", "available", "available", "reserved", "occupied", "maintenance"])
            f.write(f"INSERT INTO `Tables` VALUES ({i},{i},{cap},'{status}','{location}');\n")

        for i in range(1, N + 1):
            name = fake.name() if fake else f"Khách hàng {i:03d}"
            f.write(
                f"INSERT INTO Customers VALUES ({i},'{esc(name)}','{phones[i - 1]}','Địa chỉ {i}','c{i}@mail.com');\n"
            )

        for did, name, cid, _image, _base_price, _variants in DISHES:
            f.write(f"INSERT INTO Dishes VALUES ({did},{cid},'{esc(name)}',NULL,1);\n")

        variant_map = {}
        vid = 1
        for did, _name, _cid, _image, base_price, variants in DISHES:
            for variant_name, delta in variants:
                price = base_price + delta
                f.write(f"INSERT INTO DishVariants VALUES ({vid},{did},'{esc(variant_name)}',{price});\n")
                variant_map.setdefault(did, []).append((vid, price))
                vid += 1

        users = [
            (1, "admin", "REPLACE_WITH_HASH", "Quản trị viên", "admin"),
            (2, "cashier", "REPLACE_WITH_HASH", "Thu ngân", "cashier"),
            (3, "waiter1", "REPLACE_WITH_HASH", "Phục vụ", "waiter"),
        ]
        for user in users:
            f.write(
                "INSERT INTO Users VALUES "
                f"({user[0]},'{user[1]}','{user[2]}','{esc(user[3])}','{user[4]}');\n"
            )

        reservation_statuses = ["pending", "confirmed", "completed", "cancelled"]
        for i in range(1, N + 1):
            table_id = random.randint(1, N)
            reservation_dt = rand_dt()
            while (table_id, reservation_dt) in used_reservation_slots:
                table_id = random.randint(1, N)
                reservation_dt = rand_dt()
            used_reservation_slots.add((table_id, reservation_dt))

            guest_count = random.choice([1, 2, 2, 3, 4, 5, 6, 8])
            status = random.choice(reservation_statuses)
            f.write(
                "INSERT INTO Reservations VALUES "
                f"({i},{i},{table_id},'{reservation_dt}',{guest_count},'{status}');\n"
            )

        for i in range(1, N + 1):
            table_id = random.randint(1, N)
            payment_method = random.choice(["cash", "card", "transfer"])
            payment_date = rand_dt(days_back=90, days_forward=0)
            f.write(
                "INSERT INTO Invoices VALUES "
                f"({i},{i},{table_id},0,0,0,0,'{payment_method}','{payment_date}','paid');\n"
            )

        item_id = 1
        subtotals = {}
        variant_ids = [variant for variants in variant_map.values() for variant in variants]
        for inv_id in range(1, N + 1):
            subtotal = 0
            selected_variants = random.sample(variant_ids, k=random.randint(2, 5))
            for vid_value, price in selected_variants:
                qty = random.randint(1, 3)
                subtotal += qty * price
                f.write(
                    f"INSERT INTO InvoiceItems VALUES ({item_id},{inv_id},{vid_value},{qty},{price});\n"
                )
                item_id += 1
            subtotals[inv_id] = subtotal

        for inv_id, subtotal in subtotals.items():
            service_charge = round(subtotal * 0.05, 2)
            discount = random.choice([0, 0, 0, 10000, 20000])
            total = max(subtotal + service_charge - discount, 0)
            f.write(
                "UPDATE Invoices SET "
                f"SubTotal={subtotal},ServiceCharge={service_charge},Discount={discount},TotalAmount={total} "
                f"WHERE InvoiceID={inv_id};\n"
            )

        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")


def import_seed(output_path):
    try:
        from dotenv import load_dotenv

        script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(script_dir, "rms_webapp", "app", ".env"))
        load_dotenv()
    except ImportError:
        pass

    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "3306")
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_name = os.environ.get("DB_NAME", "restaurantmanagement")

    cmd = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        f"-h{db_host}",
        f"-P{db_port}",
        f"-u{db_user}",
        "--default-character-set=utf8mb4",
        db_name,
    ]
    if db_password:
        cmd.insert(4, f"-p{db_password}")

    with open(output_path, "r", encoding="utf-8") as sql_file:
        result = subprocess.run(cmd, stdin=sql_file, text=True, capture_output=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--import", dest="do_import", action="store_true")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()

    print("Generating data...")
    write_seed(args.output)
    print(f"SQL file created: {args.output}")

    if args.do_import:
        print("Importing...")
        import_seed(args.output)
        print("Import done!")


if __name__ == "__main__":
    main()
