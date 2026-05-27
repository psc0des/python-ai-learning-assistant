# SQL, HTTP, Git, and Linux Basics

Every software developer — regardless of specialisation — works with four fundamental tools daily: HTTP (how web requests and responses work), SQL (how to query and update database data), Git (how to track and share code changes), and the Linux command line (how to inspect what is happening on a running server).

Think of a production issue as a crime scene that spans four rooms. The HTTP room shows you what request came in and what response went out. The SQL room shows you the state of the data. The Git room shows you what changed in the code recently. The Linux room shows you what is running and what the logs say. Strong engineers look in all four rooms — weak engineers look only in one and guess about the others.

## 1. HTTP — How Web Requests Work

Every time your browser loads a page, or your code calls an API, it sends an HTTP request and receives an HTTP response. Understanding the structure of these messages is fundamental to building and debugging web applications.

**An HTTP request has:**
- **Method** — what you want to do (GET, POST, PUT, DELETE)
- **URL** — which resource you are acting on
- **Headers** — metadata (authentication, content type, etc.)
- **Body** — data you are sending (for POST/PUT)

**An HTTP response has:**
- **Status code** — whether it worked (and if not, what kind of failure)
- **Headers** — response metadata
- **Body** — the data you requested (usually JSON)

**The most important status codes:**

```
200 OK              — success, data returned
201 Created         — new resource created
204 No Content      — success, nothing to return
400 Bad Request     — your request is malformed
401 Unauthorized    — not logged in / bad credentials
403 Forbidden       — logged in, but not allowed
404 Not Found       — resource does not exist
422 Unprocessable   — valid request, but invalid data
500 Internal Error  — the server broke
502 Bad Gateway     — server received a bad response upstream
503 Service Unavail — server is down or overloaded
```

**Common confusion:** `401` vs `403`. A `401` means 'I don't know who you are — authenticate first.' A `403` means 'I know who you are, but you are not allowed to do this.' These have different fixes: 401 → check your credentials; 403 → check your permissions.

## 2. SQL — Querying and Inspecting Data

SQL (Structured Query Language) is how you talk to relational databases. Even if you use an ORM (like SQLAlchemy) in your Python code, understanding raw SQL lets you inspect the database directly during debugging — which is often the fastest way to verify what is actually stored.

**The essential SQL commands:**

```sql
-- Read data
SELECT id, name, email FROM users
WHERE active = true
ORDER BY created_at DESC
LIMIT 10;

-- Count records
SELECT COUNT(*) FROM orders WHERE status = 'pending';

-- Filter by multiple conditions
SELECT * FROM orders
WHERE user_id = 42
  AND created_at > '2024-01-01'
  AND total > 100.00;

-- Find recently created records
SELECT * FROM events
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

**Updating data safely — always check first:**

```sql
-- STEP 1: SELECT to verify you are targeting the right rows
SELECT id, email, status FROM users WHERE id = 42;
-- STEP 2: Only then UPDATE with the same filter
UPDATE users SET status = 'inactive' WHERE id = 42;

-- NEVER do this by accident:
UPDATE users SET status = 'inactive';  -- NO WHERE clause → updates EVERY user!
-- Always add WHERE. Use LIMIT in SELECT queries to be sure of scope.
```

**Production safety rule:** before any `UPDATE` or `DELETE`, run the equivalent `SELECT` with the same `WHERE` clause to see exactly which rows will be affected. Only then run the write query.

## 3. Git — Tracking and Sharing Code Changes

Git is a version control system — it records every change to your code, who made it, and when. This lets you collaborate with teammates, roll back mistakes, and understand why code behaves the way it does by looking at its history.

**The everyday Git workflow:**

```bash
# See what you have changed:
git status              # list modified files
git diff                # show exact line-by-line changes
git diff HEAD~1         # compare to previous commit

# Save your changes:
git add app.py tests/test_app.py    # stage specific files (not 'git add .')
git commit -m 'Fix: validate email before saving to database'

# Sync with your team:
git pull                # get latest changes from the shared repo
git push                # share your commits

# Look at history:
git log --oneline -10   # last 10 commits, one line each
git log --follow app.py # history of changes to one file
```

**What makes a good commit message:**

```bash
# BAD — tells you nothing:
git commit -m 'fix'
git commit -m 'changes'
git commit -m 'wip'

