# Python for DevOps

Python is the most popular language for DevOps automation — from deployment scripts and infrastructure tools to CI/CD pipelines and monitoring jobs. Operational scripts that run in production are different from one-off scripts you write to explore data: they need to handle missing files, bad config, failed commands, and partial failures gracefully.

Think of a well-designed operational script like a professional surgeon's checklist. Before the operation (execution), they validate conditions. They have a plan for each step. If something goes wrong mid-way, they have a defined protocol — not panic. Python DevOps automation follows the same discipline: load config → validate → inspect current state → compute plan → execute with dry-run option → record what happened → fail clearly with context.

## 1. The Operational Automation Mindset

The difference between a 'works on my machine' script and a production-ready automation tool comes down to one thing: how the script handles things going wrong.

A toy script assumes everything is present and correct. A production script assumes nothing — it validates every assumption before acting.

**The questions every operational script should answer:**
- What are my inputs, and what happens if they are missing or malformed?
- What is the current state of the system before I make changes?
- What will I do, and can I show a dry run before I do it?
- If step 3 fails, what state is the system in, and how does the operator know?
- How do I report what happened so the next person understands?

```python
# The mindset in code: validate early, fail clearly
import sys
from pathlib import Path

def load_and_validate_config(config_path: str) -> dict:
    path = Path(config_path)

    if not path.exists():
        print(f'ERROR: Config file not found: {config_path}', file=sys.stderr)
        sys.exit(1)

    import json
    try:
        config = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f'ERROR: Invalid JSON in {config_path}: {e}', file=sys.stderr)
        sys.exit(1)

    required = ['environment', 'service_name', 'replicas']
    missing = [k for k in required if k not in config]
    if missing:
        print(f'ERROR: Missing required config keys: {missing}', file=sys.stderr)
        sys.exit(1)

    return config
```

Failing early with a clear message is a feature, not a weakness. It is far better to stop and explain the problem than to continue and corrupt state silently.

## 2. Configuration and Path Handling

Real operational scripts need to read configuration from files, environment variables, or both. `pathlib` and the `os`/`json` standard library modules handle this cleanly and cross-platform.

**The golden rules for config in scripts:**
1. Never hardcode paths — use config files or environment variables
2. Never hardcode secrets — use environment variables or a secrets manager
3. Validate required keys exist before using them
4. Use `pathlib.Path` instead of string concatenation for file paths

```python
import os
import json
from pathlib import Path

# Reading a JSON config file safely:
config_path = Path(os.environ.get('CONFIG_PATH', 'config/default.json'))
if not config_path.exists():
    raise FileNotFoundError(f'Config not found at: {config_path}')
config = json.loads(config_path.read_text(encoding='utf-8'))

# Reading from environment variables with defaults:
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = int(os.environ.get('DB_PORT', '5432'))
api_key = os.environ.get('API_KEY')   # no default — must be set
if not api_key:
    raise ValueError('API_KEY environment variable is required')

# pathlib makes path operations readable and OS-independent:
log_dir = Path('/var/log/myapp')
log_dir.mkdir(parents=True, exist_ok=True)  # create if missing, no error if exists
latest_log = log_dir / 'deploy.log'         # OS-correct path joining with /
```

**`pathlib` vs string paths:** `Path('logs') / 'deploy.log'` is safer and more readable than `'logs' + os.sep + 'deploy.log'`. It handles Windows backslashes vs Unix forward-slashes automatically.

## 3. Safe Shell Commands with subprocess

Most automation needs to run shell commands: `git pull`, `docker build`, `kubectl apply`. Python's `subprocess` module lets you do this safely. The wrong approach is `os.system('command ' + user_input)` — this is a **shell injection vulnerability**.

**Always use argument lists, not shell strings:**

```python
import subprocess

# DANGEROUS — never do this with any external input:
# os.system('git clone ' + repo_url)   # shell injection risk!

# SAFE — use a list of arguments:
result = subprocess.run(
    ['git', 'clone', repo_url],   # each arg is a separate list item
    capture_output=True,          # capture stdout and stderr
    text=True,                    # decode bytes to str automatically
    timeout=60,                   # fail after 60 seconds instead of hanging
    check=False,                  # do not raise on non-zero exit — we check manually
)

if result.returncode != 0:
    print(f'git clone failed (exit {result.returncode})')
    print('stdout:', result.stdout)
    print('stderr:', result.stderr)
    raise RuntimeError('Deployment aborted: git clone failed')

print('Cloned successfully')
print(result.stdout)
```

