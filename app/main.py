from flask import render_template, request, redirect, url_for, flash, session, send_file
from app.auth import login_required
import os

def init_main_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=session)
