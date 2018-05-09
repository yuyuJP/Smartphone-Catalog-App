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
engine = create_engine('sqlite:///companysmartphone.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Show all companies
@app.route('/')
def showCompanies():
    companies = session.query(Company).all()
    return render_template('index.html', companies=companies)


@app.route('/companies/<int:company_id>/smartphones/')
def showCompany(company_id):
    company = session.query(Company).filter_by(id=company_id).one()
    smartphones = session.query(Smartphone).filter_by(company_id=company_id).all()
    return render_template('company.html', company=company, smartphones=smartphones)


@app.route('/companies/<int:company_id>/smartphones/<int:smartphone_id>/')
def showSmartphone(company_id, smartphone_id):
    company = session.query(Company).filter_by(id=company_id).one()
    smartphone = session.query(Smartphone).filter_by(id=smartphone_id).one()
    return render_template('smartphone.html', company=company, smartphone=smartphone)


@app.route('/companies/<int:company_id>/smartphones/<int:smartphone_id>/edit', methods=['GET', 'POST'])
def editSmartphone(company_id, smartphone_id):
    selectedCompany = session.query(Company).filter_by(id=company_id).one()
    companies = session.query(Company).all()
    editSmartphone = session.query(Smartphone).filter_by(id=smartphone_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editSmartphone.name = request.form['name']
        if request.form['description']:
            editSmartphone.description = request.form['description']
        if request.form['price']:
            editSmartphone.price = request.form['price']
        if request.form['company']:
            editSmartphone.company = request.form['company']
        session.add(editSmartphone)
        session.commit()
        return redirect(url_for('showSmartphone', company_id=company_id, smartphone_id=smartphone_id))

    return render_template('editItem.html', selectedCompany=selectedCompany, editItem=editSmartphone, companies=companies)


@app.route('/companies/<int:company_id>/smartphones/<int:smartphone_id>/delete', methods=['GET', 'POST'])
def deleteSmartphone(company_id, smartphone_id):
    company = session.query(Company).filter_by(id=company_id).one()
    smartphone = session.query(Smartphone).filter_by(id=smartphone_id).one()
    return "This is a page for deleting smartphone item"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
