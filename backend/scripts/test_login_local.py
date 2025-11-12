"""Local test that uses Flask's test_client to exercise the /api/auth/login endpoint
without requiring the HTTP server to be running. It creates an admin user if missing
and posts credentials to the API blueprint directly.
"""
import json
import os
import sys
# Ensure 'backend' package directory is on sys.path so we can import app and models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from models import db, User


def ensure_admin():
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Created admin user (admin/admin123)')
        else:
            # Ensure password is known for test
            admin.set_password('admin123')
            db.session.commit()
            print('Ensured admin user exists and password set')


def run_test():
    ensure_admin()
    with app.test_client() as client:
        resp = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        print('Status:', resp.status_code)
        try:
            print('JSON:', resp.get_json())
        except Exception:
            print('Response data:', resp.data.decode())


if __name__ == '__main__':
    run_test()
