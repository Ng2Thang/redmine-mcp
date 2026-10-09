"""Create one version, preserving validation errors and uncertain write outcomes."""

from http import HTTPMethod
from typing import Any

from fastapi import status as http_status
from pydantic import ValidationError

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text
from redmine_mcp.features.projects.models import (
    CreateProjectVersionRequest,
    CreateProjectVersionResult,
    ProjectVersionError,
    ProjectVersionObservation,
)
from redmine_mcp.integrations.redmine.client import RedmineClient
from redmine_mcp.integrations.redmine.responses import (
    resource_object,
    response_count,
    response_items,
)
from redmine_mcp.integrations.redmine.write import RedmineWriter, RedmineWriteRejected


def observe_version(value: dict[str, Any]) -> ProjectVersionObservation:
    try:
        return ProjectVersionObservation.model_validate(value, strict=True)
    except ValidationError:
        raise ApplicationError(
            codes_text.UPSTREAM_RESPONSE,
            redmine_text.UNEXPECTED_DATA,
            http_status.HTTP_502_BAD_GATEWAY,
        ) from None


class RedmineProjectVersions:
    def __init__(self, client: RedmineClient, writer: RedmineWriter) -> None:
        self.client = client
        self.writer = writer

    async def _existing_version(
        self, project_id: int, name: str
    ) -> ProjectVersionObservation | None:
        try:
            data = await self.client.get(f"projects/{project_id}/versions.json", {})
            values = response_items(data, "versions")
            if response_count(data) != len(values):
                return None
            # Validate the whole collection before treating any match as reliable.
            versions = [observe_version(value) for value in values]
            if len({version.id for version in versions}) != len(versions):
                return None
            matches = [
                version
                for version in versions
                if version.project.id == project_id and version.name == name
            ]
            return matches[0] if len(matches) == 1 else None
        except ApplicationError:
            return None

    async def create_project_version(
        self, project_id: int, request: CreateProjectVersionRequest
    ) -> CreateProjectVersionResult:
        expected = request.model_dump(mode="json", exclude_none=True)
        expected.update(status="open", sharing="none")
        try:
            receipt = await self.writer.write_json(
                HTTPMethod.POST,
                f"projects/{project_id}/versions.json",
                {"version": expected},
                accepted_statuses=(http_status.HTTP_201_CREATED,),
            )
        except RedmineWriteRejected as exc:
            if exc.upstream_status == http_status.HTTP_422_UNPROCESSABLE_CONTENT:
                existing = await self._existing_version(project_id, request.name)
                if existing is not None:
                    return CreateProjectVersionResult(
                        outcome="existing",
                        upstream_accepted=False,
                        resource_id=existing.id,
                        observed_version=existing,
                        error=ProjectVersionError(),
                    )
            raise

        result = CreateProjectVersionResult(
            outcome=receipt.outcome,
            upstream_accepted=True if receipt.status == http_status.HTTP_201_CREATED else None,
        )
        version = receipt.payload.get("version") if receipt.payload is not None else None
        version_id = version.get("id") if isinstance(version, dict) else None
        if type(version_id) is not int or version_id < 1:
            result.outcome = "uncertain"
            return result
        result.resource_id = version_id
        try:
            created = observe_version(resource_object(version, version_id))
        except ApplicationError:
            result.outcome = "uncertain"
            return result
        if created.project.id != project_id or receipt.status != http_status.HTTP_201_CREATED:
            result.outcome = "uncertain"
            return result
        try:
            data = await self.client.get(f"versions/{version_id}.json", {})
            actual = resource_object(data.get("version"), version_id)
            observed = observe_version(actual)
        except ApplicationError:
            return result
        result.observed_version = observed
        comparisons = [observed.project.id == project_id]
        comparisons.extend(
            actual[field] == value for field, value in expected.items() if field in actual
        )
        if not all(comparisons):
            result.verification = "mismatch"
        elif expected.keys() <= actual.keys():
            result.verification = "matched"
        return result
