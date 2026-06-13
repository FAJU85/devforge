#!/usr/bin/env python3
"""
Permission Check Middleware - Phase 7.2 RBAC

Validates user permissions before allowing access to protected endpoints.
"""

from fastapi import Request, HTTPException
from typing import Callable, Optional, Set
from functools import wraps
from uuid import UUID
import logging

from db.models_workspace_v1 import Workspace
from api.services.database_service import SessionLocal
from api.services.role_permission_service import RolePermissionService
from api.services.auth_service import get_current_user_from_request

logger = logging.getLogger(__name__)


def require_permission(permission_name: str):
    """
    Decorator to check if user has specific permission in workspace.

    Usage:
        @router.get("/admin-endpoint")
        @require_permission("workspace.admin")
        async def admin_endpoint(request: Request):
            ...

    Args:
        permission_name: Permission name to check (e.g., "workspace.create", "members.invite")
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                raise HTTPException(status_code=500, detail="Request not found in context")

            # Check workspace context is available
            if not hasattr(request.state, "workspace_id") or not request.state.workspace_id:
                raise HTTPException(status_code=400, detail="Workspace context not available")

            # Check authentication
            db = SessionLocal()
            try:
                user = await get_current_user_from_request(request, db)
                if not user:
                    raise HTTPException(status_code=401, detail="Not authenticated")

                workspace_id = request.state.workspace_id
                user_id = user.id

                # Check permission
                has_permission = RolePermissionService.check_permission(
                    db,
                    workspace_id,
                    user_id,
                    permission_name
                )

                if not has_permission:
                    logger.warning(
                        f"Permission denied: user {user_id} tried to access {permission_name} "
                        f"in workspace {workspace_id}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission denied: {permission_name}"
                    )

                # Inject permissions into request state for use in handler
                request.state.user_permissions = RolePermissionService.get_user_permissions(
                    db, workspace_id, user_id
                )
                request.state.user_role = RolePermissionService.get_user_role(
                    db, workspace_id, user_id
                )

            finally:
                db.close()

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_workspace_admin(func: Callable):
    """
    Decorator to check if user is workspace admin (owner or admin role).

    Usage:
        @router.post("/manage-members")
        @require_workspace_admin
        async def manage_members(request: Request):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if not request:
            raise HTTPException(status_code=500, detail="Request not found in context")

        # Check workspace context
        if not hasattr(request.state, "workspace_id") or not request.state.workspace_id:
            raise HTTPException(status_code=400, detail="Workspace context not available")

        # Check authentication
        db = SessionLocal()
        try:
            user = await get_current_user_from_request(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            workspace_id = request.state.workspace_id

            # Check if admin
            is_admin = RolePermissionService.is_admin(db, workspace_id, user.id)

            if not is_admin:
                logger.warning(
                    f"Admin access denied: user {user.id} is not admin "
                    f"in workspace {workspace_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Workspace admin access required"
                )

            # Inject role info
            request.state.user_role = RolePermissionService.get_user_role(
                db, workspace_id, user.id
            )

        finally:
            db.close()

        return await func(*args, **kwargs)

    return wrapper


def require_workspace_owner(func: Callable):
    """
    Decorator to check if user is workspace owner.

    Usage:
        @router.delete("/workspace")
        @require_workspace_owner
        async def delete_workspace(request: Request):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if not request:
            raise HTTPException(status_code=500, detail="Request not found in context")

        # Check workspace context
        if not hasattr(request.state, "workspace_id") or not request.state.workspace_id:
            raise HTTPException(status_code=400, detail="Workspace context not available")

        # Check authentication
        db = SessionLocal()
        try:
            user = await get_current_user_from_request(request, db)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            workspace_id = request.state.workspace_id

            # Check if owner
            is_owner = RolePermissionService.is_owner(db, workspace_id, user.id)

            if not is_owner:
                logger.warning(
                    f"Owner access denied: user {user.id} is not owner "
                    f"of workspace {workspace_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Workspace owner access required"
                )

        finally:
            db.close()

        return await func(*args, **kwargs)

    return wrapper


class PermissionCheckMiddleware:
    """
    Middleware base class for permission checking.

    Can be subclassed to implement custom permission logic.
    """

    def __init__(self):
        self.db = SessionLocal()

    async def check_permission(
        self,
        workspace_id: UUID,
        user_id: UUID,
        permission_name: str
    ) -> bool:
        """Check if user has permission."""
        return RolePermissionService.check_permission(
            self.db,
            workspace_id,
            user_id,
            permission_name
        )

    async def get_user_permissions(
        self,
        workspace_id: UUID,
        user_id: UUID
    ) -> Set[str]:
        """Get all permissions for user."""
        return RolePermissionService.get_user_permissions(
            self.db,
            workspace_id,
            user_id
        )

    async def is_admin(
        self,
        workspace_id: UUID,
        user_id: UUID
    ) -> bool:
        """Check if user is admin."""
        return RolePermissionService.is_admin(
            self.db,
            workspace_id,
            user_id
        )

    async def is_owner(
        self,
        workspace_id: UUID,
        user_id: UUID
    ) -> bool:
        """Check if user is owner."""
        return RolePermissionService.is_owner(
            self.db,
            workspace_id,
            user_id
        )

    def __del__(self):
        """Cleanup database session."""
        if self.db:
            self.db.close()
