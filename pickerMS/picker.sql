-- Drop tables if they exist to avoid conflicts when reinitializing
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS picker;

-- Create picker table
CREATE TABLE picker (
    pickerID INTEGER PRIMARY KEY AUTOINCREMENT,
    pickerName VARCHAR(100) NOT NULL,
    pickerPhone VARCHAR(20) NOT NULL
);

-- Create orders table for order confirmation
CREATE TABLE orders (
    orderID INTEGER PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    pickerID INTEGER,
    confirmationTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pickerID) REFERENCES picker(pickerID)
);

-- Create indices for better query performance
CREATE INDEX idx_orders_pickerID ON orders(pickerID);
CREATE INDEX idx_picker_name ON picker(pickerName);

-- Insert sample data (optional, comment out if not needed)
INSERT INTO picker (pickerName, pickerPhone) VALUES 
('John Doe', '555-123-4567'),
('Jane Smith', '555-765-4321'),
('Robert Johnson', '555-987-6543');

-- Create view for active pickers with order counts (optional)
CREATE VIEW picker_stats AS
SELECT 
    p.pickerID,
    p.pickerName,
    p.pickerPhone,
    COUNT(o.orderID) as orderCount
FROM 
    picker p
LEFT JOIN 
    orders o ON p.pickerID = o.pickerID
GROUP BY 
    p.pickerID;
