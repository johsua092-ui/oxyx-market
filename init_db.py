#!/usr/bin/env python
import os
import sys
import secrets
import hashlib
import base64
from datetime import datetime

def generate_password_hash(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=64)
    return base64.b64encode(salt + key).decode('ascii')

print("=" * 60)
print("OXYX BUILDS - DATABASE INITIALIZATION")
print("=" * 60)

# Create necessary folders
os.makedirs('instance', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Generate admin password
admin_password = secrets.token_urlsafe(16)
password_hash = generate_password_hash(admin_password)

print("\n✅ Folders created successfully")
print("\n" + "=" * 60)
print("🔐 ADMIN CREDENTIALS - SAVE THIS!")
print("=" * 60)
print(f"Username: admin")
print(f"Password: {admin_password}")
print("=" * 60)
print("\n⚠️  IMPORTANT: Save these credentials now!")
print("⚠️  They will NOT be shown again.\n")

# Save to file (temporary)
with open('admin_credentials.txt', 'w') as f:
    f.write("OXYX BUILDS - ADMIN CREDENTIALS\n")
    f.write("=" * 40 + "\n")
    f.write(f"Username: admin\n")
    f.write(f"Password: {admin_password}\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 40 + "\n")
    f.write("DELETE THIS FILE AFTER SAVING CREDENTIALS!\n")

print("📄 Credentials saved to: admin_credentials.txt")
print("🗑️  DELETE this file after saving the password!\n")
print("Run the app with: python run.py")
print("Then login at: http://localhost:5000")
