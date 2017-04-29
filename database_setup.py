import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Jewelry(Base):
    __tablename__ = 'jewelry'

    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)


class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name= Column(String(250), nullable=False)
    price = Column(String(10), nullable=False)
    jewelry_id = Column(Integer, Foreign_key('jewelry.id'))
    jewelry = relationship(Jewelry)


engine = create_engine('sqlite:///jewelrydb.db')

Base.metadata.create_all(engine)

