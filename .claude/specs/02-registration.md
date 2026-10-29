# Spec: Registration

## Overview
Turn the static `/register` page into a working sign-up flow. A visitor submits their name, email and password; the app validates the input, hashes the password with werkzeug, inserts a row into the existing `users` table and redirects them to the login page. This is Step 02 of the Spendly roadmap and the first feature that writes user data. Login/logout (Step 3) and everything behind it need real accounts to exist. Sessions are out of scope, so registration does not log the user in.

## Depends on
- Step 01 — Database Setup (`users` table, `get_db()`, `init_db()`, `seed_db()`)

## Routes
- GET /register — render the registration form (route exists, behaviour unchanged) — public
- POST /register — validate the form, create the user, redirect to `/login` on success; re-render `register.html` with an error message and HTTP 400 on failure — public

The existing `@app.route("/register")` must be changed to `methods=["GET", "POST"]`. No other routes are added.

## Database changes
No database changes. The `users` table in `database/db.py` already has `id`, `name`, `email` (UNIQUE, NOT NULL), `password_hash` and `created_at`.

One new helper is added to `database/db.py` (no schema change):
- `create_user(name, email, password)` — hashes the password with `generate_password_hash`, inserts the row with a parameterised query, commits, closes the connection and returns the new user id. `sqlite3.IntegrityError` from the UNIQUE constraint is allowed to propagate so the route can handle it.

## Templates
- Create: none
- Modify:
  - `templates/register.html` — on error, re-fill `name` and `email` from the submitted values (`value="{{ name or '' }}"`); never re-fill the password. The existing `auth-error` block is reused for messages.

## Files to change
- `app.py` — import `request`, `redirect`, `url_for` and `sqlite3`; import `create_user`; make `/register` handle GET and POST with validation
- `database/db.py` — add `create_user()`
- `templates/register.html` — re-fill name and email on error

## Files to create
- `tests/test_registration.py` — pytest tests for the registration route (pytest and pytest-flask are already in `requirements.txt`)

## New dependencies
No new dependencies.

## Validation rules
Applied server-side in the POST handler in this order. The first failure re-renders the form with HTTP 400:
1. `name` and `email` are stripped; `name`, `email` and `password` must all be non-empty — "All fields are required."
2. `email` is lower-cased, then must contain `@` with text before it and a `.` after it — "Enter a valid email address."
3. `password` must be at least 8 characters (not stripped) — "Password must be at least 8 characters."
4. `email` must not already exist, detected by catching `sqlite3.IntegrityError` from the UNIQUE constraint rather than a separate SELECT — "An account with this email already exists."

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never build SQL with string formatting or f-strings
- Passwords hashed with werkzeug (`generate_password_hash`); never store or log the plain password
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Close DB connections in `try/finally`, matching `database/db.py`
- Redirect with `redirect(url_for("login"))` after a successful POST (Post/Redirect/Get)
- Do not add sessions, `secret_key` or auto-login — that belongs to Step 3
- Show only the error messages listed above; never echo exception text to the user
- Tests must use a temporary database (monkeypatch `DB_PATH`) and never touch `spendly.db`

## Definition of done
- [ ] `GET /register` renders the form with HTTP 200
- [ ] Valid name, email and password creates a row in `users` and redirects (302) to `/login`
- [ ] The stored `password_hash` differs from the submitted password and passes `check_password_hash`
- [ ] Email is stored lower-cased and trimmed (` Test@Example.COM ` is stored as `test@example.com`)
- [ ] Registering `demo@spendly.com` (the seeded user) shows "An account with this email already exists." and creates no second row
- [ ] Registering an existing email in different casing is rejected as a duplicate
- [ ] A password shorter than 8 characters shows the length error and creates no row
- [ ] An empty name, email or password shows "All fields are required." and creates no row
- [ ] An invalid email such as `abc` shows "Enter a valid email address." and creates no row
- [ ] On any error the form reappears with name and email pre-filled and the password field empty
- [ ] Error responses return HTTP 400
- [ ] An email like `'; DROP TABLE users;--` does not alter the database
- [ ] `pytest tests/test_registration.py` passes
- [ ] The app starts without errors and the "Sign in" link on the register page still works
