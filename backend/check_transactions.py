import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app
from models import db, Transaction

with app.app_context():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(5).all()
    print("\n" + "="*80)
    print("RECENT TRANSACTIONS WITH QUANTITIES")
    print("="*80)
    for t in transactions:
        print(f"\nID: {t.id} | Type: {t.type} | Qty: {t.quantity}")
        print(f"Product: {t.product.name if t.product else 'N/A'}")
        print(f"Store: {t.store.name if t.store else 'N/A'}")
        print(f"Previous Qty: {t.previous_quantity}")
        print(f"New Qty: {t.new_quantity}")
        print(f"Note: {t.note}")
        print("-" * 80)
    print("\n")
