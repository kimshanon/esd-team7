from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/FoodStallsDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class FoodStall(db.Model):
    __tablename__ = 'FoodStall'

    stallID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stallName = db.Column(db.String(255), nullable=False)
    stallLocation = db.Column(db.String(255), nullable=False)

    menus = db.relationship('FoodMenu', back_populates='stall')

    def __init__(self, stallName, stallLocation):
        self.stallName = stallName
        self.stallLocation = stallLocation

    def json(self):
        return {
            "stallID": self.stallID,
            "stallName": self.stallName,
            "stallLocation": self.stallLocation,
            "menus": [menu.json() for menu in self.menus]
        }


from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class FoodStall(db.Model):
    __tablename__ = 'FoodStall'

    stallID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stallName = db.Column(db.String(255), nullable=False)
    stallLocation = db.Column(db.String(255), nullable=False)

    # One to many relationship with FoodMenu
    menus = db.relationship('FoodMenu', back_populates='stall')

    def __init__(self, stallName, stallLocation):
        self.stallName = stallName
        self.stallLocation = stallLocation

    def json(self):
        return {
            "stallID": self.stallID,
            "stallName": self.stallName,
            "stallLocation": self.stallLocation,
            "menus": [menu.json() for menu in self.menus]
        }


class FoodMenu(db.Model):
    __tablename__ = 'FoodMenu'

    menuID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stallID = db.Column(db.Integer, db.ForeignKey('FoodStall.stallID'), nullable=False)
    menuName = db.Column(db.String(255), nullable=False)
    menuPrice = db.Column(db.Float, nullable=False)

    stall = db.relationship('FoodStall', back_populates='menus')

    def __init__(self, stallID, menuName, menuPrice):
        self.stallID = stallID
        self.menuName = menuName
        self.menuPrice = menuPrice

    def json(self):
        return {
            "menuID": self.menuID,
            "stallID": self.stallID,
            "menuName": self.menuName,
            "menuPrice": self.menuPrice
        }


if __name__ == '__main__':
    app.run(port=5000, debug=True)