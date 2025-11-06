import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.webapi import config
from src.webapi.routes_meetings import bp as meetings_bp
from src.webapi.routes_auth import bp as auth_bp
from src.webapi.models import init_db

app = Flask(__name__, static_folder=config.FRONTEND_DIST, static_url_path="")
CORS(app)

# Initialize database
init_db()

# Register API routes
app.register_blueprint(meetings_bp)
app.register_blueprint(auth_bp)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """
    Serve frontend build (Vite -> dist folder). During development you can
    run the Vite dev server and call Flask API directly.
    """
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    index_path = os.path.join(app.static_folder, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"message": "Frontend not built. Run `npm run build` in frontend/"}), 200

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)