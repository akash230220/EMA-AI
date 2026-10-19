# backend/app/api/v1/endpoints/settings.py
"""
User settings: profile, integrations, notifications, AI preferences,
security/sessions, and destructive account actions. Maps to the
direct axiosClient calls made in frontend/src/pages/SettingsPage.jsx
(no dedicated settingsApi.js exists yet on the frontend — this is the
matching backend surface for those /settings/* calls).
"""

from fastapi import APIRouter, Depends

from app.schemas.settings_schema import (
    SettingsResponse,
    ProfileUpdateRequest,
    NotificationPreferencesUpdateRequest,
    AiPreferencesUpdateRequest,
)
from app.services.settings_service import (
    get_user_settings,
    update_profile,
    update_notification_preferences,
    update_ai_preferences,
    disconnect_google_integration,
    revoke_session,
    revoke_all_sessions,
    clear_ai_data,
    delete_account,
)
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings_route(current_user=Depends(get_current_user)):
    """
    Returns the full settings bundle: profile, gmailStatus,
    calendarStatus, notificationPreferences, aiPreferences, sessions —
    matches what SettingsPage.jsx destructures from a single GET.
    """
    return await get_user_settings(user_id=current_user.id)


@router.patch("/profile")
async def update_profile_route(payload: ProfileUpdateRequest, current_user=Depends(get_current_user)):
    return await update_profile(user_id=current_user.id, name=payload.name, timezone=payload.timezone)


@router.patch("/notifications")
async def update_notifications_route(
    payload: NotificationPreferencesUpdateRequest, current_user=Depends(get_current_user)
):
    return await update_notification_preferences(user_id=current_user.id, preferences=payload)


@router.patch("/ai-preferences")
async def update_ai_preferences_route(payload: AiPreferencesUpdateRequest, current_user=Depends(get_current_user)):
    return await update_ai_preferences(user_id=current_user.id, preferences=payload)


@router.post("/integrations/disconnect")
async def disconnect_integration(current_user=Depends(get_current_user)):
    """Revokes the Google OAuth grant and clears stored tokens for Gmail/Calendar."""
    await disconnect_google_integration(user_id=current_user.id)
    return {"detail": "Google account disconnected."}


@router.delete("/sessions/{session_id}")
async def revoke_session_route(session_id: str, current_user=Depends(get_current_user)):
    await revoke_session(user_id=current_user.id, session_id=session_id)
    return {"detail": "Session revoked."}


@router.post("/sessions/revoke-all")
async def revoke_all_sessions_route(current_user=Depends(get_current_user)):
    await revoke_all_sessions(user_id=current_user.id)
    return {"detail": "All sessions revoked."}


@router.post("/clear-ai-data")
async def clear_ai_data_route(current_user=Depends(get_current_user)):
    """Removes all AI summaries/categorizations/embeddings; emails re-processed on next sync."""
    await clear_ai_data(user_id=current_user.id)
    return {"detail": "AI data cleared."}


@router.delete("/account")
async def delete_account_route(current_user=Depends(get_current_user)):
    """Permanently deletes the user's account and all associated data."""
    await delete_account(user_id=current_user.id)
    return {"detail": "Account deleted."}