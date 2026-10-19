EMA AI is an AI-powered email productivity application. Its frontend provides tools for managing an inbox, generating email replies, tracking tasks and meetings, viewing analytics, configuring automation, and using an AI copilot. The backend exposes the API and integrates with MongoDB, Google services, Gemini, and ChromaDB.

## Repository layout

- [`frontend/`](./frontend/) — React and Vite single-page application
- [`backend/`](./backend/) — FastAPI service and Python tests

Each application has its own setup and run instructions:

- [Frontend setup and commands](./frontend/README.md)
- [Backend setup, configuration, and tests](./backend/README.md)

## Quick start

1. Set up and start the backend by following the [backend README](./backend/README.md). MongoDB must be available; configure Google OAuth and Gemini credentials for the integrations you plan to use.
2. Install frontend dependencies and start the Vite development server:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

3. Open the development URL printed by Vite (usually `http://localhost:5173`).

The frontend defaults to the backend API at `http://localhost:8000/api/v1`. To use another backend URL, set `VITE_API_BASE_URL` in `frontend/.env` before starting or building the frontend. See the [frontend README](./frontend/README.md) for details.

## Security

Do not commit `.env` files or place private credentials in frontend `VITE_` variables. Those variables are exposed in the built client application.
