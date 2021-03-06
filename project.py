import os
from flask import Flask, url_for, redirect, flash, request, \
    send_from_directory, jsonify
from flask import render_template as flask_render
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from PIL import Image

from database_setup import Base, Categories, Items, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import uuid
from functools import wraps


CLIENT_ID = json.loads(open('client_secrets.json', 'r').
                       read())['web']['client_id']
APPLICATION_NAME = "Item-Catalog"

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png', 'gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

engine = create_engine('sqlite:///jewelrydb.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()


@app.route('/login')
def showLogin():
    """
    Create an anti-forgery state token
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    print login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    OAuth for google connect
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter!'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    code = request.data

    try:
        # upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        print 'credentials in gconnect=%s' % credentials
        print 'credential.token_expiry=%s' % credentials.token_expiry
        print 'credentials.toke_response[expires_in]=%s' % \
              credentials.token_response["expires_in"]
        print datetime.now().time()
        login_session['expires_in'] = credentials.token_expiry

    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade authorization '
                                            'code'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # check that access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # if there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-type'] = 'application/json'
        return response

    # store the access token info in the session for later use
    login_session['access_token'] = access_token
    print 'access_token = %s' % login_session['access_token']

    # verfiy that the access token is for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID does not match "
                                            "given user ID"), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # verify that the response token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match "
                                            "app's"), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        login_session['credentials'] = credentials
        response = make_response(json.dumps("Current user is already "
                                            "connected"), 200)
        response.headers['Content-type'] = 'application/json'
        return response

    # login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print data

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id

    print 'in gconnect = %s' % login_session.keys()
    print "done"
    flash("Successfully logged in")
    return redirect(url_for('catalog'))
    # output = ''
    # output += '<h1>Welcome, '
    # output += login_session['username']
    # output += '!</h1>'
    # output += '<img src="'
    # output += login_session['picture']
    # output += '" style="width:300px; height:300px; border-radius:150px;
    #              -webkit-border-radius:150px;-moz-border-radius:150px"'
    # flash("You are now logged in as %s" % login_session['username'])
    # print "Done"
    # return output


# Disconnect - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect', methods=['GET'])
def gDisconnect():
    """
    Disconnect a user
    """
    # only disconnect a connected user
    print 'in disconnect = %s ' % login_session.keys()

    access_token = login_session.get('access_token')
    print 'access_token=%s' % access_token
    if access_token is None:
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print result['status']

    # if access_token is present but expired disconnect the user
    expire_in = login_session.get('expires_in')
    if expire_in:
        R = datetime.now() > expire_in
    else:
        R = False
    print R

    if result['status'] == '200' or R:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['email']
        # response = make_response(json.dumps('Successfully disconnected'),
        #                          200
        # response.headers['Content-type'] = 'application/json'
        flash("Successfully disconnected")
        # return response
        return redirect(url_for('catalog'))
    else:
        response = make_response(json.dumps('Failed to revoke token for '
                                            'given user', 400))
        response.headers['Content-type'] = 'application/json'
        return response


def login_required(function):
    @wraps(function)
    def wrapper(**kw):
        if not userLoggedIn():
            return redirect('/login')
        else:
            return function(**kw)
    return wrapper


def render_template(template_name, **params):
    if 'username' in login_session:
        params['username'] = login_session['username']
        print params['username']
    return flask_render(template_name, **params)


# All categories
@app.route('/')
@app.route('/Catalog')
def catalog():
    """
    Main page - show all categories
    """
    try:
        categories = getAllCategories()
        return render_template('catalog.html', categories=categories, c=True)
    except:
        flash('Sorry catalog does not exist')


# All the items in a particular category
@app.route('/Catalog/<string:categories_name>')
def items(categories_name):
    """
    Show all items in a category
    param: categories_name
    """
    categories = getAllCategories()
    try:
        category = getCategory(categories_name)
        items = getAllItems(category.id)
        return render_template('items.html', category=category, items=items,
                               categories=categories, i=True)
    except:
        flash('Category does not exist')
        return redirect(url_for('catalog'))


# show details of a particular item
@app.route('/Catalog/<string:category_name>/<string:item_name>/show')
def showItem(category_name, item_name):
    """
    Show details of a particular item
    param: category_name
    param: item_name
    """
    categories = getAllCategories()
    category = getCategory(category_name)
    try:
        item = getItem(item_name)
        return render_template('show.html', category=category, item=item,
                               categories=categories, show_item=True)
    except:
        flash('Item does not exist')
        return redirect(url_for('catalog'))


# JSON for the whole catalog - all categories & their respective items
@app.route('/Catalog/catalog.json')
def catalogJson():
    """
    JSON for entire catalog - all categories along with the items in each
    category
    """
    categories = getAllCategories()
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

    # R = json.dumps(serializedResult, indent=4, separators=(',',':'))
    # print R
    return jsonify(categories=serializedResult)


# JSON for a particular category with all its items
@app.route('/Catalog/<string:category_name>/category.json')
def categoryJson(category_name):
    """
    JSON for a particular category with all its items
    param: category_name
    """
    category = getCategory(category_name)
    print category.name
    serializedResult = []
    serializedItems = {}
    allItems = []
    for i in category.categoryItems:
        item = {}
        for cName in Items.__table__.columns.keys():
            item[cName] = getattr(i, cName)
        allItems.append(item)
        serializedItems['items'] = allItems
    for columnName in Categories.__table__.columns.keys():
        serializedItems[columnName] = getattr(category, columnName)
    serializedResult.append(serializedItems)

    return jsonify(category=serializedResult)


# JSON for all items in a category
@app.route('/Catalog/<string:category_name>/items.json')
def itemsJson(category_name):
    """
    JSON for all items in a category
    param: category_name
    """
    print category_name
    category = getCategory(category_name)

    items = getAllItems(category.id)
    print items
    return jsonify(items=[i.serialize for i in items])


# JSON for a particular item
@app.route('/Catalog/<string:category_name>/<string:item_name>/item.json')
def itemJson(category_name, item_name):
    """
    JSON for a particular item
    param: category_name
    param: item_name
    """
    category = getCategory(category_name)
    item = getItem(item_name)
    print item
    return jsonify(item=[item.serialize])


# add a new category
@app.route('/Catalog/add', methods=['GET', 'POST'])
@login_required
def addCategory():
    """
    Add a new category if the user is logged in
    This user is now the owner of this category
    """
    categories = getAllCategories()
    if request.method == 'POST':
        name = ''
        if request.form['name']:
            name = request.form['name']
            name = name[0].upper() + name[1:].lower()
            category = session.query(Categories).filter_by(name=name).first()
            if category:
                flash('Category already exists with that name')
                return redirect(url_for('addCategory'))
        else:
            flash('Please enter category name')
            return redirect(url_for('addCategory'))

        id = getUserId(login_session['email'])

        if request.form['description']:
            description = request.form['description']
        else:
            flash('Please enter category description')
            return redirect(url_for('addCategory'))
        image = request.files['picture']
        path = ''
        filename = ''
        print 'image=%s' % image
        print 'Allowed_file=%s' % allowed_file(image.filename)
        if image:
            if allowed_file(image.filename):
                filename = secure_filename(image.filename)
                ufilename = uniqueImageName(filename)
                print 'filename=%s' % filename
                print 'ufilename=%s' % ufilename
                i = imgResizer(image)
                path = os.path.join(app.config['UPLOAD_FOLDER'], ufilename)
                print 'path=%s' % path
                i.save(path)
                i.close()
            else:
                flash('Please upload an image file')
                return redirect(url_for('addCategory', name=name,
                                        description=description))
        else:
            flash('Please upload category image')
            return redirect(url_for('addCategory'))

        newCategory = Categories(name=request.form['name'], picture=path,
                                 description=description, user_id=id)
        session.add(newCategory)
        session.commit()
        flash('Category ' + name + ' successfully added!')
        return redirect(url_for('catalog'))
    else:
        return render_template('updatecategory.html', categories=categories,
                               newCategory=True)


# edit a category
@app.route('/Catalog/<string:category_name>/edit', methods=['GET', 'POST'])
@login_required
def editCategory(category_name):
    """
    Edit a category only if a user is logged in & is the owner of the
    category
    param: category_name
    """
    categories = getAllCategories()
    category = getCategory(category_name)
    loggeduser_id = getUserId(login_session['email'])
    if not matchUserId(loggeduser_id, category.user_id) or \
            checkAdmin(category):
        flash('You are not authorized to edit this category')
        return redirect(url_for('catalog'))

    if category:
        if request.method == 'POST':
            if request.form['name']:
                category.name = request.form['name']
            else:
                flash('Please enter a name for the category')
                return redirect(url_for('editCategory',
                                        category_name=category_name))
            if request.form['description']:
                category.description = request.form['description']
            else:
                flash('Please enter description for the category')
                return redirect(url_for('editCategory',
                                        category_name=category_name))

            if request.files['picture']:
                image = request.files['picture']
                print image
                path = ''
                if image:
                    if allowed_file(image.filename):
                        filename = secure_filename(image.filename)
                        ufilename = uniqueImageName(filename)
                        print 'filename=%s' % filename
                        i = imgResizer(image)
                        path = os.path.join(app.config['UPLOAD_FOLDER'],
                                            ufilename)
                        os.remove(category.picture)
                        i.save(path)
                        category.picture = path
                        print category.picture
                        i.close()
                    else:
                        flash('Please upload an image file')
                        return redirect(url_for('editCategory',
                                                category_name=category_name))

            session.add(category)
            session.commit()
            flash('Category ' + category.name + ' successfully updated!')
            return redirect(url_for('catalog'))
        else:
            return render_template('updatecategory.html',
                                   category_name=category.name,
                                   category=category,
                                   categories=categories)
    else:
        return page_not_found('Invalid category')


# delete a category
@app.route('/Catalog/<string:category_name>/delete', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_name):
    """
    Delete a category if the user is logged in & the owner of
    the category
    param: category_name
    """
    categories = getAllCategories()
    category = getCategory(category_name)

    loggeduser_id = getUserId(login_session['email'])
    print loggeduser_id
    print category.user_id
    if not matchUserId(loggeduser_id, category.user_id) or \
            checkAdmin(category):
        flash('You are not authorized to delete this category')
        return redirect(url_for('catalog'))

    if category:
        if request.method == 'POST':
            items = getAllItems(category.id)
            if items:
                for item in items:
                    os.remove(item.picture)
                    session.delete(item)
                    session.commit()

            os.remove(category.picture)
            session.delete(category)
            session.commit()
            flash('Category ' + category.name + ' successfully deleted!')
            return redirect(url_for('catalog'))
        else:
            return render_template('delete.html', category_name=category.name,
                                   categories=categories)
    else:
        return page_not_found('Invalid category')


# edit an item from a category
@app.route('/Catalog/<string:categories_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(categories_name, item_name):
    """
    Edit an item from a particular category only if a user is logged in
    and the owner of that item
    param: categories_name
    param: item_name
    """
    categories = getAllCategories()
    item = getItem(item_name)

    loggeduser_id = getUserId(login_session['email'])
    if not matchUserId(loggeduser_id, item.user_id) or checkAdmin(item):
        flash('You are not authorized to edit this item')
        return redirect(url_for('catalog'))

    if item:
        if request.method == 'POST':
            if request.files['picture']:
                image = request.files['picture']
                print 'image=%s' % image
                path = ''
                filename = ''
                if image:
                    if allowed_file(image.filename):
                        filename = secure_filename(image.filename)
                        print 'filename=%s' % filename
                        ufilename = uniqueImageName(filename)
                        i = imgResizer(image)
                        path = os.path.join(app.config['UPLOAD_FOLDER'],
                                            ufilename)
                        print 'in edit item, path=%s' % path
                        os.remove(item.picture)
                        i.save(path)
                        item.picture = path
                        print item.picture
                        i.close()
                else:
                    flash('Please upload an image file')
                    return redirect(url_for('editItem',
                                            categories_name=categories_name,
                                            item_name=item_name))

            for attr in request.form:
                    if request.form[attr]:
                        if attr == 'picture':
                            pass
                        setattr(item, attr, request.form[attr])
                    else:
                        flash('Please enter the %s for the item' % attr)
                        return redirect(url_for('editItem',
                                                categories_name=categories_name,
                                                item_name=item_name))
            session.add(item)
            session.commit()
            flash('Item ' + item.name + ' successfully updated!')
            return redirect(url_for('items', categories_name=categories_name))
        else:
            return render_template('updateitem.html',
                                   categories_name=categories_name, item=item,
                                   item_name=item_name,
                                   categories=categories,
                                   update_item=True)
    else:
        return page_not_found('Item not found')


# delete the item by name from a category
@app.route('/Catalog/<string:categories_name>/<item_name>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(categories_name, item_name):
    """
    Delete an item from a category if the user is logged in &
    is the owner of the item
    param: categories_name
    param: item_name
    """
    categories = getAllCategories()
    item = getItem(item_name)

    loggeduser_id = getUserId(login_session['email'])
    if not matchUserId(loggeduser_id, item.user_id) or checkAdmin(item):
        flash('You are not authorized to delete this item')
        return redirect(url_for('catalog'))

    if item:
        if request.method == 'POST':
            os.remove(item.picture)
            print item.picture
            session.delete(item)
            session.commit()
            flash('Item ' + item.name + ' successfully deleted!')
            return redirect(url_for('items', categories_name=categories_name))
        else:
            return render_template('delete.html',
                                   categories_name=categories_name,
                                   item_name=item_name,
                                   categories=categories, deleteItem=True,
                                   update_item=True)
    else:
        return page_not_found('Item not found')


# add a new item for a particular category
@app.route('/Catalog/<string:categories_name>/add', methods=['GET', 'POST'])
@login_required
def addNewItem(categories_name):
    """
    Add a new item to a category if the user is logged in
    This user is now the owner of this item
    param: categories_name
    """
    categories = getAllCategories()
    if request.method == 'POST':
        category = session.query(Categories).\
                   filter_by(name=categories_name).one()
        if category:
            if request.form['name']:
                name = request.form['name']
            else:
                flash('Please add name for the item')
                return redirect(url_for('addNewItem',
                                        categories_name=category.name))
            if request.form['description']:
                desc = request.form['description']
            else:
                flash('Please add description for the item')
                return redirect(url_for('addNewItem',
                                        categories_name=category.name))
            if request.form['price']:
                price = request.form['price']
            else:
                flash('Please add price for the item')
                return redirect(url_for('addNewItem',
                                        categories_name=category.name))
            image = request.files['picture']
            path = ''
            if image:
                if allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    ufilename = uniqueImageName(filename)
                    i = imgResizer(image)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], ufilename)
                    i.save(path)
                    i.close()
                else:
                    flash('Please upload an image file')
                    return redirect(url_for('addNewItem',
                                            categories_name=categories_name))

            else:
                flash('Please upload image for the item')
                return redirect(url_for('addNewItem',
                                        categories_name=category.name))

            newItem = Items(name=name, description=desc, price=price,
                            picture=path, category_id=category.id,
                            user_id=getUserId(login_session['email']))
            session.add(newItem)
            session.commit()
            flash('New item ' + request.form['name'] +
                  ' added for category ' + category.name)
            return redirect(url_for('items', categories_name=categories_name))
        else:
            return page_not_found('Category not found')
    else:
        return render_template('updateitem.html',
                               categories_name=categories_name,
                               categories=categories, newItem=True)


# error handler
@app.errorhandler(404)
def page_not_found(e):
    """Load custom page to display errors"""
    return render_template('error.html', error=e), 404


# get file from folder to display on page
@app.route('/<filename>')
def uploaded_file(filename):
    """Load image file from the UPLOAD_FOLDER"""
    print 'filename=%s' % filename
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# check if the extension is valid
def allowed_file(filename):
    """Validate if the uploaded file is an image file"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# get all categories
def getAllCategories():
    """Retruns all categories from the database"""
    return session.query(Categories).all()


# get a category by name
def getCategory(cname):
    """Return a particular category from the database"""
    return session.query(Categories).filter_by(name=cname).one()


# get an item by name
def getItem(iname):
    return session.query(Items).filter_by(name=iname).one()


# get all items for a particular category by id
def getAllItems(c_id):
    return session.query(Items).filter_by(category_id=c_id).all()


# get user_id by email
def getUserId(email):
    """Return the user_id"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# create a new user
def createUser(login_session):
    """Create a new user in the database"""
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   admin=False)
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# get user by user_id
def getUserInfo(user_id):
    """Return user info from database with the user_id"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


# check if the user's logged in
def userLoggedIn():
    """Check if a user is actually logged in"""
    return 'email' in login_session


# check if the current user's user_id matches to the user_id in category/item
def matchUserId(id, tomatch_id):
    """Check if the current user is the owner of a particular
     item or category
    """
    return id == tomatch_id


# check if the user is admin/super user
def checkAdmin(itemtochk):
    """Check if the current user is the admin/super user"""
    return itemtochk.user.admin


# give a unique name to each image(important so that no 2 image files
# have the same name-especially while deleting)
def uniqueImageName(image_name):
    """
    Assign a unique name to each image by adding a unique id
    (Extremely important if the user loads the same file)
    param: image_name
    """
    uId = str(uuid.uuid4())
    name = os.path.splitext(image_name)[0]
    ext = os.path.splitext(image_name)[-1]
    return name + uId + ext


# resize uploaded image to a particular size(for better display)
def imgResizer(image):
    i = Image.open(image)
    size = 500, 350
    print i.size
    i = i.resize(size, resample=0)
    return i


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
