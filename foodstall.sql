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
  ('Triplets', '70 Stamford Road #B1-24A Li Ka Shing Library Building, Singapore 178901'),
  ('Khoon', '90 Stamford Road #01-72 School of Economics / School of Computing and Information Systems 2 Building Singapore 178903'),
  ('Canteen Bistro', '80 Stamford Road #B1-61 School of Computing and Information Systems Building, Singapore 178902');

CREATE TABLE FoodMenu (
  menuID INT AUTO_INCREMENT PRIMARY KEY,
  stallID INT,
  menuName VARCHAR(255),
  menuPrice INT,
  FOREIGN KEY (stallID) REFERENCES FoodStall(stallID)
);

INSERT INTO FoodMenu (stallID, menuName, menuPrice)
VALUES
    (1, )

INSERT INTO FoodMenu (stallID, menuName, menuPrice)
VALUES
    (2, 'Plain Waffle', $1.25, )


INSERT INTO FoodMenu (stallID, menuName, menuPrice) 
VALUES
(3, 'Plain Waffle', 1.0, ''), 
(3, 'Kaya Waffle', 2.0, ''), 
(3, 'Butter Waffle', 2.0, ''),
(3, 'Honey Waffle', 2.0,''),
(3,'Chocolate Waffle', 2.2, ''), 
(3, 'Peanbut Butter Waffle', 2.2, ''),
(3, 'Sliced Cheese Waffle', 2.2, ''), 
(3, 'Biscoff waffle', 2.8, ''), 
(3, 'Tater tots', 2.5, ''), 
(3, 'Kaya Bun', 2.2, ''),
(3, 'Chocolate Bun', 2.2, ''),
(3, 'Peanut Butter Bun', 2.2, ''), 
(3, 'Honey Butter Bun', 2.4, ''), 
(3, 'Sweet Milk Bun', 2.2, ''), 
(3, 'Biscoff Bun', 2.8,''), 
(3, 'Mushroom Vegan Baked Rice Set', 4.4, ''),
(3, 'Chicken Sausage Baked Rice Set', 5.5, ''),
(3, 'Chicken Sausage Burger with Egg' 4.4, ''), 
(3, 'Chicken Sausage Burger with Egg Set', 6.5, ''), 
(3, 'Kopi-O hot',1.1,''),
(3, 'Kopi-O ice', 1.3,''),
(3, 'Kopi hot', 1.3, ''), 
(3, 'Kopi ice', 1.5, ''), 
(3, 'Kopi-C hot', 1.5, ''), 
(3, 'Kopi-C ice', 1.7, ''), 
(3, 'Teh-O hot', 1.1, ''), 
(3, 'Teh-O ice', 1.3, ''), 
(3, 'Teh hot', 1.3, ''), 
(3, 'Teh ice', 1.5, ''), 
(3, 'Teh-C hot', 1.5, ''), 
(3, 'Teh-C ice', 1.7, ''), 
(3, 'Ice Lemon Tea', 1.5, '')
(3, 'Original Soy Coffe hot', 3.0, ''), 
(3, 'Original Soy Coffee ice', 3.2, ''), 
(3, 'Mocha', 3.0, ''), 
(3, 'Matcha Latte', 3.0, ''), 
(3, 'Chocolate drink', 3.0, ''), 
(3, 'Taiwanese Milk Tea', 3.0, ''), 
(3, 'Ginger Milk Tea', 3.3, '')





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
(4, 'Wagyu Beef', 18,'')
(4, 'Grilled Chicken Chop', 13, ''),
(4, 'Crispy Chicken Cutlet', 13, ''), 
(4, 'Fish & Chips', 13, ''), 
(4, 'Pan-Seared Salmon', 18, ''), 
(4, 'Creamy Salmon Linguine', 15, ''), 
(4, 'Creamy Meatball Linguine', 15, ''), 
(4, 'Vongole Linguine', 15, ''),
(4, 'Mushroom Aglio Olio Linguine', 15, '')



