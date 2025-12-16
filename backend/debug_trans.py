import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app
from models import db, Transaction
import json

with app.app_context():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(3).all()
    print("\n" + "="*80)
    print("MOST RECENT TRANSACTIONS - FULL JSON")
    print("="*80)
    for t in transactions:
        print(f"\nTransaction ID: {t.id}")
        print(json.dumps(t.to_dict(), indent=2, default=str))
        print("-" * 80)
