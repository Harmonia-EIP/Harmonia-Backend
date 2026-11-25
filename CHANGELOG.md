CHANGELOG.md 📜 - 12/11/2026
All notable changes to the Harmonia backend will be documented in this file.

[1.4.0] - Security Hardening, Alembic and CI
Security
`JWT_SECRET` is now mandatory (32+ characters): the API refuses to start otherwise.
Disabled accounts can no longer use any endpoint (403), not only the AI routes.
Password change revokes every existing token (`users.token_version`); `PUT /profile/me/password` now returns `{"message", "token"}` (200) instead of 204.
Sign-in returns the same 401 whether the account exists or not, with the same bcrypt cost.
In-memory rate limiting (429 `RATE_LIMITED` + `Retry-After`) on sign-in (per IP and per account), sign-up, email/password changes and AI routes.
Test accounts (admin/root...) are only seeded with `SEED_TEST_USERS=1`.
AI network/response errors no longer leak internal details to clients.
Changed
Emails are stored lowercase; email and username uniqueness/sign-in are case-insensitive.
Sign-up validation aligned with profile update (lengths, username format, 72-byte password limit).
Role update validates the role code (422) and admins can no longer change their own role or active status.
Concurrent duplicate sign-ups/updates return 409 instead of 500.
Avatar errors use the standard `error_code` format (`INVALID_IMAGE`, `IMAGE_TOO_LARGE`, `UNSUPPORTED_IMAGE_FORMAT`).
Invalid `new_email` returns `INVALID_EMAIL` (400).
Prompt limited to 500 characters.
Shared auth dependency (`routes/dependencies.py`) with Swagger "Authorize" support.
`python-jose` replaced by `PyJWT`, `passlib` by `bcrypt` (existing hashes still valid).
Logging instead of prints, FastAPI lifespan, `/health` endpoint.
Fixed
`variation` is now forwarded to the AI service.
Expired tokens return `TOKEN_EXPIRED`.
Swagger favicon path.
Seed script now exits with an error code when it fails.
Infra / CI
Alembic migrations (`migrations/`, `migrate.py`), replacing `create_all` and one-off scripts.
Docker: slim image, non-root user, healthcheck, LF-only shell scripts.
CI: `ruff format` auto-applied and committed on the PR branch; dev -> main stays manual; deploy without downtime-inducing `down`, waits for health.

[1.3.0] - Generation History, User Profile and Avatar
Added
Generation history (merge of `prompt_historic`).
Update of user info and avatar (branch `update_info_user`).
Fixed
AI model now stored and returned correctly in the history.
Uploads folder made accessible from the main app.
Ruff lint and format errors.

[1.2.0] - AI v2 (CLAP), Models Endpoint and Color Preference
Added
Support for the `harmonia_v2` model, with preset variations forwarded to the AI service (PR #12, `feature/ai-v2-clap`).
Check of the available AI models, exposed through a models endpoint (branch `check_models`).
Color preference stored per user, with its migration (branch `color-preference`).
Fixed
Models endpoint.
Lint check on the migration file.
Deploy CI (several iterations).
POST request to the AI service.
Refine preset endpoint test.

[1.1.0] - Auto Lint, Auto Pull Request and Refine Endpoint
Added
CI/CD: automatic pull request creation, not targeting `dev`.
CI/CD: automatic lint and format, with auto-fix commits; lint errors no longer block the pipeline.
Test of the refine endpoint.
Changed
The model selected in the app is now forwarded to the AI backend.
Fixed
Timezone issue in the tests.
Lint indentation in the CI.
Unit tests and CI (several iterations).

[1.0.0] - First Release (v1)
Added
AI is called with a URL that depends on the selected model.
Fixed
Unit tests.

[0.0.6] - VPS Deployment, English Messages and License
Added
Deployment on the VPS with an endpoint test.
Docker deployment setup and VPS auto-deploy workflow.
Error messages switched to English.
MIT license.
Changed
Removed the duplicate deploy workflow.
Fixed
Signup crash: the roles table is now registered before the User mapper flush.
Connection to the AI API.
Test succeeding after the removal of an endpoint.
Unit tests and README.

[0.0.5] - Unit Tests CI, Diagrams and 20 Parameters
Added
Unit tests on routes and services.
CI/CD running the unit tests.
Diagram in the documentation.
Mirror of the repository for Epitech (CI fixes).
Changed
Backend now works with the 20 charter parameters.
Fixed
Bcrypt version.
Requirements for the CI (many iterations).

[0.0.4] - Documentation, Layout and Theme in Database
Added
Layout and theme stored and managed in the database.
Swagger home page, with comments in the code.
Icon and logo, theme fix.
Documentation diagram.
Algorithm and access token duration (hours) configurable through the environment.
Changed
Removed ReDoc.
Removed the useless role table.
Fixed
Link to the front-end documentation.
Requirements and README.

[0.0.3] - AI Route and Tests
Added
Route for the AI, and connection of the AI to the backend.
Unit tests (TU) and CI/CD running them.

[0.0.2] - Roles, Scripts and Mirror
Added
Role in the database and script to insert data.
Files moved into a `scripts` folder, with instructions to launch them.
Mirror push of the backend.
Fixed
README and file renaming.

[0.0.1] - Backend Structure and Authentication
Added
Backend structure.
Sign in and sign up.
Information of the currently connected user.
Exception handlers.
Removed
Token log.
Fixed
.gitignore.