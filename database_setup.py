import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Categories(Base):
    __tablename__ = 'categories'

    name = Column(String(250), nullable=False)
    picture = Column(String(500), nullable=False)
    id = Column(Integer, primary_key=True)
    categoryItems = relationship('Items', backref='categories', lazy='dynamic')

    @property
    def serialize(self):
        return {
            "id": "self.id",
            "name": "self.name",
            "picture": "self.picture",
            "categoryItems": "self.categoryItems"
        }


class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name= Column(String(500), nullable=False)
    price = Column(String(10), nullable=False)
    picture = Column(String(500))
    description = Column(String(600))
    category_id = Column(Integer, ForeignKey('categories.id'))
    #category = relationship(Categories)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'picture': self.picture,
            'description': self.description
        }


engine = create_engine('sqlite:///jewelrydb.db')

Base.metadata.create_all(engine)