**Why argument lists instead of `shell=True`?**
- No shell injection: `repo_url` is passed as data, not parsed as shell syntax
- No shell metacharacter surprises: spaces, `&`, `;`, `|` in arguments work as intended
- Explicit timeouts prevent the script from hanging indefinitely
- Captured output lets you log what actually happened

## 4. Idempotency and Dry Run Mode

**Idempotency** means running the same script multiple times produces the same result as running it once. This is critical for automation that might be re-run after a partial failure, a retry, or by accident.

**Dry run mode** shows what the script *would* do without actually doing it — invaluable for reviewing automation before it runs in production.

```python
import argparse

def ensure_directory_exists(path, dry_run=False):
    from pathlib import Path
    p = Path(path)
    if p.exists():
        print(f'  [SKIP] Directory already exists: {p}')  # idempotent — no error
        return
    if dry_run:
        print(f'  [DRY RUN] Would create directory: {p}')
        return
    p.mkdir(parents=True, exist_ok=True)
    print(f'  [DONE] Created directory: {p}')

def deploy(config, dry_run=False):
    print(f"Deploying {config['service']} to {config['environment']}")
    if dry_run:
        print('  [DRY RUN] Skipping actual deployment — would run:')
        print(f"    docker push {config['image']}")
        print(f"    kubectl set image deploy/{config['service']} ...")
        return
    # ... actual deployment code

# CLI interface:
parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true', help='Preview actions without executing')
args = parser.parse_args()

deploy(config, dry_run=args.dry_run)
```

A script that can be safely re-run and previewed is one that operators trust. Trust is what makes automation actually used in real incidents.

## 5. Logging — What Happened and Why

Print statements disappear into the void when a script runs in CI or on a server. The Python `logging` module writes structured, timestamped output that can be captured by log aggregation systems and inspected after the fact.

```python
import logging

# Configure logging at the top of your script:
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('deploy')

# Use logger instead of print:
logger.info('Starting deployment for service: %s', config['service'])
logger.warning('Replicas requested (%d) exceeds recommended max (10)', replicas)
logger.error('Failed to connect to registry: %s', error_msg)

# Log decisions, not just actions:
if config.get('skip_health_check'):
    logger.warning('Health check skipped — set by config. This is not recommended.')
else:
    logger.info('Running health check...')
    # ...
```

**Log the things that matter for debugging:**
- What config was loaded and from where
- Each decision point: 'skipping X because Y', 'proceeding with Z'
- Each action taken and whether it succeeded
- What changed vs what was already correct
- Any warnings about unusual conditions

Good logs make the difference between an operator who can diagnose a 2am incident in 5 minutes and one who spends 2 hours guessing.

## 6. Structured Reporting and Exit Codes

When automation is done — whether successful or not — it should produce a clear summary that a human (or another script) can understand immediately. Structured exit codes tell CI/CD systems whether the script succeeded.

```python
import sys
from datetime import datetime, timezone

def run_deployment_steps(steps, dry_run=False):
    results = []
    for step in steps:
        try:
            if not dry_run:
                step['execute']()
            results.append({'name': step['name'], 'status': 'done' if not dry_run else 'dry_run'})
        except Exception as exc:
            results.append({'name': step['name'], 'status': 'failed', 'error': str(exc)})

    return results

def print_summary(results, service, environment):
    done    = [r for r in results if r['status'] == 'done']
    failed  = [r for r in results if r['status'] == 'failed']
    skipped = [r for r in results if r['status'] == 'dry_run']

    print('\n' + '='*50)
    print(f'DEPLOYMENT SUMMARY — {service} → {environment}')
    print(f'Timestamp: {datetime.now(timezone.utc).isoformat()}')
    print(f'Done:    {len(done)}')
    print(f'Skipped: {len(skipped)}')
    print(f'Failed:  {len(failed)}')

    if failed:
        print('\nFAILED STEPS:')
        for r in failed:
            print(f'  x {r["name"]}: {r["error"]}')
        return 1   # non-zero exit code → CI marks the job as failed

    print('\nAll steps completed successfully.')
    return 0

results = run_deployment_steps(steps)
exit_code = print_summary(results, config['service'], config['environment'])
sys.exit(exit_code)   # 0 = success, non-zero = failure
```

**Exit code 0 = success, anything else = failure.** CI/CD systems like GitHub Actions, Jenkins, and GitLab CI read exit codes to determine whether to continue to the next stage or mark the pipeline as failed.
