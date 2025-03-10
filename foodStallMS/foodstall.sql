CREATE DATABASE FoodStallsDB;
USE FoodStallsDB;

CREATE TABLE FoodStall (
    stallID INT PRIMARY KEY AUTO_INCREMENT,
    stallName VARCHAR(255) NOT NULL,
    stallLocation VARCHAR(255) NOT NULL
);

INSERT INTO FoodStall (stallName, stallLocation)
VALUES
  ('King Kong Curry', '40 Stamford Road #01-04 SMU Connexion Singapore 178908'),
  ('Triplets Waffle', '70 Stamford Road #B1-24A Li Ka Shing Library Building, Singapore 178901'),
  ('Khoon', '90 Stamford Road #01-72 School of Economics / School of Computing and Information Systems 2 Building Singapore 178903'),
  ('Canteen Bistro', '80 Stamford Road #B1-61 School of Computing and Information Systems Building, Singapore 178902');

CREATE TABLE FoodMenu (
  menuID INT AUTO_INCREMENT PRIMARY KEY,
  stallID INT,
  menuName VARCHAR(255),
  menuPrice FLOAT COMMENT 'Price in SGD',
  FOREIGN KEY (stallID) REFERENCES FoodStall(stallID)
);

INSERT INTO FoodMenu (stallID, menuName, menuPrice)
VALUES
    (1, 'Fresh Milk Cheese Omelette Curry Rice', 6.0),
    (1, 'Original Chicken Katsu Curry Rice', 6.0),
    (1, 'Mayo Chicken Katsu Curry Rice', 6.0),
    (1, 'Spicy Mayo Chicken Katsu Curry Rice', 6.0),
    (1, 'Cheese Mayo Chicken Katsu Curry Rice', 6.0),
    (1, 'Black Vinegar Mayo Chicken Katsu Curry Rice', 6.0),
    (1, 'Tartar Mayo Chicken Katsu Curry Rice', 6.0),
    (1, 'Truffle Mayo Curry Rice', 6.0),
    (1, 'Fish Katsu Curry Rice', 6.5),
    (1, 'Salmon Katsu Curry Rice', 7.0),
    (1, 'Ebi Katsu Curry Rice', 7.0),
    (1, 'Takoyaki Curry Rice', 6.5);

INSERT INTO FoodMenu (stallID, menuName, menuPrice)
VALUES
    (2, 'Plain Waffle', 1.8),
    (2, 'Peanut Waffle', 2.3),
    (2, 'Chocolate Waffle', 2.3),
    (2, 'Kaya Waffle', 2.3),
    (2, 'Cream Cheese Waffle', 2.3),
    (2, 'Strawberry Waffle', 2.3),
    (2, 'Blueberry Waffle', 2.3),
    (2, 'Slice Cheese Waffle', 2.3),
    (2, 'Crunchy Peanut Waffle', 2.8),
    (2, 'Chocolate Oreo Waffle', 2.8),
    (2, 'Walnut Chocolate Waffle', 2.8),
    (2, 'Almond Chocolate Waffle', 2.8),
    (2, 'Chicken Ham & Cheese Waffle', 2.8),
    (2, 'Oreo Cheese Waffle', 2.8),
    (2, 'Almond Chocolate Waffle', 2.8),
    (2, 'Blueberry Cheese Waffle', 2.8),
    (2, 'Cranberry Cheese Waffle', 2.8),
    (2, 'Redbean Waffle', 2.8);

INSERT INTO FoodMenu (stallID, menuName, menuPrice) 
VALUES 
    (4, 'Fries', 6, ''),
    (4, 'Cheese Fries', 8, ''),
    (4, 'Truffle Fries', 12, ''),
    (4, 'Pulled Pork Fries', 12, ''),
    (4, 'Vongole', 12, ''),
    (4, 'Fried Chicken Wings', 15, ''),
    (4, 'Fried Caalamari', 15, ''), 
    (4, 'Tempura Prawns', 15, ''), 
    (4, 'Combo Platter', 26, ''), 
    (4, 'Crispy Chicken', 14, ''), 
    (4, 'Crispy Fish', 14, ''), 
    (4, 'Pulled Pork', 16, ''), 
    (4, 'Wagyu Beef', 18,'');



