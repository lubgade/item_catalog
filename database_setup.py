import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    admin = Column(Boolean, default=False)



class Categories(Base):
    __tablename__ = 'categories'

    name = Column(String(250), nullable=False)
    picture = Column(String(500), nullable=False)
    id = Column(Integer, primary_key=True)
    categoryItems = relationship('Items', backref='categories', lazy='dynamic')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            "id": "self.id",
            "name": "self.name",
            "picture": "self.picture",
            "categoryItems": "self.categoryItems",
            "user_id": "self.user_id"
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
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'picture': self.picture,
            'description': self.description,
            'user_id': self.user_id
        }


engine = create_engine('sqlite:///jewelrydb.db')

Base.metadata.create_all(engine)

