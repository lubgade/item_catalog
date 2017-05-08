import os
from flask import Flask, render_template, url_for, redirect, flash, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename

from database_setup import Base, Categories, Items
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']
APPLICATION_NAME = "Item-Catalog"

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['jpg','jpeg','png','gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

engine = create_engine('sqlite:///jewelrydb.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)for x in xrange(32))
    login_session['state'] = state
    print login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    #print request.args.get('state')
    #print login_session['state']
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
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade authorization code'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # check that acess toke is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url,'GET')[1])

    # if there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-type'] = 'application/json'
        return response

    # verfiy that the access token is for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID does not match given user ID"), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # verify that the response token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's"), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("Current user is already connected"), 200)
        response.headers['Content-type'] = 'application/json'
        return response

    # store the access token info in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token':credentials.access_token, 'alt':'json'}
    answer = requests.get(userinfo_url,params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # user_id = getUserId(login_session['email'])
    # if not user_id:
    #     user_id = createUser(login_session)
    #
    # login_session['user_id'] = user_id

    print 'in gconnect = %s' % login_session.keys()
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width:300px; height:300px; border-radius:150px; -webkit-border-radius:150px;-moz-border-radius:150px"'
    flash("You are now logged in as %s" % login_session['username'])
    print "Done"
    return output


# Disconnect - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect', methods=['GET'])
def gDisconnect():
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
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user', 400))
        response.headers['Content-type'] = 'application/json'
        return response



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
            image = request.files['picture']
            path = ''
            filename = ''
            print 'image=%s' % image
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                print 'filename=%s' % filename
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(path)
            newCategory = Categories(name=request.form['name'],picture=path)
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
                    if attr == 'picture':
                        image = request.files['picture']
                        path = ''
                        if image and allowed_file(image.filename):
                            filename = secure_filename(image.filename)
                            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            image.save(path)
                            os.remove(category.picture)
                            category.picture = path

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
            os.remove(category.picture)
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
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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


def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user



if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)