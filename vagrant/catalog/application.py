from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
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

# Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Show all companies
@app.route('/')
def showCompanies():
    companies = session.query(Company).all()
    return render_template('index.html', companies=companies)


@app.route('/companies/<int:company_id>/')
@app.route('/companies/<int:company_id>/Smartphones/')
def showCompany(company_id):
    return "This page is for Company page. It displays Company No.%s" % company_id


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
