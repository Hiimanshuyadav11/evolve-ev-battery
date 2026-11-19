"""
EVolve Root Deployment & Server Entrypoint.
Automatically binds to cloud provider PORT environment variable (e.g. Render, Railway, Koyeb).
"""

import os
import sys

# Ensure backend directory is on the module search path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Launching EVolve Production Server on {host}:{port}...")
    uvicorn.run("app.main:app", host=host, port=port, app_dir=backend_dir)
