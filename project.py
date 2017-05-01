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
    category = session.query(Categories).first()
    items = session.query(Items).filter_by(category_id=category.id)
    #return render_template('catalog.html', categories=categories)
    output =""
    for i in items:
        output += i.name
        output += "</br>"

    return output


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=8000)