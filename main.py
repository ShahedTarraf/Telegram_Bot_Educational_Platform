"""FastAPI entrypoint for Vercel / generic deployments.
This file simply re-exports the admin dashboard FastAPI app
so that platforms looking for main.app can find it.
"""

from admin_dashboard.app import app  # noqa: F401
