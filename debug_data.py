from db import connect, from_blob

con = connect()

# Check people
cur = con.execute('SELECT * FROM people')
print('People:')
for row in cur:
    print(row)

# Check embeddings
cur = con.execute('SELECT person_id, vec FROM embeddings LIMIT 5')
print('\nEmbeddings:')
for row in cur:
    person_id, vec_blob = row
    vec = from_blob(vec_blob)
    print(f'Person {person_id}: shape={vec.shape}, dtype={vec.dtype}')

con.close()
