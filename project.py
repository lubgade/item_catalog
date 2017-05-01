from flask import Flask, render_template, url_for, redirect, flash

from database_setup import Base, Categories, Items
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

engine = create_engine('sqlite:///jewelrydb.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()

@app.route('/')

@app.route('/Catalog')
def catalog():
    categories = session.query(Categories)
    return render_template('catalog.html', categories=categories)

@app.route('/Catalog/<categories_name>/')
def items(categories_name):
    category = session.query(Categories).filter_by(name=categories_name).one()
    items = session.query(Items).filter_by(category=category)
    return render_template('items.html',category=category, items=items)


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=8000)