from typing import Annotated

from fastapi import APIRouter, Depends

from redmine_mcp.api import get_auth_context, get_users, require_read_access
from redmine_mcp.auth import AuthContext
from redmine_mcp.features import UserService
from redmine_mcp.features.users.models import CurrentUser

router = APIRouter(
    prefix="/api/v1/users", tags=["users"], dependencies=[Depends(require_read_access)]
)


@router.get(
    "/current",
    operation_id="get_current_user",
    response_model=CurrentUser,
    description=(
        "Identify the Redmine user associated with the requesting API key. "
        "Returns ID, login, first and last name, nullable email, and visible project "
        "memberships with roles and inherited flags. Takes no arguments and always "
        "requests memberships. Memberships follow Redmine project visibility; they "
        "are not a complete list of accessible projects or effective permissions. "
        "An omitted email is null with a visibility observation. Credentials and "
        "additional account metadata are excluded."
    ),
)
async def get_current_user(
    service: Annotated[UserService, Depends(get_users)],
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> CurrentUser:
    """Read the requesting user's basic profile and visible memberships."""
    return await service.get_current_user(context.principal.redmine_user_id)
