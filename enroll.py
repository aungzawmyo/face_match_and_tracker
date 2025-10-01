#!/usr/bin/env python3
import argparse, os, glob, cv2, numpy as np
from db import connect, init_db, add_person, add_embedding, get_person_by_name, get_person_by_name_legacy

# Handle zoneinfo import for PyInstaller compatibility
try:
    import zoneinfo
except ImportError:
    try:
        from backports import zoneinfo
    except ImportError:
        # Create a mock zoneinfo module to prevent import errors
        import sys
        import types
        zoneinfo = types.ModuleType('zoneinfo')
        zoneinfo.ZoneInfo = lambda x: None
        zoneinfo.ZoneInfoNotFoundError = Exception
        sys.modules['zoneinfo'] = zoneinfo

import insightface

# def extract_embedding(face_app, img_path):
#     im = cv2.imread(img_path)
#     if im is None:
#         return None
#     faces = face_app.get(im)
#     if not faces:
#         return None
#     # pick largest face
#     f = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]))
#     emb = f.normed_embedding  # already L2-normalized
#     return emb
def extract_embedding(face_app, img_path):
    """Extract face embedding from image with robust error handling."""
    try:
        # Check if file exists and is readable
        if not os.path.exists(img_path):
            print(f"Warning: Image file not found: {img_path}")
            return None
            
        # Read image
        im = cv2.imread(img_path)
        if im is None:
            print(f"Warning: Could not read image: {img_path}")
            return None
            
        # Check if image has valid shape
        if not hasattr(im, 'shape') or len(im.shape) < 2:
            print(f"Warning: Invalid image shape: {img_path}")
            return None
            
        # Check if image is not empty
        if im.shape[0] == 0 or im.shape[1] == 0:
            print(f"Warning: Empty image: {img_path}")
            return None
            
        # Detect faces
        faces = face_app.get(im)
        if not faces or len(faces) == 0:
            print(f"Warning: No faces detected in: {img_path}")
            return None
            
        # Pick largest face
        f = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]))
        
        # Check if embedding is valid
        if not hasattr(f, 'normed_embedding') or f.normed_embedding is None:
            print(f"Warning: Could not extract embedding from: {img_path}")
            return None
            
        emb = f.normed_embedding  # already L2-normalized
        return emb
        
    except Exception as e:
        print(f"Error processing image {img_path}: {str(e)}")
        return None

# def enroll_from_dir(name: str, img_dir: str, min_ok: int = 5, con=None):
#     if con is None:
#         con = init_db()
#     existing = get_person_by_name_legacy(con, name)
#     if existing:
#         person_id = existing[0]
#     else:
#         # Create a simple person record for enrollment
#         cur = con.cursor()
#         cur.execute(
#             "INSERT INTO people(name, phone, dob, link, info, social_link, info1, note) VALUES (?,?,?,?,?,?,?,?)", 
#             (name, None, None, None, None, None, None, None)
#         )
#         con.commit()
#         person_id = cur.lastrowid

#     # Initialize InsightFace with robust import handling
#     try:
#         import insightface.app
#         app = insightface.app.FaceAnalysis(name="buffalo_l")
#     except AttributeError:
#         # Alternative import method
#         from insightface import app as insight_app
#         app = insight_app.FaceAnalysis(name="buffalo_l")
    
#     app.prepare(ctx_id=-1)  # CPU

#     imgs = sorted([p for p in glob.glob(os.path.join(img_dir, "*")) if os.path.isfile(p)])
#     ok = 0
#     for p in imgs:
#         emb = extract_embedding(app, p)
#         if emb is None: 
#             continue
#         add_embedding(con, person_id, emb, src_path=p)
#         ok += 1

#     if ok < min_ok:
#         raise SystemExit(f"Only {ok} usable faces found; need at least {min_ok}.")

#     print(f"Enrolled {name} with {ok} embeddings.")

def enroll_from_dir(name: str, img_dir: str, min_ok: int = 5, con=None):
    """Enroll a person from directory with comprehensive error handling."""
    try:
        if con is None:
            con = init_db()
            
        # Check if directory exists
        if not os.path.exists(img_dir):
            raise ValueError(f"Directory does not exist: {img_dir}")
            
        existing = get_person_by_name_legacy(con, name)
        if existing:
            person_id = existing[0]
        else:
            # Create a simple person record for enrollment
            cur = con.cursor()
            cur.execute(
                "INSERT INTO people(name, phone, dob, link, info, social_link, info1, note) VALUES (?,?,?,?,?,?,?,?)", 
                (name, None, None, None, None, None, None, None)
            )
            con.commit()
            person_id = cur.lastrowid

        # Initialize InsightFace with robust import handling
        try:
            import insightface.app
            app = insightface.app.FaceAnalysis(name="buffalo_l")
        except AttributeError:
            # Alternative import method
            from insightface import app as insight_app
            app = insight_app.FaceAnalysis(name="buffalo_l")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize InsightFace: {str(e)}")
        
        try:
            app.prepare(ctx_id=-1)  # CPU
        except Exception as e:
            raise RuntimeError(f"Failed to prepare InsightFace model: {str(e)}")

        # Get image files with common extensions
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
        imgs = []
        for ext in image_extensions:
            imgs.extend(glob.glob(os.path.join(img_dir, ext)))
            imgs.extend(glob.glob(os.path.join(img_dir, ext.upper())))
        
        imgs = sorted([p for p in imgs if os.path.isfile(p)])
        
        if not imgs:
            raise ValueError(f"No image files found in directory: {img_dir}")
        
        print(f"Found {len(imgs)} image files to process...")
        
        ok = 0
        processed = 0
        for p in imgs:
            processed += 1
            print(f"Processing image {processed}/{len(imgs)}: {os.path.basename(p)}")
            
            emb = extract_embedding(app, p)
            if emb is None: 
                continue
                
            add_embedding(con, person_id, emb, src_path=p)
            ok += 1
            print(f"Successfully processed {ok} images so far...")

        print(f"Enrollment complete: {ok} out of {processed} images processed successfully")
        
        if ok < min_ok:
            raise ValueError(f"Only {ok} usable faces found; need at least {min_ok}. Please check your images contain clear, visible faces.")

        print(f"Enrolled {name} with {ok} embeddings.")
        return True
        
    except Exception as e:
        print(f"Error during enrollment: {str(e)}")
        raise
    
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Enroll a person from an image folder.")
    ap.add_argument("--name", required=True, help="Person's name (unique)")
    ap.add_argument("img_dir", help="Directory containing >=5 images of the person")
    args = ap.parse_args()
    enroll_from_dir(args.name, args.img_dir)
