## Pulsse Authentication Service — Project Workflow

### Overview
This service is a Django REST Framework (DRF) application that manages authentication, organizations, roles/permissions, and a small dashboard. It exposes versioned APIs under `api/v1`, uses JWT for stateless auth, and standardizes responses.

- Base app: `authentication`
- Organization management: `organization`
- Roles & permissions: `role`
- Dashboard metrics: `dashboard`
- Shared utilities: `utils`
- API docs: `drf-spectacular` at `/api-docs/`

### Request lifecycle
1. Client sends HTTP request to `config.urls` (versioned with `api/v1`).
2. URL dispatcher includes app routes (e.g., `authentication.urls`, `organization.urls`, `role.urls`, `dashboard.urls`).
3. DRF view/viewset handles the request, often using serializers and models.
4. Authentication: `JWTAuthentication` (with extremely long lifetimes configured) and `TokenAuthentication` are enabled. Default permission is `AllowAny` unless overridden per view.
5. Middleware (notably `utils.middleware.ModifyHTMLMiddleware`) runs on the response.
6. Responses are standardized via helpers in `utils.custom_response`.

### Authentication flow
- Login endpoint (`authentication.views.LoginView.login`):
  - Accepts `identifier` (email or username) and `password` (see `LoginRequestSerializer`).
  - Resolves user by email or username and authenticates via `django.contrib.auth.authenticate`.
  - Validates the user’s organization status (if linked via `Profile`).
  - Issues JWT using `rest_framework_simplejwt.RefreshToken.for_user(user)` and returns both access and refresh tokens.
  - Ensures any open `LoginHistory` is closed, creates a new `LoginHistory` entry.
  - Response uses `utils.custom_response.True_Response_200` with tokens, `user_id`, `is_superuser`, `role`, and `organization`.

- JWT configuration (`config.settings.SIMPLE_JWT`):
  - `AUTH_HEADER_TYPES=('Bearer',)`
  - Access/refresh token lifetimes set to 100 years (intended for development; revisit for production).
  - Refresh rotation enabled with blacklist after rotation.

- User model (`authentication.models.User`):
  - Extends `AbstractUser` and `utils.models.BaseModel`.
  - Enforces unique `email`, `username`, and optional unique `contact`.
  - Links optionally to a `role.Role` via `role` FK.
  - Passwords are validated and hashed on save.

- Profile and Login History:
  - `Profile` links `User` to an `Organization` for tenant context.
  - `LoginHistory` records session events; prior open session is closed on new login.

### Roles and permissions
- Models (`role.models`):
  - `Permission` with `name`, `codename`, and `model`.
  - `Role` with `name`, `organization` (nullable for global roles), `status`, and M2M `permissions`.

- Enforcement (`utils.permissions`):
  - `IsSuperUser` permission class for superuser-only access.
  - `check_permission(required_permission)` decorator checks the requesting user’s role permissions by `codename`; superusers bypass checks.
  - Predefined permission sets for organization defaults: `HOST_PERMISSIONS` and `NON_HOST_PERMISSIONS`.

- Provisioning:
  - `organization.signals.create_default_roles` creates “Host” and “Non Host” roles for each new `Organization`, assigning subsets of permissions based on `HOST_PERMISSIONS` and `NON_HOST_PERMISSIONS`.
  - Management commands in `role/management/commands/`:
    - `sync_permissions.py`: syncs permission definitions (backed by `permissions.json`).
    - `sync_roles.py`: can seed/sync roles.

### Organizations
- Model (`organization.models.Organization`):
  - One-to-one with `authentication.User` (owner/admin), status flag, network credentials (IP, SSH key), optional `api_key`/`secret_key`.

- Signals (`organization.signals`):
  - On create: creates Host/Non Host roles and assigns permissions.
  - On create/update of `api_key`/`secret_key`: invokes `utils.http_service.update_ezviz_config` to update external ML/vision configuration.

- Views (`organization.views.OrganizationView`):
  - CRUD-style operations with dynamic filtering, pagination, and optional organization scoping.
  - Integrates microservice calls for subscription checks through `utils.microservices.subscriptions.get_active_subscriptions`.

### Dashboard
- Views in `dashboard.views` expose aggregated stats for active users, role distribution, signups, etc.
- Helpers in `dashboard.helpers` support dynamic date-ranged queries and optional organization filters.

### Utilities
- `utils.custom_response`: Standard response helpers
  - `True_Response_200`, `Created_Response_201`, `Exception_Response_400`, etc. Responses include a consistent shape with `status`, `message`, and `results`.
- `utils.custom_pagination.CustomPageNumberPagination`: DRF pagination with consistent metadata.
- `utils.helpers`:
  - `generate_unique_token`, `dynamic_filter`, `send_email`.
- `utils.http_service`: Simple HTTP client for external service calls plus `update_ezviz_config` integration.
- `utils.permissions`: Permission sets and decorators.
- `utils.middleware.ModifyHTMLMiddleware`: Post-processing of HTML responses.

### URL map (high level)
- `config/urls.py` (versioned under `api/v1`):
  - `/auth/` → `authentication.urls`
  - `/login-history` → `authentication.login_history_urls`
  - `/roles` → `role.urls`
  - `/organizations/external` → `organization.external_apis_urls`
  - `/organizations` → `organization.urls`
  - `/dashboard/` → `dashboard.urls`
  - `/api-docs/` and `/schema` via drf-spectacular
  - `/health` → health check view

### Response conventions
- Success envelope:
  - `{ "status": true, "message": str, "results": any }`
- Errors via `Exception_Response_400` or `Except_Exception_Response_400` return consistent shapes and appropriate HTTP codes.

### Developer workflows
- Sync permissions from `permissions.json`:
  - `python manage.py sync_permissions`
- Sync/seed roles:
  - `python manage.py sync_roles`
- Create a superuser (custom command may exist):
  - `python manage.py mysuperuser`
- Data maintenance:
  - `python manage.py hard_delete_old_data`

### Security & production notes
- JWT lifetimes are set to 100 years in settings; reduce significantly for production.
- Ensure HTTPS termination and secure CORS in production (currently `CORS_ALLOW_ALL_ORIGINS=True`).
- Validate and rotate organization `api_key`/`secret_key`; monitor external config update outcomes.

### How things fit together
- Users authenticate via `/api/v1/auth/...` and receive JWTs. The `Profile` ties a user to an `Organization` (which controls availability and scope). Roles and permissions restrict access to endpoints or actions via decorators/permission classes. Organization creation triggers default role provisioning and external service configuration. The dashboard aggregates data across these domains with optional org scoping.

