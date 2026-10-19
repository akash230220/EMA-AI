"""Business logic service layer for the AI Email OS backend.

Each module in this package corresponds 1:1 to an endpoint module
(and ultimately to a frontend api/*.js file):

    auth_service.py       → endpoints/auth.py
    inbox_service.py      → endpoints/inbox.py
    email_service.py      → endpoints/emails.py
    reply_service.py      → endpoints/reply.py
    task_service.py       → endpoints/tasks.py
    meeting_service.py    → endpoints/meetings.py
    analytics_service.py  → endpoints/analytics.py
    automation_service.py → endpoints/automation.py
    copilot_service.py    → endpoints/copilot.py
    settings_service.py   → endpoints/settings.py

Services own all business logic; repositories own raw Mongo I/O;
endpoints own HTTP concern (request parsing, response shaping).
"""

