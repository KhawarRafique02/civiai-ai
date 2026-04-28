from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import base64
import urllib.request
import urllib.parse
import json

app = Flask(__name__)
CORS(app)

# Imagga API — Free, no card needed
IMAGGA_API_KEY    = "acc_312e15bc245234a"
IMAGGA_API_SECRET = "6e9a0df53b9b4f423fa4c83afa780c7f"

def analyze_with_imagga(image_bytes):
    # Image base64
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    credentials = base64.b64encode(
        f"{IMAGGA_API_KEY}:{IMAGGA_API_SECRET}".encode()
    ).decode("utf-8")

    url  = "https://api.imagga.com/v2/tags"
    data = urllib.parse.urlencode({"image_base64": image_b64}).encode("utf-8")

    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode("utf-8"))

def classify_image(result):
    tags = []
    if "result" in result and "tags" in result["result"]:
        tags = [(t["tag"]["en"].lower(), t["confidence"])
                for t in result["result"]["tags"]]

    print("Detected tags:", tags)

    categories = {
        "road_damage": [
            "pothole", "road", "crack", "asphalt", "pavement",
            "broken", "damaged road", "street", "highway", "concrete crack"
        ],
        "garbage": [
            "garbage", "trash", "waste", "litter", "rubbish",
            "refuse", "dump", "junk", "filth", "debris", "bin"
        ],
        "streetlight": [
            "street light", "lamp", "light pole", "electric pole",
            "streetlight", "lantern", "dark", "night", "lamp post"
        ],
        "water_leakage": [
            "water", "flood", "leak", "puddle", "pipe",
            "wet", "drainage", "flow", "waterlogging"
        ],
        "sewer_blockage": [
            "sewer", "drain", "manhole", "sewage", "gutter",
            "blocked", "overflow", "drainage"
        ],
        "illegal_dumping": [
            "illegal", "dumping", "rubble", "construction waste",
            "abandoned", "demolition", "junk pile"
        ],
    }

    scores = {cat: 0.0 for cat in categories}

    for tag, confidence in tags:
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in tag or tag in kw:
                    scores[cat] += confidence

    print("Scores:", scores)

    best = max(scores, key=scores.get)
    if scores[best] < 1.0:
        return "other"
    return best

@app.route("/detect", methods=["POST"])
def detect():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_bytes = request.files["image"].read()

    try:
        result   = analyze_with_imagga(image_bytes)
        category = classify_image(result)
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Detection failed", "details": str(e)}), 500

    labels_map = {
        "road_damage":     "Road Damage / Pothole",
        "garbage":         "Garbage Overflow",
        "streetlight":     "Broken Streetlight",
        "water_leakage":   "Water Leakage",
        "sewer_blockage":  "Sewer Blockage",
        "illegal_dumping": "Illegal Dumping",
        "other":           "Other Issue",
    }

    return jsonify({
        "category": category,
        "label":    labels_map.get(category, "Other Issue"),
        "message":  "Issue detected successfully"
    })

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CiviAI AI Server is running!"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)