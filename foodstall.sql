CREATE TABLE FoodStall (
    stallID INT PRIMARY KEY AUTO_INCREMENT,
    stallName VARCHAR(255) NOT NULL,
    stallLocation VARCHAR(255) NOT NULL
);



INSERT INTO FoodStall (stallName, stallLocation) VALUES ('Kingkong Curry', '40 Stamford Road #01-04 SMU Connexion Singapore 178908');
INSERT INTO FoodStall (stallName, stallLocation) VALUES ('Triplets', '70 Stamford Road #B1-24A Li Ka Shing Library Building, Singapore 178901');
INSERT INTO FoodStall (stallName, stallLocation) VALUES ('Khoon', '90 Stamford Road #01-72 School of Economics / School of Computing and Information Systems 2 Building Singapore 178903');
INSERT INTO FoodStall (stallName, stallLocation) VALUES ('Canteen Bistro','80 Stamford Road #B1-61 School of Computing and Information Systems Building, Singapore 178902')