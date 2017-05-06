import os
from flask import Flask, render_template, url_for, redirect, flash, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename

from database_setup import Base, Categories, Items
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['jpg','jpeg','png','gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

engine = create_engine('sqlite:///jewelrydb.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()

@app.route('/')
@app.route('/Catalog')
def catalog():
    categories = session.query(Categories)
    return render_template('catalog.html', categories=categories)


@app.route('/Catalog/<string:categories_name>')
def items(categories_name):
    categories = session.query(Categories)
    category = session.query(Categories).filter_by(name=categories_name).one()
    items = session.query(Items).filter_by(category_id=category.id)
    return render_template('items.html', category=category, items=items, categories=categories)


@app.route('/Catalog/json')
def catalogJson():
    categories = session.query(Categories).all()
    serializedResult = []
    for c in categories:
        serializeditems = {}
        allItems = []
        for columnName in Categories.__table__.columns.keys():
            serializeditems[columnName] = getattr(c, columnName)
        for i in c.categoryItems:
            item = {}
            for cName in Items.__table__.columns.keys():
                item[cName] = getattr(i, cName)
            allItems.append(item)
        serializeditems['items'] = allItems
        serializedResult.append(serializeditems)
    return jsonify(categories = serializedResult)


@app.route('/Catalog/add', methods=['GET','POST'])
def addCategory():
    if request.method == 'POST':
        name = request.form['name']
        name = name[0].upper() + name[1:].lower()
        category = session.query(Categories).filter_by(name=name).first()
        if category:
            flash('Category already exists with that name')
            return redirect(url_for('addCategory'))
        else:
            newCategory = Categories(name=request.form['name'],picture=request.form['picture'])
            session.add(newCategory)
            session.commit()
            return redirect(url_for('catalog'))
    else:
        return render_template('addcategory.html')


@app.route('/Catalog/<string:category_name>/edit', methods=['GET','POST'])
def editCategory(category_name):
    category = session.query(Categories).filter_by(name=category_name).one()
    if category:
        if request.method == 'POST':
            for attr in request.form:
                if request.form[attr]:
                    setattr(category, attr, request.form[attr])
            session.add(category)
            session.commit()
            return redirect(url_for('catalog'))
        else:
            return render_template('editcategory.html', category_name=category.name, category=category)
    else:
        return page_not_found('Invalid category')


@app.route('/Catalog/<string:category_name>/delete', methods=['GET','POST'])
def deleteCategory(category_name):
    category = session.query(Categories).filter_by(name=category_name).one()
    if category:
        if request.method == 'POST':
            session.delete(category)
            session.commit()
            return redirect(url_for('catalog'))
        else:
            return render_template('deletecategory.html', category_name=category.name)
    else:
        return page_not_found('Invalid category')


@app.route('/Catalog/<string:categories_name>/<string:item_name>/edit', methods=['GET','POST'])
def editItem(categories_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    if item:
        if request.method == 'POST':
            for attr in request.form:
                    if request.form[attr]:
                        if attr == 'picture':
                            image = request.files['picture']
                            path = ''
                            if image and allowed_file(image.filename):
                                filename = secure_filename(filename)
                                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                                image.save(path)
                                os.remove(item.picture)
                                item.picture = path
                                print item.picture
                        setattr(item, attr, request.form[attr])
            session.add(item)
            session.commit()
            return redirect(url_for('items', categories_name=categories_name))
        else:
            return render_template('edititem.html', categories_name=categories_name, item=item, item_name=item_name)
    else:
        return page_not_found('Item not found')


@app.route('/Catalog/<string:categories_name>/<item_name>/delete', methods=['GET','POST'])
def deleteItem(categories_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    if item:
        if request.method == 'POST':
            os.remove(item.picture)
            print item.picture
            session.delete(item)
            session.commit()
            return redirect(url_for('items', categories_name=categories_name))
        else:
            return render_template('deleteitem.html', categories_name=categories_name, item=item, item_name=item_name)
    else:
        return page_not_found('Item not found')


@app.route('/Catalog/<string:categories_name>/add', methods=['GET','POST'])
def addNewItem(categories_name):
    if request.method == 'POST':
        category = session.query(Categories).filter_by(name=categories_name).one()
        image = request.files['picture']
        path = ''
        print 'image=%s' % image
        print 'image.filename = %s' % image.filename
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            print 'filename=%s' % filename
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print'path=%s' % path
            image.save(path)
        newItem = Items(name=request.form['name'], description=request.form['description'], price=request.form['price'],
                        picture=path, category_id=category.id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('items', categories_name=categories_name))
    else:
        return render_template('addnewitem.html', categories_name=categories_name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error=e), 404


# get file from folder to display on page
@app.route('/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def allowed_file(filename):
    # check if the extension is valid
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)