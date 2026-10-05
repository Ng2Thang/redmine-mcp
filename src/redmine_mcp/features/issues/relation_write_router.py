from typing import Annotated

from fastapi import APIRouter, Depends, Path

from redmine_mcp.api import get_issues, require_write_access
from redmine_mcp.features.issues.service import IssueService
from redmine_mcp.features.issues.write_models import IssueRelationDeleteResult

router = APIRouter(
    prefix="/api/v1/relations", tags=["issues"], dependencies=[Depends(require_write_access)]
)


@router.delete(
    "/{relation_id}",
    operation_id="delete_issue_relation",
    response_model=IssueRelationDeleteResult,
    description=(
        "Delete one visible relation after resolving its endpoints and checking both issue "
        "contexts. Requires the restricted writer and Manage issue relations on either "
        "endpoint's project. Native removal journals both issues and does not restore dates. "
        "Reports acceptance separately from visible absence in both issue contexts; "
        "inaccessible contexts cannot prove deletion. Reconcile uncertain writes before retrying."
    ),
)
async def delete_issue_relation(
    service: Annotated[IssueService, Depends(get_issues)],
    relation_id: Annotated[int, Path(ge=1, description="ID of the relation to delete")],
) -> IssueRelationDeleteResult:
    return await service.delete_issue_relation(relation_id)