# GOOD — explains what changed and why:
git commit -m 'Fix: handle None email in registration to prevent 500'
git commit -m 'Add: rate limiting to /api/run endpoint (15 req/min)'
git commit -m 'Refactor: extract validate_config into its own function'
```

Good commit messages are time travel — they let future-you (or your teammate) understand why a change was made without having to read all the code.

## 4. Linux Command Line — Inspecting Running Systems

When something goes wrong on a server, you need to look around. The Linux command line is how you do that — inspecting files, reading logs, checking what processes are running, and understanding the current state of the machine.

**Essential commands to know:**

```bash
# Navigation:
pwd              # where am I? (print working directory)
ls -la           # list files with details and hidden files
cd /var/log      # change directory

# Reading files:
cat config.json                   # print entire file
head -20 app.log                  # first 20 lines
tail -50 app.log                  # last 50 lines
tail -f app.log                   # follow live updates (useful for watching logs)

# Searching:
grep 'ERROR' app.log              # find lines containing 'ERROR'
grep -r 'api_key' ./config/       # search recursively in a directory
grep -c 'WARN' app.log            # count matching lines

# Processes:
ps aux | grep python              # find Python processes
kill -9 <pid>                     # force-stop a process by its PID

# Environment:
echo $PATH                        # see your executable search path
env | grep API                    # see env variables containing 'API'
```

**Critical habit: always check `pwd` first.** Many production mistakes happen because someone ran a command in the wrong directory. Know where you are before you act.

## 5. Cross-Layer Debugging — Tracing an Issue End to End

The real value of knowing HTTP, SQL, Git, and Linux together is being able to follow an issue through all layers instead of stopping when one layer looks fine.

**Example scenario:** users are reporting that creating an order returns a `500` error.

```bash
# LAYER 1 — HTTP: reproduce and capture the exact request/response
curl -X POST http://api.example.com/orders \
     -H 'Content-Type: application/json' \
     -d '{"product_id": 42, "quantity": 2}'
# Response: 500 Internal Server Error
# This tells you the server crashed, not a client input problem

# LAYER 2 — Linux: read the server logs to find the actual error
tail -100 /var/log/app/error.log | grep 'order'
# Found: "IntegrityError: column 'discount_code_id' cannot be null"
# Now you know the exact error
```

```sql
-- LAYER 3 — SQL: inspect the database schema and recent data
-- Check what the column constraint actually is:
\d orders
-- Check recent failed orders:
SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '1 hour'
  AND status = 'failed';
```

```bash
# LAYER 4 — Git: find what changed recently
git log --oneline -10   # look for recent changes to order logic
git show abc1234        # inspect the commit that touched orders
git diff HEAD~3 -- orders.py  # what changed in orders.py in last 3 commits
# Found: migration added NOT NULL constraint on discount_code_id yesterday!
```

The diagnosis took 4 steps across 4 tools. Stopping after any one step would have led to guessing.

## 6. Safety Habits — Protecting Production

Most serious production incidents involving these four tools share a common cause: an action taken without first verifying what would be affected. Here are the safety rules that prevent the most common mistakes.

**SQL safety:**

```sql
-- Always SELECT first to verify scope:
SELECT COUNT(*) FROM users WHERE status = 'trial';  -- how many rows?
-- Then UPDATE:
UPDATE users SET status = 'expired' WHERE status = 'trial';

-- Use transactions for multi-step changes:
BEGIN;
  UPDATE orders SET status = 'cancelled' WHERE id = 99;
  UPDATE inventory SET quantity = quantity + 1 WHERE product_id = 42;
COMMIT;  -- or ROLLBACK; if something looks wrong
```

**Git safety:**

```bash
git status          # always check before adding
git diff --staged   # review what you are about to commit
git stash           # temporarily save work without committing
# NEVER commit: .env files, API keys, passwords, private keys
# Add them to .gitignore before you accidentally commit them
```

**Linux safety:**

```bash
# Before deleting — verify what 'rm' will affect:
ls -la /tmp/old-logs/   # look at the directory first
# Then delete:
rm -rf /tmp/old-logs/   # now you know exactly what you are removing

# Before running a script in production — check where you are:
pwd                     # are you in the right directory?
whoami                  # are you the right user?
echo $ENVIRONMENT        # are you in the right environment?
```

The 30 seconds spent verifying before acting has saved entire production databases. The minute spent not verifying has ended careers.
