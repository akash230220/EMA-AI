# backend/app/api/v1/router.py
"""
Aggregates every endpoint router into a single APIRouter, mounted by
main.py at the /api/v1 prefix. Each sub-router corresponds 1:1 to a
frontend api/*.js file:

    auth.py         <-> frontend/src/api/authApi.js
    inbox.py        <-> frontend/src/api/emailApi.js (sync methods)
    emails.py       <-> frontend/src/api/emailApi.js (CRUD/AI methods)
    reply.py        <-> frontend/src/api/emailApi.js (reply methods)
    tasks.py        <-> frontend/src/api/taskApi.js
    meetings.py     <-> frontend/src/api/meetingApi.js
    analytics.py    <-> frontend/src/api/analyticsApi.js
    automation.py   <-> frontend/src/api/automationApi.js
    copilot.py      <-> frontend/src/api/copilotApi.js
    settings.py     <-> frontend/src/pages/SettingsPage.jsx's direct
                        axiosClient calls to /settings/*

This file only wires prefixes/tags — no business logic lives here;
each endpoints/*.py module owns its own routes and delegates to the
corresponding services/*.py module.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    inbox,
    emails,
    reply,
    tasks,
    meetings,
    analytics,
    automation,
    copilot,
    settings as settings_endpoints,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(reply.router, prefix="/emails", tags=["reply"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
api_router.include_router(settings_endpoints.router, prefix="/settings", tags=["settings"])