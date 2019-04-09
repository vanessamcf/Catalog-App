#! /usr/bin/python
# -*- coding: utf-8 -*-
from db_setup import Base, User, Categories, Items
from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify, abort, g
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
import random
import string
import httplib2
import requests
import google.auth

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r')
                       .read())['web']['client_id']
APPLICATION_NAME = "Formigoni Store - Catalog Log"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:53092@localhost/catalog',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Autenticação e Autorização
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print(("access token received %s ") % (access_token))

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/me"

    url = '%s?access_token=%s&fields=name,id,email,picture' % (
        userinfo_url, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result.decode('utf-8'))
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = access_token

    # Get user picture
    login_session['picture'] = data["picture"]["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += \
        ' " style = "width: 300px; height: 300px;border-radius:150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    return "you have been logged out"


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('AllCatalog'))
    else:
        flash("You were not logged in to begin with!")
        redirect(url_for('AllCatalog'))


@app.route('/gconnect', methods=['GET', 'POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    # Obtain authorization code

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(access_token)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    flash("You are now logged in as %s" % login_session['username'])
    print("Done!")
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except BaseException:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON for Show All Categories.
@app.route('/catalog/category/JSON', methods=['GET', 'POST'])
def AllCategoriesJSON():
    if request.method == 'GET':
        category = session.query(Categories).order_by(asc(Categories.name))
        return jsonify(category=[category.serialize for category in category])


# JSON for Show All Items of a Category.
@app.route('/catalog/<category_name>/JSON', methods=['GET', 'POST'])
def AllItemsJSON(category_name):
    if request.method == 'GET':
        category = session.query(Categories).filter_by(
            name=category_name).first()
        items = session.query(Items).order_by(Items.id).all()
        return jsonify(items=[item.serialize for item in items])


# JSON for Show a Item.
@app.route(
    '/catalog/<item_id>/JSON',
    methods=[
        'GET',
        'POST'])
def showItemJSON(item_id):
    item = session.query(Items).filter_by(item_id=id).first()
    return jsonify(Item=[item_id.serialize])


# Navegação no Catálogo App
@app.route('/', methods=['GET', 'POST'])
@app.route('/catalog', methods=['GET', 'POST'])
def AllCatalog():
    category = session.query(Categories).order_by(asc(Categories.name))
    items = session.query(Items).order_by(desc(Items.id)).limit(12)
    return render_template('catalog.html', category=category, items=items)


@app.route('/catalog/<category_id>', methods=['GET', 'POST'])
def AllItems(category_id):
    category = session.query(Categories).filter_by(id=category_id).first()
    items = session.query(Items).filter_by(category_id=category_id).all()
    return render_template('allitems.html', items=items, category=category)


@app.route('/catalog/<category_name>/<item_name>', methods=['GET', 'POST'])
def ShowItem(category_name, item_name):
    category = session.query(Categories).filter_by(name=category_name).first()
    showitems = session.query(Items).filter_by(item_name=item_name).all()
    return render_template('item.html', category=category, items=showitems)


# Alteração do Catálogo


@app.route('/catalog/new', methods=['GET', 'POST'])
def NewItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        category_id = request.form['category']
        categ = session.query(Categories).filter_by(
            id=category_id).one_or_none()
        newItem = Items(
            item_name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,
            user_id=login_session['user_id'])
        category_name = categ.name
        session.add(newItem)
        session.commit()
        return redirect(
            url_for(
                'ShowItem',
                category_name=categ.name,
                item_name=newItem.item_name))
        flash('New Item included!')
    else:
        categories = session.query(Categories).all()
        return render_template('newItem.html', categories=categories)


@app.route('/catalog/<category_id>/<item_name>/edit', methods=['GET', 'POST'])
def EditItem(category_id, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    edit = session.query(Items).filter_by(item_name=item_name).first()
    user_id = login_session.get('user_id')
    if request.method == 'POST':
        if user_id is None or user_id != edit.user_id:
            return "You are not authorized to edit this item"
        if request.form['name']:
            edit.item_name = request.form['name']
        if request.form['description']:
            edit.description = request.form['description']
        session.add(edit)
        session.commit()
        return redirect(
            url_for(
                'AllCatalog',
                category_id=category_id,
                item_name=item_name))
        flash('Item edited!')
    else:
        category = session.query(Categories).all()
        return render_template(
            'editItem.html',
            category_id=category_id,
            item_name=item_name,
            category=category,
            items=edit)


@app.route(
    '/catalog/<category_name>/<item_name>/delete',
    methods=[
        'GET',
        'POST'])
def DeleteItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Categories).filter_by(name=category_name).first()
    delete = session.query(Items).filter_by(item_name=item_name).first()
    user_id = login_session.get('user_id')
    if request.method == 'POST':
        if user_id is None or user_id != delete.user_id:
            return "You are not authorized to edit this item"
        session.delete(delete)
        session.commit()
        return redirect(
            url_for(
                'AllCatalog',
                category_name=category_name,
                item_name=delete))
    else:
        return render_template(
            'deleteItem.html',
            category=category,
            items=delete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
