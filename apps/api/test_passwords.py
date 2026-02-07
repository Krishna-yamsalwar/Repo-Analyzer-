import sqlite3
from passlib.context import CryptContext

# Same config as security.py
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# Connect to database
conn = sqlite3.connect('repopilot.db')
cursor = conn.cursor()

# Get users
cursor.execute('SELECT email, hashed_password FROM users')
users = cursor.fetchall()

print("Users in database:")
for email, hash in users:
    print(f"  - {email}")
    print(f"    Hash: {hash[:50]}...")

# Test password verification
print("\n" + "="*60)
print("Testing password verification with common passwords:")
print("="*60)

test_passwords = ['password', 'password123', '123456', 'admin', 'test']

for email, stored_hash in users:
    print(f"\nUser: {email}")
    for test_pwd in test_passwords:
        result = pwd_context.verify(test_pwd, stored_hash)
        print(f"  '{test_pwd}': {result}")
    
conn.close()
