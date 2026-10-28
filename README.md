# AI Career Copilot

A Flask-based career preparation app with user authentication, admin approval, and SQLite.

## Tech Stack

- **Python** 3.8+
- **Flask** – web framework
- **SQLite** – database
- **Werkzeug** – password hashing

## Project Structure

```
ai-career-copilot/
├── app.py              # Flask app, routes, auth
├── database.db         # SQLite DB (created on first run)
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── chat.html
│   ├── skillgap.html
│   ├── admin.html
│   └── ... (other pages)
└── static/
    ├── css/style.css
    └── js/script.js
```

## Setup

1. **Create virtual environment** (optional):

   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows
   # source venv/bin/activate   # macOS/Linux
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:

   ```bash
   python app.py
   ```

4. Open **http://127.0.0.1:10000** in your browser.

> **Note:** If you had an older version with `database.db`, delete it and restart so the new `users` and `chat_history` tables are created correctly.

## Default Admin Account

- **Email:** `admin@copilot.com`
- **Password:** `admin123`
- **Role:** admin
- **Approved:** 1 (always approved)

## Routes

| Route | Description | Auth |
|-------|-------------|------|
| `/` | Landing (login/signup) | Public |
| `/signup` | POST – register | Public |
| `/login` | POST – login | Public |
| `/logout` | Logout | Any |
| `/dashboard` | Dashboard | Login |
| `/chat` | Chat copilot | Login |
| `/admin` | Admin panel | Admin |
| `/approve-user/<id>` | POST – approve user | Admin |
| `/reject-user/<id>` | POST – reject user | Admin |

## Database (SQLite)

### users

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Full name |
| email | TEXT | Unique, used for login |
| password | TEXT | Hashed (pbkdf2:sha256) |
| role | TEXT | `admin` or `student` |
| approved | INTEGER | 0 = pending, 1 = approved |

### chat_history

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | FK to users |
| message | TEXT | User message |
| response | TEXT | AI/demo response |
| timestamp | TEXT | When sent |

---

## How to Test the Admin Approval System

### Step 1: Start the server

```bash
cd ai-career-copilot
python app.py
```

Open http://127.0.0.1:10000 in your browser.

### Step 2: Sign up as a new student

1. On the landing page, click the **Sign up** tab.
2. Enter:
   - **Name:** Test Student
   - **Email:** student@test.com
   - **Password:** test123
3. Click **Sign up**.
4. You should see: *"Account created. Wait for admin approval before logging in."*

### Step 3: Try logging in (should fail)

1. Switch to the **Sign in** tab.
2. Enter:
   - **Email:** student@test.com
   - **Password:** test123
3. Click **Login**.
4. You should see: *"Your account is waiting for admin approval."*
5. You stay on the login page.

### Step 4: Log in as admin

1. On the **Sign in** tab, enter:
   - **Email:** admin@copilot.com
   - **Password:** admin123
2. Click **Login**.
3. You should be redirected to the **Admin** page.

### Step 5: Approve the pending user

1. On the Admin page, find the **Pending user approvals** table.
2. You should see **Test Student** (student@test.com).
3. Click the **Approve** button next to that user.
4. You should see *"User approved."* and the user moves to **Approved users**.

### Step 6: Log in as the approved student

1. Click **Logout** in the sidebar (or open http://127.0.0.1:10000 in a new incognito/private window).
2. Sign in with:
   - **Email:** student@test.com
   - **Password:** test123
3. You should be redirected to the **Dashboard**.

### Step 7: Test reject (optional)

1. Sign up another user (e.g. reject@test.com).
2. Log in as admin (admin@copilot.com).
3. In **Pending user approvals**, click **Reject** next to that user.
4. Confirm the dialog.
5. The user is removed and cannot log in.
