
DROP DATABASE IF EXISTS PickerDB;
CREATE DATABASE PickerDB;
USE PickerDB;

CREATE TABLE Picker (
    pickerID INT PRIMARY KEY AUTO_INCREMENT,
    pickerName VARCHAR(100) NOT NULL,
    pickerPhone VARCHAR(20) NOT NULL,
    pickerStatus VARCHAR(50) DEFAULT 'Available'
);

-- Insert sample data
INSERT INTO Picker (pickerName, pickerPhone, pickerStatus) VALUES
    ('John Doe', '9876-5432', 'Available'),
    ('Jane Smith', '8765-4321', 'Busy'),
    ('Robert Johnson', '9123-4567', 'Available'),
    ('Sarah Williams', '8234-5678', 'Offline'),
    ('Michael Brown', '9345-6789', 'Available');