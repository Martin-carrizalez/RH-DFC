import bcrypt

usuarios = [
    ("admin@empresa.com", "Admin2025!"),
    ("supervisora@empresa.com", "Super2025!"),
    ("reg.norte@empresa.com", "Norte2025!"),
    ("reg.sur@empresa.com", "Sur2025!"),
    # ... agrega todos
]

print("-- SQL con hashes generados:")
print()

for email, password in usuarios:
    hash_bytes = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    hash_str = hash_bytes.decode()
    print(f"-- Password: {password}")
    print(f"'{hash_str}',")
    print()