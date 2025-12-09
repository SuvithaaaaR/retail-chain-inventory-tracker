import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app
from models import db, User

with app.app_context():
    users = User.query.all()
    print("\n" + "="*60)
    print("USER PERMISSIONS")
    print("="*60)
    for user in users:
        perms = user.get_permissions()
        print(f"\n{user.username} ({user.role}):")
        print(f"  Permissions: {', '.join(perms)}")
    print("\n" + "="*60 + "\n")
