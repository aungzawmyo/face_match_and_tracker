#!/usr/bin/env python3
"""
Debug the load_gallery cursor issue
"""
from db import connect

def test_cursor_issue():
    print("Testing nested cursor issue in load_gallery...")
    con = connect()
    cur = con.cursor()
    
    print("\n1. Testing current implementation (nested cursor):")
    people = {}
    for pid, name in cur.execute("SELECT id,name FROM people"):
        print(f"Processing {name} (id: {pid})")
        vecs = [b for (b,) in cur.execute("SELECT vec FROM embeddings WHERE person_id=?", (pid,))]
        print(f"  Found {len(vecs)} embeddings")
        people[name] = (pid, len(vecs))
    
    print("Final result with nested cursor:")
    for name, data in people.items():
        print(f"  {name}: {data}")
    
    print("\n2. Testing fixed implementation (separate cursors):")
    people2 = {}
    cur1 = con.cursor()
    for pid, name in cur1.execute("SELECT id,name FROM people"):
        print(f"Processing {name} (id: {pid})")
        cur2 = con.cursor()
        vecs = [b for (b,) in cur2.execute("SELECT vec FROM embeddings WHERE person_id=?", (pid,))]
        print(f"  Found {len(vecs)} embeddings")
        people2[name] = (pid, len(vecs))
        cur2.close()
    cur1.close()
    
    print("Final result with separate cursors:")
    for name, data in people2.items():
        print(f"  {name}: {data}")
    
    con.close()

if __name__ == "__main__":
    test_cursor_issue()
