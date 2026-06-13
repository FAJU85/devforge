#!/usr/bin/env python3
"""
Workspace Context Middleware - Phase 7.2 RBAC

Injects workspace context into all requests and validates user membership.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from uuid import UUID
import logging
from typing import Optional

from db.models_workspace_v1 import Workspace
from db.models_v2 import User
from api.services.database_service import SessionLocal
from api.services.workspace_service import WorkspaceService
from api.services.auth_service import get_current_user_from_request

logger = logging.getLogger(__name__)


class WorkspaceContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject workspace context into all requests.

    Extracts workspace_id from:
    1. Path parameter: /api/workspaces/{workspace_id}/...
    2. Query parameter: ?workspace_id=...
    3. Header: X-Workspace-ID
    4. User's default workspace (if no explicit workspace specified)

    Validates that user is a member of the workspace and injects into request.state.
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and inject workspace context."""
        db = SessionLocal()

        try:
            # Extract workspace ID from various sources
            workspace_id = self._extract_workspace_id(request)

            # Skip workspace validation for auth and health endpoints
            if self._should_skip_workspace_validation(request.url.path):
                request.state.workspace = None
                request.state.workspace_id = None
                return await call_next(request)

            # If workspace_id required but not provided, try to get user's default
            if not workspace_id:
                user = await get_current_user_from_request(request, db)
                if user and user.default_workspace_id:
                    workspace_id = user.default_workspace_id
                else:
                    # No workspace context - this is OK for multi-workspace endpoints
                    request.state.workspace = None
                    request.state.workspace_id = None
                    return await call_next(request)

            # Validate workspace exists and is not deleted
            workspace = WorkspaceService.get_workspace(db, workspace_id)
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")

            # Validate user is member of workspace
            user = await get_current_user_from_request(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            is_member = WorkspaceService.is_member(db, workspace_id, user.id)
            is_owner = WorkspaceService.is_owner(db, workspace_id, user.id)

            if not (is_member or is_owner):
                raise HTTPException(
                    status_code=403,
                    detail="Not a member of this workspace"
                )

            # Inject workspace context into request state
            request.state.workspace = workspace
            request.state.workspace_id = workspace_id
            request.state.user_id = user.id

            logger.debug(f"Workspace context injected: {workspace_id} for user {user.id}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in workspace context middleware: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            db.close()

        return await call_next(request)

    @staticmethod
    def _extract_workspace_id(request: Request) -> Optional[UUID]:
        """
        Extract workspace ID from request.

        Args:
            request: HTTP request

        Returns:
            Workspace ID or None
        """
        # 1. Try path parameter (most specific)
        try:
            # Check if {workspace_id} is in path
            if "{workspace_id}" in str(request.url):
                # This is a path parameter, will be in request.path_params
                pass

            # Extract from actual path if present
            path_parts = request.url.path.split("/")
            if len(path_parts) > 3 and path_parts[2] == "workspaces":
                try:
                    return UUID(path_parts[3])
                except (ValueError, IndexError):
                    pass
        except Exception:
            pass

        # 2. Try query parameter
        try:
            workspace_id = request.query_params.get("workspace_id")
            if workspace_id:
                return UUID(workspace_id)
        except (ValueError, TypeError):
            pass

        # 3. Try header
        try:
            workspace_id = request.headers.get("X-Workspace-ID")
            if workspace_id:
                return UUID(workspace_id)
        except (ValueError, TypeError):
            pass

        return None

    @staticmethod
    def _should_skip_workspace_validation(path: str) -> bool:
        """
        Check if this path should skip workspace validation.

        Args:
            path: Request path

        Returns:
            True if should skip validation
        """
        skip_paths = [
            "/api/auth",
            "/api/health",
            "/health",
            "/metrics",
            "/ws",
            "/api/invitations/accept",  # Can accept invitation without workspace context
            "/static",
        ]

        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True

        return False


class WorkspaceContextMiddlewareV2(BaseHTTPMiddleware):
    """
    Alternative workspace context middleware that doesn't require authentication.

    Used for routes that handle invitations and other guest actions.
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and inject workspace context without auth."""
        db = SessionLocal()

        try:
            # Extract workspace ID
            workspace_id = WorkspaceContextMiddleware._extract_workspace_id(request)

            if workspace_id:
                workspace = WorkspaceService.get_workspace(db, workspace_id)
                if workspace:
                    request.state.workspace = workspace
                    request.state.workspace_id = workspace_id
                    logger.debug(f"Workspace context injected (no-auth): {workspace_id}")

        except Exception as e:
            logger.error(f"Error in workspace context middleware (v2): {e}")
        finally:
            db.close()

        return await call_next(request)
