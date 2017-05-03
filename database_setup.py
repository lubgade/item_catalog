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


class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name= Column(String(500), nullable=False)
    price = Column(String(10), nullable=False)
    picture = Column(String(500))
    description = Column(String(600))
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Categories)


engine = create_engine('sqlite:///jewelrydb.db')

Base.metadata.create_all(engine)

