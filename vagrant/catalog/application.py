from flask import Flask, render_template, request, redirect, jsonify, url_for, flash  # NOQA
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Company, Smartphone, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Smartphone Catalog App"

# Connect to Database and create database session
sqlite_path = 'sqlite:///companysmartphone.db?check_same_thread=False'
engine = create_engine(sqlite_path)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state,
                           login_session=login_session)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
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
    result = json.loads(h.request(url, 'GET')[1])
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        res_msg = 'Current user is already connected.'
        response = make_response(json.dumps(res_msg),
                                 200)
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
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    return render_template('welcome.html', username=login_session['username'],
                           imgsrc=login_session['picture'])


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
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
        # Return success response
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # Return error response
        res_msg = 'Failed to revoke token for given user.'
        response = make_response(json.dumps(res_msg, 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        return redirect(url_for('showCompanies'))
    else:
        return redirect(url_for('showCompanies'))


# Show all companies
@app.route('/')
def showCompanies():
    companies = session.query(Company).all()
    smartphone_query = session.query(Smartphone)
    smartphone_desc = smartphone_query.order_by(Smartphone.id.desc())
    smartphones = smartphone_desc.limit(5).all()
    return render_template('index.html', companies=companies,
                           smartphones=smartphones,
                           login_session=login_session)

# Show company info
@app.route('/companies/<int:company_id>/smartphones/')
def showCompany(company_id):
    company = session.query(Company).filter_by(id=company_id).one()
    smartphone_query = session.query(Smartphone)
    smartphones = smartphone_query.filter_by(company_id=company_id).all()
    return render_template('company.html',
                           company=company,
                           smartphones=smartphones,
                           login_session=login_session)


# Add smartphone item from a company page
@app.route('/companies/<int:company_id>/smartphones/new',
           methods=['GET', 'POST'])
def newSmartphoneFromCompany(company_id):
    # Check if the user is already logged in.
    if 'username' not in login_session:
        return redirect('/login')
    selectedCompany = session.query(Company).filter_by(id=company_id).one()
    companies = session.query(Company).all()
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        price = request.form['price']
        comp = request.form['company']
        if name and desc and price and comp:
            comp_query = session.query(Company)
            company = comp_query.filter_by(name=comp).one()
            newSmartphone = Smartphone(user_id=login_session['user_id'],
                                       name=name,
                                       description=desc,
                                       price=price,
                                       company=company)
            session.add(newSmartphone)
            session.commit()
            return redirect(url_for('showCompany', company_id=company_id))
        else:
            # If there is no enough parameters, return error.
            return "ERORR: Not enough parameter", 400
    else:
        return render_template('newItemFromCompany.html',
                               selectedCompany=selectedCompany,
                               companies=companies,
                               login_session=login_session)


# Show one specific smartphone info
@app.route('/companies/<int:company_id>/smartphones/<int:smartphone_id>/')
def showSmartphone(company_id, smartphone_id):
    #Fetch one company filtered by company ID
    company = session.query(Company).filter_by(id=company_id).one()
    #Fetch one smartphone filtered by smartphone ID
    smartphone = session.query(Smartphone).filter_by(id=smartphone_id).one()
    # Check an item's owner
    isAuthorized = smartphone.user_id == login_session['user_id']
    print(isAuthorized)
    return render_template('smartphone.html',
                           company=company,
                           smartphone=smartphone,
                           login_session=login_session,
                           isAuthorized=isAuthorized)


# Create new smartphone item
@app.route('/new/', methods=['GET', 'POST'])
def newSmartphone():
    # Check if the user is already logged in.
    if 'username' not in login_session:
        return redirect('/login')
    companies = session.query(Company).all()
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        price = request.form['price']
        comp = request.form['company']
        # Check if all required items are contained in the request.
        if name and desc and price and comp:
            comp_query = session.query(Company)
            company = comp_query.filter_by(name=comp).one()
            newSmartphone = Smartphone(user_id=login_session['user_id'],
                                       name=name,
                                       description=desc,
                                       price=price,
                                       company=company)
            session.add(newSmartphone)
            session.commit()
            # Redirect to top page.
            return redirect(url_for('showCompanies'))
        else:
            # If there is no enough parameters, return error.
            return "ERORR: Not enough parameter", 400
    else:
        return render_template('newItem.html',
                               companies=companies,
                               login_session=login_session)


# Edit item page
@app.route('/companies/<int:company_id>/smartphones/<int:smartphone_id>/edit',
           methods=['GET', 'POST'])
def editSmartphone(company_id, smartphone_id):
    # Check if the user is already logged in.
    if 'username' not in login_session:
        return redirect('/login')
    selectedCompany = session.query(Company).filter_by(id=company_id).one()
    companies = session.query(Company).all()
    edSmartphone = session.query(Smartphone).filter_by(id=smartphone_id).one()
    # Check an item's owner
    isAuthorized = edSmartphone.user_id != login_session['user_id']
    if isAuthorized:
        return 'ERROR: You are NOT authorized to edit this item.', 403
    if request.method == 'POST':
        if request.form['name']:
            edSmartphone.name = request.form['name']
        if request.form['description']:
            edSmartphone.description = request.form['description']
        if request.form['price']:
            edSmartphone.price = request.form['price']
        if request.form['company']:
            query = session.query(Company)
            company_form = request.form['company']
            edSmartphone.company = query.filter_by(name=company_form).one()
        session.add(edSmartphone)
        session.commit()
        return redirect(url_for('showSmartphone',
                                company_id=company_id,
                                smartphone_id=smartphone_id))
    else:
        return render_template('editItem.html',
                               selectedCompany=selectedCompany,
                               editItem=edSmartphone,
                               companies=companies,
                               login_session=login_session,)


# Delete item page
@app.route('/companies/<int:company_id>/smartphones/<int:smartphone_id>/delete', methods=['GET', 'POST'])  # NOQA
def deleteSmartphone(company_id, smartphone_id):
    # Check if the user is already logged in.
    if 'username' not in login_session:
        return redirect('/login')
    company = session.query(Company).filter_by(id=company_id).one()
    delSmartphone = session.query(Smartphone).filter_by(id=smartphone_id).one()

    # Check an item's owner
    if delSmartphone.user_id != login_session['user_id']:
        return 'ERROR: You are NOT authorized to delete this item.', 403
    if request.method == 'POST':
        session.delete(delSmartphone)
        session.commit()
        return redirect(url_for('showCompany', company_id=company_id))
    else:
        return render_template('deleteItem.html',
                               company=company,
                               deleteItem=delSmartphone,
                               login_session=login_session)


# Return JSON string which contains all smartphone items
@app.route('/JSON/')
def smartphonesJSON():
    companies = session.query(Company).all()
    return jsonify(Companies=[i.serialize for i in companies])


# Return JSON string which contains all smartphone items of one specific company
@app.route('/companies/<int:company_id>/smartphones/JSON/')
def showCompanySmartphoneJSON(company_id):
    company = session.query(Company).filter_by(id=company_id).one()
    smartphone_query = session.query(Smartphone)
    smartphones = smartphone_query.filter_by(company_id=company_id).all()
    return jsonify(Smartphones=[i.serialize for i in smartphones])


#Return JSON string which contains one specific smartphone item
@app.route('/companies/<int:company_id>/smartphones/<int:smartphone_id>/JSON')
def showSmartphoneJSON(company_id, smartphone_id):
    company = session.query(Company).filter_by(id=company_id).one()
    smartphone = session.query(Smartphone).filter_by(id=smartphone_id).one()
    return jsonify(Smartphone=smartphone.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
