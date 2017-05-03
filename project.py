from flask import Flask, render_template, url_for, redirect, flash, request

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

@app.route('/Catalog/<categories_name>')
def items(categories_name):
    category = session.query(Categories).filter_by(name=categories_name).one()
    items = session.query(Items).filter_by(category=category)
    return render_template('items.html', category=category, items=items)


@app.route('/Catalog/<categories_name>/<item_name>/edit', methods=['GET','POST'])
def editItem(categories_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['price']:
            item.price = request.form['price']
        if request.form['picture']:
            item.picture = request.form['picture']
        session.add(item)
        session.commit()
        return redirect(url_for('items', categories_name=categories_name))
    else:
        return render_template('edititem.html', categories_name=categories_name, item=item, item_name=item_name)


@app.route('/Catalog/<categories_name>/<item_name>/delete', methods=['GET','POST'])
def deleteItem(categories_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('items', categories_name=categories_name))
    else:
        return render_template('deleteitem.html', categories_name=categories_name, item=item, item_name=item_name)


@app.route('/Catalog/<categories_name>/add', methods=['GET','POST'])
def addNewItem(categories_name):
    if request.method == 'POST':
        category = session.query(Categories).filter_by(name=categories_name).one()
        newItem = Items(name=request.form['name'], description=request.form['description'], price=request.form['price'],
                        picture=request.form['picture'], category=category, category_id=category.id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('items', categories_name=categories_name))
    else:
        return render_template('addnewitem.html', categories_name=categories_name)


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=8000)