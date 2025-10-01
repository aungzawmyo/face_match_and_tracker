#!/usr/bin/env python3
"""
Test face matching with multiple people
"""
from db import load_gallery, connect
from pipeline import build_flat_gallery, match_embedding
import numpy as np

def test_multiple_person_matching():
    print("Testing face matching with multiple people...")
    
    # Load gallery
    con = connect()
    gallery = load_gallery(con)
    flat = build_flat_gallery(gallery)
    
    print(f"\nLoaded gallery with {len(gallery)} people:")
    for name, (pid, vecs) in gallery.items():
        print(f"  - {name}: {len(vecs)} embeddings (Person ID: {pid})")
    
    print(f"\nFlat gallery has {len(flat)} total embeddings")
    
    # Test with different thresholds
    MATCH_THR = 0.50
    UNKNOWN_THR = 0.65
    
    print(f"\nTesting matching with thresholds: MATCH={MATCH_THR}, UNKNOWN={UNKNOWN_THR}")
    
    # Create some test embeddings (simulating real face embeddings)
    print("\nTesting random embeddings:")
    for i in range(5):
        test_embedding = np.random.random(512).astype(np.float32)
        # Normalize the test embedding
        test_embedding = test_embedding / (np.linalg.norm(test_embedding) + 1e-8)
        
        name, pid, dist = match_embedding(test_embedding, flat, use_average=True)
        
        status = "CONFIDENT" if dist < MATCH_THR else ("MAYBE" if dist < UNKNOWN_THR else "UNKNOWN")
        print(f"  Test {i+1}: {name} (dist: {dist:.3f}) [{status}]")
    
    con.close()
    print("\nMultiple person matching test completed!")

if __name__ == "__main__":
    test_multiple_person_matching()
