import sqlite3, os
paths=[r'D:/FEWINFOCAD/retail-chain-inventory-tracker/backend/database.db', r'D:/FEWINFOCAD/retail-chain-inventory-tracker/backend/instance/database.db', r'D:/FEWINFOCAD/retail-chain-inventory-tracker/instance/database.db']
for p in paths:
    print('\nDB:',p,'Exists=',os.path.exists(p))
    if not os.path.exists(p):
        continue
    try:
        conn=sqlite3.connect(p)
        cur=conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cur.fetchone():
            cur.execute('SELECT id,username,role FROM users')
            rows=cur.fetchall()
            print('Users:')
            for r in rows:
                print(' ',r)
        else:
            print('  No users table')
        conn.close()
    except Exception as e:
        print('  Error reading DB:',e)
