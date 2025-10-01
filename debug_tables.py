from db import connect

con = connect()
cur = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [row[0] for row in cur])

# Check the schema
cur = con.execute("PRAGMA table_info(people)")
print('People table schema:')
for row in cur:
    print(row)

cur = con.execute("PRAGMA table_info(embeddings)")
print('Embeddings table schema:')
for row in cur:
    print(row)

con.close()
