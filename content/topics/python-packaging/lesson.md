# Python Packaging and Environments

Every real Python project needs to answer three questions: what packages does it depend on, at what versions, and how is that kept isolated from every other project on the same machine? This topic covers virtual environments, pip/requirements.txt, semantic versioning, and the modern pyproject.toml project manifest.

Note: this app's sandbox cannot literally run `pip` or `python -m venv` (those are shell/process operations, deliberately blocked in the code runner) — the labs here focus on the underlying logic (parsing requirements, comparing versions, validating config) that these tools are built on, which is exactly the part worth understanding deeply.

## 1. Why Virtual Environments — Isolating Project Dependencies

A virtual environment ("venv") is a private, isolated set of installed packages for one project — separate from your system Python and every other project on the same machine. Without one, every project on your computer would have to share a single global set of installed package versions.

```python run
# Simulating why isolation matters: two "projects" needing different tool versions
project_a_needs = {'requests': '2.28.0'}
project_b_needs = {'requests': '2.31.0'}
print(f"Without venvs, only ONE requests version could be installed globally: conflict={project_a_needs['requests'] != project_b_needs['requests']}")
```

Creating and using one is three commands:

```
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate      # macOS/Linux
pip install requests
```

`python -m venv .venv` creates the isolated environment (a `.venv` folder holding its own Python interpreter copy and package directory). `activate` switches your current shell to use that environment's Python and `pip` instead of the system-wide ones. Every `pip install` after that only affects `.venv`, never your system Python or any other project.

## 2. pip and requirements.txt — Declaring Dependencies

`requirements.txt` is a plain text list of a project's dependencies, one per line, so anyone (including a future you, or a deployment server) can recreate the exact same set of installed packages with `pip install -r requirements.txt`.

```python run
def parse_requirements(text):
    packages = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        packages.append(line)
    return packages

requirements_text = '''
# Core dependencies
requests==2.31.0
flask>=2.0,<3.0

pytest==7.4.0
'''
print(parse_requirements(requirements_text))
```

`==` pins an **exact** version (most reproducible, used for applications you deploy). `>=` sets a minimum; combined with `<` it defines a range (common for libraries, which want to stay compatible with a range of versions their users might have). No version constraint at all (`requests`) means "whatever the latest version is right now" — convenient while developing, risky for anything you'll run again later, since a future install could silently pull in a different, possibly incompatible version.

## 3. Semantic Versioning — What X.Y.Z Actually Means

Most Python packages follow **semantic versioning**: `MAJOR.MINOR.PATCH` (e.g. `2.31.0`). A `PATCH` bump (2.31.0 → 2.31.1) means a bug fix with no API changes. A `MINOR` bump (2.31.0 → 2.32.0) means new functionality was added, but everything that worked before still works. A `MAJOR` bump (2.31.0 → 3.0.0) means something that used to work might now be broken — a breaking change.

```python run
def parse_version(version_str):
    major, minor, patch = version_str.split('.')
    return (int(major), int(minor), int(patch))

v1 = parse_version('2.31.0')
v2 = parse_version('2.4.10')
print(v1)
print(v2)
print(v1 > v2)
```

**Common trap:** comparing version strings directly instead of parsing them into numbers first. `'1.9.0' < '1.10.0'` as plain strings compares character by character — and `'9' > '1'`, so Python says `'1.9.0' > '1.10.0'`, which is semantically backwards.

```python run
def parse_version(v):
    return tuple(int(p) for p in v.split('.'))

as_strings = sorted(['1.9.0', '1.10.0', '1.2.0'])
as_versions = sorted(['1.9.0', '1.10.0', '1.2.0'], key=parse_version)
print(as_strings)
print(as_versions)
```

Sorting the raw strings gives the wrong order (`'1.10.0'` sorts before `'1.2.0'`); parsing each version into a tuple of integers first, then sorting by that, gives the semantically correct order. This is exactly why version-comparison tools (and `pip` itself) never compare version strings directly.

## 4. pyproject.toml — The Modern Project Manifest

`pyproject.toml` is the modern, standardized file describing a Python project — its name, version, dependencies, and how it should be built. It replaced the older, more ad-hoc `setup.py` approach.

```
[project]
name = "my-package"
version = "1.0.0"
dependencies = ["requests>=2.28"]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
```

The `[project]` table holds metadata a checker (or an installer) reads and validates — every real project manifest needs at least a name and a version.

```python run
def validate_project_config(config):
    errors = []
    if 'name' not in config:
        errors.append('missing name')
    if 'version' not in config:
        errors.append('missing version')
    return errors

good_config = {'name': 'my-package', 'version': '1.0.0'}
bad_config = {'name': 'my-package'}
print(validate_project_config(good_config))
print(validate_project_config(bad_config))
```

This app's own `requirements.txt` (for `wasmtime`) and `pyproject.toml` (for ruff's lint config) are real, small examples of exactly this — a project declaring what it needs and how it's configured, in one standard place.

## 5. Project Structure — Organizing Code, Tests, and Packages

A Python **package** is just a directory containing an `__init__.py` file — that one file is what tells Python "treat this folder as an importable package," not just a folder full of unrelated scripts.

```python run
def is_package(directory_contents):
    return '__init__.py' in directory_contents

print(is_package(['core.py', '__init__.py']))
print(is_package(['core.py']))
```

A common, sensible layout for a small real project:

```
my_project/
    src/
        my_project/
            __init__.py
            core.py
    tests/
        test_core.py
    pyproject.toml
    README.md
```

Separating `src/` (the actual package) from `tests/` (which imports and exercises it) keeps the package's public shape honest — code under `tests/` has to import `my_project` the same way an external user would, instead of accidentally relying on being in the same folder.

## 6. Common Traps — Committing venvs, Unpinned Versions, and Version-String Bugs

Three mistakes account for most real-world packaging pain:

- **Committing the `.venv` folder to version control.** A virtual environment contains machine-specific binary files and can be huge — it belongs in `.gitignore`, never in the repository. Anyone cloning the project should run `python -m venv .venv` themselves and install from `requirements.txt`.
- **Leaving dependencies completely unpinned** (`requests` with no version at all) in a deployed application. It works fine today; months later, a fresh install pulls in whatever the latest version happens to be then — which might have a breaking change — and the exact same code starts failing with no code change of its own. Pin exact versions (`==`) for applications you deploy; use ranges (`>=`, `<`) mainly for libraries meant to stay flexible for their users.
- **Comparing version strings directly instead of parsing them into numbers.** As section 3 showed, `'1.9.0' < '1.10.0'` as plain text compares incorrectly — always parse a version into its numeric parts before comparing or sorting.

**Rule of thumb:** a project's dependency list should be specific enough that running it again in a year, on a different machine, installs the exact same thing you tested with today. That reproducibility is the entire point of `requirements.txt`, `pyproject.toml`, and virtual environments working together.
