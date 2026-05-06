CREATE DATABASE IF NOT EXISTS restaurantmanagement
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE restaurantmanagement;

CREATE TABLE IF NOT EXISTS MenuCategories (
    CategoryID INT PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL UNIQUE,
    SortOrder INT NOT NULL UNIQUE,
    CHECK (SortOrder > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `Tables` (
    TableID INT PRIMARY KEY AUTO_INCREMENT,
    TableNumber INT NOT NULL UNIQUE,
    Capacity INT NOT NULL,
    Status ENUM('available', 'reserved', 'occupied', 'maintenance')
        NOT NULL DEFAULT 'available',
    Location ENUM('indoor', 'outdoor', 'vip') NOT NULL DEFAULT 'indoor',
    CHECK (Capacity > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Customers (
    CustomerID INT PRIMARY KEY AUTO_INCREMENT,
    CustomerName VARCHAR(255) NOT NULL,
    PhoneNumber VARCHAR(15) UNIQUE,
    Address TEXT,
    Email VARCHAR(255) UNIQUE
) ENGINE=InnoDB;

-- Bỏ MenuItems, dùng Dishes + DishVariants thay thế
CREATE TABLE IF NOT EXISTS Dishes (
    DishID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryID INT NOT NULL,
    DishName VARCHAR(255) NOT NULL,
    Description TEXT,
    IsAvailable TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT fk_dishes_category
        FOREIGN KEY (CategoryID) REFERENCES MenuCategories(CategoryID),
    CHECK (IsAvailable IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS DishVariants (
    VariantID INT PRIMARY KEY AUTO_INCREMENT,
    DishID INT NOT NULL,
    VariantName VARCHAR(100) NOT NULL DEFAULT 'Mặc định',
    Price DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_variants_dish
        FOREIGN KEY (DishID) REFERENCES Dishes(DishID),
    CONSTRAINT uq_dish_variant UNIQUE (DishID, VariantName),
    CHECK (Price > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FullName VARCHAR(255) NOT NULL,
    Role ENUM('admin', 'cashier', 'waiter') NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Reservations (
    ReservationID INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID INT NOT NULL,
    TableID INT NOT NULL,
    ReservationDate DATETIME NOT NULL,
    GuestCount INT NOT NULL,
    Status ENUM('pending', 'confirmed', 'completed', 'cancelled')
        NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_reservations_customer
        FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    CONSTRAINT fk_reservations_table
        FOREIGN KEY (TableID) REFERENCES `Tables`(TableID),
    CHECK (GuestCount > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Invoices (
    InvoiceID INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID INT NOT NULL,
    TableID INT NOT NULL,
    SubTotal DECIMAL(15, 2) NOT NULL DEFAULT 0,
    ServiceCharge DECIMAL(15, 2) NOT NULL DEFAULT 0,
    Discount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    TotalAmount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    PaymentMethod ENUM('cash', 'card', 'transfer') NOT NULL DEFAULT 'cash',
    PaymentDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('paid', 'unpaid', 'cancelled') NOT NULL DEFAULT 'unpaid',
    CONSTRAINT fk_invoices_customer
        FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    CONSTRAINT fk_invoices_table
        FOREIGN KEY (TableID) REFERENCES `Tables`(TableID),
    CHECK (SubTotal >= 0),
    CHECK (ServiceCharge >= 0),
    CHECK (Discount >= 0),
    CHECK (TotalAmount >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS InvoiceItems (
    ItemID INT PRIMARY KEY AUTO_INCREMENT,
    InvoiceID INT NOT NULL,
    VariantID INT NOT NULL,         -- ← trỏ tới variant, không phải dish
    Quantity INT NOT NULL DEFAULT 1,
    UnitPrice DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_invoiceitems_invoice
        FOREIGN KEY (InvoiceID) REFERENCES Invoices(InvoiceID),
    CONSTRAINT fk_invoiceitems_variant
        FOREIGN KEY (VariantID) REFERENCES DishVariants(VariantID),
    CONSTRAINT uq_invoice_variant UNIQUE (InvoiceID, VariantID),
    CHECK (Quantity > 0),
    CHECK (UnitPrice > 0)
) ENGINE=InnoDB;

CREATE INDEX idx_dishes_category ON Dishes(CategoryID);
CREATE INDEX idx_variants_dish ON DishVariants(DishID);
CREATE INDEX idx_reservations_customer ON Reservations(CustomerID);
CREATE INDEX idx_reservations_table ON Reservations(TableID);
CREATE INDEX idx_invoices_customer ON Invoices(CustomerID);
CREATE INDEX idx_invoices_table ON Invoices(TableID);
CREATE INDEX idx_invoiceitems_invoice ON InvoiceItems(InvoiceID);
CREATE INDEX idx_invoiceitems_variant ON InvoiceItems(VariantID);

CREATE OR REPLACE VIEW v_daily_bookings AS
SELECT
    r.ReservationID,
    DATE(r.ReservationDate) AS BookingDate,
    r.ReservationDate,
    r.GuestCount,
    r.Status,
    c.CustomerName,
    c.PhoneNumber,
    t.TableNumber,
    t.Location
FROM Reservations r
JOIN Customers c ON c.CustomerID = r.CustomerID
JOIN `Tables` t ON t.TableID = r.TableID;

CREATE OR REPLACE VIEW v_table_availability AS
SELECT
    t.TableID,
    t.TableNumber,
    t.Capacity,
    t.Status,
    t.Location,
    COUNT(r.ReservationID) AS UpcomingReservations
FROM `Tables` t
LEFT JOIN Reservations r
    ON r.TableID = t.TableID
   AND r.Status IN ('pending', 'confirmed')
   AND r.ReservationDate >= NOW()
GROUP BY t.TableID, t.TableNumber, t.Capacity, t.Status, t.Location;

CREATE OR REPLACE VIEW v_top_selling_dishes AS
SELECT
    d.DishID,
    d.DishName,
    SUM(ii.Quantity) AS TotalSold,
    SUM(ii.Quantity * ii.UnitPrice) AS Revenue
FROM InvoiceItems ii
JOIN DishVariants v ON v.VariantID = ii.VariantID
JOIN Dishes d ON d.DishID = v.DishID
JOIN Invoices i ON i.InvoiceID = ii.InvoiceID
WHERE i.Status = 'paid'
GROUP BY d.DishID, d.DishName;

DROP FUNCTION IF EXISTS fn_service_charge;
DELIMITER $$
CREATE FUNCTION fn_service_charge(subtotal DECIMAL(15, 2))
RETURNS DECIMAL(15, 2)
DETERMINISTIC
BEGIN
    RETURN ROUND(subtotal * 0.05, 2);
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_confirm_reservation;
DELIMITER $$
CREATE PROCEDURE sp_confirm_reservation(IN p_reservation_id INT)
BEGIN
    UPDATE Reservations
    SET Status = 'confirmed'
    WHERE ReservationID = p_reservation_id
      AND Status = 'pending';
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_reservation_confirm_table;
DELIMITER $$
CREATE TRIGGER trg_reservation_confirm_table
AFTER UPDATE ON Reservations
FOR EACH ROW
BEGIN
    IF NEW.Status = 'confirmed' AND OLD.Status <> 'confirmed' THEN
        UPDATE `Tables`
        SET Status = 'reserved'
        WHERE TableID = NEW.TableID;
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_reservation_insert_table;
DELIMITER $$
CREATE TRIGGER trg_reservation_insert_table
AFTER INSERT ON Reservations
FOR EACH ROW
BEGIN
    IF NEW.Status IN ('pending', 'confirmed') THEN
        UPDATE `Tables`
        SET Status = 'reserved'
        WHERE TableID = NEW.TableID;
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_invoice_paid_table_available;
DELIMITER $$
CREATE TRIGGER trg_invoice_paid_table_available
AFTER UPDATE ON Invoices
FOR EACH ROW
BEGIN
    IF NEW.Status = 'paid' AND OLD.Status <> 'paid' THEN
        UPDATE `Tables`
        SET Status = 'available'
        WHERE TableID = NEW.TableID;
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_invoice_insert_paid_table_available;
DELIMITER $$
CREATE TRIGGER trg_invoice_insert_paid_table_available
AFTER INSERT ON Invoices
FOR EACH ROW
BEGIN
    IF NEW.Status = 'paid' THEN
        UPDATE `Tables`
        SET Status = 'available'
        WHERE TableID = NEW.TableID;
    END IF;
END$$
DELIMITER ;
