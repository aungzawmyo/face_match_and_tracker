from db import connect, from_blob

con = connect()
cur = con.execute('SELECT name, embedding FROM person_embeddings')
print('Database contents:')
for row in cur:
    name, emb_blob = row
    emb = from_blob(emb_blob)
    print(f'{name}: shape={emb.shape}, dtype={emb.dtype}')
con.close()
