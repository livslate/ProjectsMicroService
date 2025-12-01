# app.py — Projects Microservice (requires JWT from user service)

import os
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
)
from config import Config
from projectdb import ProjectDB
from project import Project

TOKEN_BLOCKLIST = set()  # here mainly for consistency


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # JWT config (must use the SAME JWT_SECRET_KEY as user microservice)
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", timedelta(minutes=60))

    # CORS
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

    # JWT
    jwt = JWTManager(app)

    # ===== Mongo Projects DB init (host/port mode) =====
    project_db = ProjectDB(
        host=app.config.get("MONGO_HOST", "localhost"),
        port=app.config.get("MONGO_PORT", 27017),
        db_name=app.config.get("MONGO_DB", "projects_db"),
        username=app.config.get("MONGO_INITDB_ROOT_USERNAME"),
        password=app.config.get("MONGO_INITDB_ROOT_PASSWORD"),
        auth_source=app.config.get("MONGO_AUTHSOURCE", "admin"),
    )

    # ============== HEALTHCHECK ==============
    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "projects"}), 200

    # ============== PROJECTS API (JWT REQUIRED) ==============
    # All of these require that the user is logged in on the user microservice
    # and passes the JWT in Authorization: Bearer <token>

    @app.post("/projects")
    @jwt_required()
    def create_project():
        """
        Create a new project.
        Expected JSON:
        {
          "project_id": "P1",
          "project_name": "My Project",
          "project_desc": "description",
          "members_list": ["user1", "user2"],
          "num_of_hardware_sets": 2,
          "hardware_set_id": ["HW1", "HW2"]
        }
        """
        data = request.get_json(force=True) or {}

        # Basic validation
        project_id = (data.get("project_id") or "").strip()
        project_name = (data.get("project_name") or "").strip()
        if not project_id or not project_name:
            return jsonify({
                "success": False,
                "message": "project_id and project_name are required"
            }), 400

        # Optional: add creator info from JWT
        username = get_jwt_identity()
        # You could store this if you like:
        data.setdefault("members_list", [])
        if username and username not in data["members_list"]:
            data["members_list"].append(username)

        project_obj = Project.from_dict(data)
        created = project_db.create_project(project_obj.to_dict())
        return jsonify({"success": True, "project": created}), 201

    @app.get("/projects")
    @jwt_required()
    def list_projects():
        projects = project_db.list_projects()
        return jsonify({"success": True, "projects": projects}), 200

    @app.get("/projects/<project_id>")
    @jwt_required()
    def get_project(project_id: str):
        proj = project_db.get_project(project_id)
        if not proj:
            return jsonify({"success": False, "message": "Project not found"}), 404
        return jsonify({"success": True, "project": proj}), 200

    @app.put("/projects/<project_id>")
    @jwt_required()
    def update_project(project_id: str):
        updates = request.get_json(force=True) or {}
        # do not allow changing project_id through updates
        updates.pop("project_id", None)

        updated = project_db.update_project(project_id, updates)
        if not updated:
            return jsonify({"success": False, "message": "Project not found"}), 404
        return jsonify({"success": True, "project": updated}), 200

    @app.delete("/projects/<project_id>")
    @jwt_required()
    def delete_project(project_id: str):
        deleted = project_db.delete_project(project_id)
        if not deleted:
            return jsonify({"success": False, "message": "Project not found"}), 404
        return jsonify({"success": True, "message": "Project deleted"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    # Use a different port from the user microservice
    port = int(os.getenv("PORT", "5003"))
    app.run(host="0.0.0.0", port=port, debug=False)
