import re
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, redirect, url_for, session, flash, jsonify, current_app, g

# Simple in-memory database untuk contoh
class SimpleDB:
    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.login_attempts = {}
        self.password_history = {}
        self.user_id_counter = 1
        self.session_id_counter = 1
    
    def get_user_by_username(self, username):
        for user_id, user in self.users.items():
            if user.get('username') == username:
                return user
        return None
    
    def get_user_by_id(self, user_id):
        return self.users.get(user_id)
    
    def create_user(self, username, password_hash, email, ip):
        user_id = self.user_id_counter
        self.user_id_counter += 1
        
        user = {
            'id': user_id,
            'username': username,
            'password': password_hash,
            'email': email,
            'join_date': datetime.now().isoformat(),
            'registration_ip': ip,
            'last_ip': ip,
            'role': 'user',
            'is_banned': False,
            'failed_attempts': 0,
            'locked_until': None,
            'last_login': None
        }
        self.users[user_id] = user
        self.password_history[user_id] = [password_hash]
        return user
    
    def create_session(self, user_id, ip, user_agent):
        session_id = self.session_id_counter
        self.session_id_counter += 1
        
        fingerprint = hashlib.sha256(
            f"{ip}|{user_agent}|{secrets.token_hex(8)}".encode()
        ).hexdigest()
        
        session_data = {
            'id': session_id,
            'user_id': user_id,
            'ip': ip,
            'user_agent': user_agent,
            'fingerprint': fingerprint,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        self.sessions[session_id] = session_data
        return session_id, fingerprint
    
    def validate_session(self, session_id, ip, user_agent, fingerprint):
        session_data = self.sessions.get(session_id)
        if not session_data:
            return None
        
        if datetime.now() > datetime.fromisoformat(session_data['expires_at']):
            self.invalidate_session(session_id)
            return None
        
        if current_app.config.get('IP_BINDING_ENABLED', True):
            if session_data['ip'] != ip:
                return None
        
        session_data['last_activity'] = datetime.now().isoformat()
        session_data['expires_at'] = (datetime.now() + timedelta(minutes=30)).isoformat()
        
        return session_data
    
    def invalidate_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def invalidate_user_sessions(self, user_id, exclude_session=None):
        to_delete = []
        for sid, sess in self.sessions.items():
            if sess['user_id'] == user_id and sid != exclude_session:
                to_delete.append(sid)
        for sid in to_delete:
            del self.sessions[sid]
    
    def record_login_attempt(self, ip, username, success):
        key = f"{ip}:{username}"
        if key not in self.login_attempts:
            self.login_attempts[key] = []
        
        self.login_attempts[key].append({
            'timestamp': time.time(),
            'success': success
        })
        
        # Clean old attempts
        self.login_attempts[key] = [
            a for a in self.login_attempts[key] 
            if time.time() - a['timestamp'] < 3600
        ]
        
        return len([a for a in self.login_attempts[key] if not a['success']])
    
    def check_rate_limit(self, ip, username):
        key = f"{ip}:{username}"
        if key not in self.login_attempts:
            return True
        
        now = time.time()
        recent_failures = [
            a for a in self.login_attempts[key]
            if not a['success'] and now - a['timestamp'] < 900
        ]
        
        return len(recent_failures) < current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    
    def check_password_history(self, user_id, new_password_hash):
        if user_id not in self.password_history:
            return True
        history = self.password_history[user_id][-5:]
        return new_password_hash not in history
    
    def update_password(self, user_id, new_password_hash):
        if user_id not in self.password_history:
            self.password_history[user_id] = []
        
        self.password_history[user_id].append(new_password_hash)
        if len(self.password_history[user_id]) > 5:
            self.password_history[user_id] = self.password_history[user_id][-5:]
        
        self.users[user_id]['password'] = new_password_hash

import time
db = SimpleDB()

def generate_password_hash(password):
    """Generate secure password hash"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000,
        dklen=64
    )
    return base64.b64encode(salt + key).decode('ascii')

def verify_password(password, hashed):
    """Verify password dengan timing attack protection"""
    try:
        import base64
        decoded = base64.b64decode(hashed.encode('ascii'))
        salt = decoded[:32]
        key = decoded[32:]
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,
            dklen=64
        )
        return hmac.compare_digest(key, new_key)
    except:
        return False

def validate_password_strength(password):
    """Validate password against security policy"""
    errors = []
    
    if len(password) < 12:
        errors.append("Password must be at least 12 characters")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    common_patterns = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if any(pattern in password.lower() for pattern in common_patterns):
        errors.append("Password contains common patterns")
    
    return errors

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        
        session_id = session.get('_session_id')
        if not session_id:
            session.clear()
            flash('Invalid session.', 'error')
            return redirect(url_for('login'))
        
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        user_agent = request.headers.get('User-Agent', '')
        fingerprint = session.get('_fingerprint')
        
        session_data = db.validate_session(session_id, ip, user_agent, fingerprint)
        if not session_data:
            session.clear()
            flash('Session expired.', 'error')
            return redirect(url_for('login'))
        
        user = db.get_user_by_id(session['user_id'])
        if not user or user.get('is_banned'):
            session.clear()
            flash('Account not found or banned.', 'error')
            return redirect(url_for('login'))
        
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

def init_auth_routes(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
            
            if not db.check_rate_limit(ip, username):
                flash('Too many failed attempts. Try again later.', 'error')
                return render_template('login.html')
            
            user = db.get_user_by_username(username)
            
            password_valid = False
            if user:
                password_valid = verify_password(password, user['password'])
            
            db.record_login_attempt(ip, username, password_valid)
            
            if user and password_valid:
                if user.get('locked_until'):
                    locked_until = datetime.fromisoformat(user['locked_until'])
                    if datetime.now() < locked_until:
                        flash('Account is locked. Try again later.', 'error')
                        return render_template('login.html')
                
                user['failed_attempts'] = 0
                user['locked_until'] = None
                
                if app.config.get('WHID_FORCE_LOGOUT_PREVIOUS', True):
                    db.invalidate_user_sessions(user['id'])
                
                user_agent = request.headers.get('User-Agent', '')
                session_id, fingerprint = db.create_session(user['id'], ip, user_agent)
                
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['_session_id'] = session_id
                session['_fingerprint'] = fingerprint
                
                user['last_login'] = datetime.now().isoformat()
                user['last_ip'] = ip
                
                flash(f'Welcome back, {user["username"]}!', 'success')
                
                if user['role'] == 'owner':
                    return redirect(url_for('owner_dashboard'))
                elif user['role'] == 'staff':
                    return redirect(url_for('staff_dashboard'))
                else:
                    return redirect(url_for('index'))
            else:
                if user:
                    user['failed_attempts'] = user.get('failed_attempts', 0) + 1
                    if user['failed_attempts'] >= app.config.get('MAX_LOGIN_ATTEMPTS', 5):
                        lock_until = datetime.now() + timedelta(minutes=app.config.get('ACCOUNT_LOCKOUT_DURATION', 30))
                        user['locked_until'] = lock_until.isoformat()
                        flash(f'Account locked for 30 minutes.', 'error')
                        return render_template('login.html')
                
                flash('Invalid username or password!', 'error')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            email = request.form['email']
            ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
            
            password_errors = validate_password_strength(password)
            if password_errors:
                for error in password_errors:
                    flash(error, 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('register.html')
            
            if db.get_user_by_username(username):
                flash('Username already exists!', 'error')
                return render_template('register.html')
            
            password_hash = generate_password_hash(password)
            user = db.create_user(username, password_hash, email, ip)
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    def logout():
        session_id = session.get('_session_id')
        if session_id:
            db.invalidate_session(session_id)
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            user = db.get_user_by_id(session['user_id'])
            
            if not verify_password(current_password, user['password']):
                flash('Current password is incorrect!', 'error')
                return render_template('change_password.html')
            
            password_errors = validate_password_strength(new_password)
            if password_errors:
                for error in password_errors:
                    flash(error, 'error')
                return render_template('change_password.html')
            
            if new_password != confirm_password:
                flash('New passwords do not match!', 'error')
                return render_template('change_password.html')
            
            new_hash = generate_password_hash(new_password)
            
            if not db.check_password_history(user['id'], new_hash):
                flash('Cannot reuse any of your last 5 passwords!', 'error')
                return render_template('change_password.html')
            
            db.update_password(user['id'], new_hash)
            
            if app.config.get('WHID_FORCE_LOGOUT_PREVIOUS', True):
                current_session = session.get('_session_id')
                db.invalidate_user_sessions(user['id'], current_session)
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('index'))
        
        return render_template('change_password.html')
