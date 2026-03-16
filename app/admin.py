from flask import render_template, request, redirect, url_for, flash, session
from app.auth import login_required

def init_admin_routes(app):
    @app.route('/owner/dashboard')
    @login_required
    def owner_dashboard():
        if session.get('role') != 'owner':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
        return render_template('owner_dashboard.html', user=session)
    
    @app.route('/staff/dashboard')
    @login_required
    def staff_dashboard():
        if session.get('role') not in ['staff', 'owner']:
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
        return render_template('staff_dashboard.html', user=session)
