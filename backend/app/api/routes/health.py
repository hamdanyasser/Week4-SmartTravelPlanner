"""Health check endpoint.

Used by Docker, load balancers, and humans to confirm the process is
alive. Deliberately does not touch the database — its job is to say
"the web layer is up", not "everything downstream works".
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
