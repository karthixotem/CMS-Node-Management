🚀 CMS and Node Management System

   This project consists of:

     - CMS (Django) → Central service for node management, file uploads, and real-time dashboard.

     - Node Applications (Django) → Worker nodes that self-register with CMS and handle file uploads.

     - Frontend Dashboard (React.js) → Web UI to monitor and manage nodes.


1) CMS (Django)

  - Create a new MySQL database and update .env file with credentials:

      DATABASE_USERNAME=
    
      DATABASE_PASSWORD=
    
      DATABASE_NAME=
    
      DATABASE_PORT=
    
      DATABASE_HOST=
    

  - CMS-Node-Management/cms_django   # Navigate to the CMS project

  - python -m venv cms_venv    # Create and activate a virtual environment

  - source cms_venv/bin/activate

  - pip install -r requirements.txt    # Install dependencies
 
  - python manage.py migrate    # Run migrations

  - uvicorn cms_django.asgi:application --host 0.0.0.0 --port 4000 --reload    # Start the CMS server


2) Node apps (two terminals)
	
  # Node 1

     - cd ../node_project

     - python -m venv node_project_env

     - source node_project_env/bin/activate

     - pip install -r requirements.txt

     # Run on configured port

     - PORT=5001 uvicorn node_project.asgi:application --host 0.0.0.0 --port 5001 --reload

 # Node 2 (new terminal)

     - cd ../node_project

     - source node_project_env/bin/activate

     - PORT=5002 NODE_ID=node-2 IP=127.0.0.1 CMS_URL=http://localhost:4000 uvicorn node_project.asgi:application --host 0.0.0.0 --port 5002 --reload

     # Nodes auto-register with CMS on startup.


# 📘 API Summary
**CMS**
- `POST /api/nodes/register` → `{ nodeId, ip, port }`
- `POST /api/nodes/<nodeId>/disconnect`
- `GET /api/nodes`
- `POST /api/upload` (multipart `file`)
- `POST /api/events/upload-status` → `{ uploadId, nodeId, status, detail? }`


**Node App**
- `POST /upload` (multipart `file`, optional field `uploadId`)
- `GET /health`


# ✅ Notes
- **Channels** provides WebSocket updates to the dashboard.
- Uses **MYSQL** for simplicity; swap DB via Django settings.
- Node instances **self-register** using a background thread in `AgentConfig.ready()`.
- For containers/servers, set `IP` to an address reachable by the CMS.
- Replace in-memory channel layer with Redis in production.
