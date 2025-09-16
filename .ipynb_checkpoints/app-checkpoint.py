from flask import Flask, request, jsonify, render_template
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import torch
import numpy as np
import pickle
import os

app = Flask(__name__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

DB_FILE = "ngit_ace_db.pkl"

# Extract embedding from PIL image
def get_embedding(img):
    """Extract face embedding from a PIL image."""
    face = mtcnn(img)
    if face is None:
        return None
    face = face.unsqueeze(0).to(device)
    with torch.no_grad():
        emb = resnet(face)
    return emb.cpu().numpy()[0]

# load database function
def load_db():
    try:
        with open(DB_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        return {}

# save database function
def save_db(db):
    with open(DB_FILE, 'wb') as f:
        pickle.dump(db, f)

# similarity function
def cosine_similarity(a, b):
    a = a / (np.linalg.norm(a) + 1e-8)
    b = b / (np.linalg.norm(b) + 1e-8)
    return float(np.dot(a, b))

# ROUTERS
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register_form')
def register_form():
    return render_template("register.html")

@app.route('/recognize_form')
def recognize_form():
    return render_template("recognize.html")

# API ROUTES
@app.route('/register', methods=['POST'])
def register_face():
    name = request.form.get("name")
    file = request.files.get("image")

    if not name or not file:
        return jsonify({"error": "Name and image are required"}), 400

    img = Image.open(file).convert('RGB')
    emb = get_embedding(img)
    if emb is None:
        return render_template("register.html", message="❌ No face detected")

    db = load_db()
    if name not in db:
        db[name] = []
    db[name].append(emb)
    save_db(db)

    return render_template("register.html", message=f"✅ Registered {name} successfully! Total samples: {len(db[name])}")

@app.route('/recognize', methods=['POST'])
def recognize_face():
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "Image is required"}), 400

    img = Image.open(file).convert('RGB')
    emb = get_embedding(img)
    if emb is None:
        return render_template("recognize.html", message="❌ No face detected")

    db = load_db()
    if not db:
        return render_template("recognize.html", message="❌ Database is empty")

    best_match, best_score = None, -1
    for name, embeddings in db.items():
        for saved_emb in embeddings:
            score = cosine_similarity(emb, saved_emb)
            if score > best_score:
                best_score = score
                best_match = name

    threshold = 0.6
    if best_score >= threshold:
        return render_template("recognize.html", message=f"✅ Recognized as: {best_match} (similarity={best_score:.2f})")
    else:
        return render_template("recognize.html", message="❌ Unknown face")

if __name__ == "__main__":
    app.run(debug=True)