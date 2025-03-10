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
(3, 'Plain Waffle', 1.0), 
(3, 'Kaya Waffle', 2.0,), 
(3, 'Butter Waffle', 2.0,),
(3, 'Honey Waffle', 2.0),
(3,'Chocolate Waffle', 2.2,), 
(3, 'Peanbut Butter Waffle', 2.2),
(3, 'Sliced Cheese Waffle', 2.2,), 
(3, 'Biscoff waffle', 2.8), 
(3, 'Tater tots', 2.5), 
(3, 'Kaya Bun', 2.2),
(3, 'Chocolate Bun', 2.2),
(3, 'Peanut Butter Bun', 2.2), 
(3, 'Honey Butter Bun', 2.4), 
(3, 'Sweet Milk Bun', 2.2), 
(3, 'Biscoff Bun', 2.8), 
(3, 'Mushroom Vegan Baked Rice Set', 4.4),
(3, 'Chicken Sausage Baked Rice Set', 5.5),
(3, 'Chicken Sausage Burger with Egg' 4.4), 
(3, 'Chicken Sausage Burger with Egg Set', 6.5), 
(3, 'Kopi-O hot',1.1),
(3, 'Kopi-O ice', 1.3),
(3, 'Kopi hot', 1.3), 
(3, 'Kopi ice', 1.5), 
(3, 'Kopi-C hot', 1.5), 
(3, 'Kopi-C ice', 1.7), 
(3, 'Teh-O hot', 1.1), 
(3, 'Teh-O ice', 1.3), 
(3, 'Teh hot', 1.3), 
(3, 'Teh ice', 1.5), 
(3, 'Teh-C hot', 1.5), 
(3, 'Teh-C ice', 1.7), 
(3, 'Ice Lemon Tea', 1.5)
(3, 'Original Soy Coffe hot', 3.0), 
(3, 'Original Soy Coffee ice', 3.2), 
(3, 'Mocha', 3.0), 
(3, 'Matcha Latte', 3.0), 
(3, 'Chocolate drink', 3.0), 
(3, 'Taiwanese Milk Tea', 3.0), 
(3, 'Ginger Milk Tea', 3.3)





INSERT INTO FoodMenu (stallID, menuName, menuPrice) 
VALUES 
(4, 'Fries', 6.0),
(4, 'Cheese Fries', 8.0),
(4, 'Truffle Fries', 12.0),
(4, 'Pulled Pork Fries', 12.0),
(4, 'Vongole', 12.0),
(4, 'Fried Chicken Wings', 15.0),
(4, 'Fried Caalamari', 15.0), 
(4, 'Tempura Prawns', 15.0), 
(4, 'Combo Platter', 26.0), 
(4, 'Crispy Chicken', 14.0), 
(4, 'Crispy Fish', 14.0), 
(4, 'Pulled Pork', 16.0), 
(4, 'Wagyu Beef', 18.0),
(4, 'Grilled Chicken Chop', 13.0),
(4, 'Crispy Chicken Cutlet', 13.0), 
(4, 'Fish & Chips', 13.0), 
(4, 'Pan-Seared Salmon', 18.0), 
(4, 'Creamy Salmon Linguine', 15.0), 
(4, 'Creamy Meatball Linguine', 15.0), 
(4, 'Vongole Linguine', 15.0),
(4, 'Mushroom Aglio Olio Linguine', 15.0)



