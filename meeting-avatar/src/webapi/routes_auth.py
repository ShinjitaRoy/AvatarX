from flask import Blueprint, request, jsonify
from .models import User, init_db
import re

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    if not all([name, email, password]):
        return jsonify({"error": "All fields required"}), 400
    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
        
    if User.register(name, email, password):
        return jsonify({"message": "Registration successful"})
    return jsonify({"error": "Email already registered"}), 400

@bp.route("/login", methods=["POST"]) 
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
        
    user = User.login(email, password)
    if user:
        return jsonify({"message": "Login successful", "user": user})
    return jsonify({"error": "Invalid email or password"}), 401