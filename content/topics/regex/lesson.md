# Regular Expressions in Python

Regular expressions ('regex') are a compact pattern-matching language for finding, validating, and extracting text. Python's `re` module is the standard tool for parsing a log line, validating a username, redacting an email address, or pulling a date out of a filename.

This topic covers the patterns and functions you'll actually reach for, plus the traps that catch almost everyone the first time — greedy matching, forgetting `r'...'`, and reaching for regex when a real parser is the correct tool instead.

## 1. Pattern Basics — Literals, Character Classes, and Quantifiers

A regular expression is a tiny pattern-matching language embedded in a string. `\d+` means "one or more digits," `[A-Za-z]+` means "one or more letters," `\w+` means "one or more word characters (letters, digits, or underscore)." `re.search()` finds the first match anywhere in a string; a `()` group around part of a pattern lets you pull out just that piece.

```python run
import re

text = 'Order #4521 shipped on 2024-03-15'

has_digits = re.search(r'\d+', text)
print(has_digits.group())

order_number = re.search(r'#(\d+)', text)
print(order_number.group())
print(order_number.group(1))
```

`group()` (no argument) returns the whole match; `group(1)` returns just the first parenthesized group — here, the digits without the leading `#`. Character classes like `[aeiou]` match any *one* of the listed characters; `+` means "one or more of the previous thing," and `*` means "zero or more."

```python run
import re

print(bool(re.fullmatch(r'[A-Za-z]+', 'Hello')))
print(bool(re.fullmatch(r'[A-Za-z]+', 'Hello123')))
print(re.findall(r'[aeiou]', 'the quick brown fox'))
print(re.findall(r'\w+', "user_name-42 costs $9.99"))
```

**Always use a raw string (`r'...'`) for patterns.** Without the `r` prefix, Python's own string escaping (`\n`, `\t`) competes with regex escaping (`\d`, `\w`), producing confusing bugs — `r'\d'` is unambiguous.

## 2. Matching Functions — match, search, fullmatch, and findall

Four functions cover almost every use case, and picking the wrong one is a common source of confusion: `re.match()` only checks the **start** of the string, `re.search()` checks the whole string for the first match anywhere, `re.fullmatch()` requires the **entire** string to match, and `re.findall()` returns every non-overlapping match as a list.

```python run
import re

text = 'cat hat bat'
print(re.match(r'cat', text))
print(re.match(r'hat', text))
print(re.search(r'hat', text))
print(re.findall(r'.at', text))
print(re.fullmatch(r'.at', 'cat'))
```

`re.match(r'hat', text)` returns `None` because `text` doesn't *start* with 'hat' — even though 'hat' clearly appears in the middle. `re.search()` is what most beginners actually want; `re.match()` is for validating that a string *begins* a certain way. A match object is truthy, and `None` (no match) is falsy — `if re.search(...):` is the idiomatic way to check for a match without caring about its exact position or contents.

## 3. Groups — Capturing and Extracting Parts of a Match

Parentheses `()` create a **group** — a piece of the pattern you can pull out individually after a match, instead of re-parsing the whole matched string yourself.

```python run
import re

log = '2024-03-15 ERROR Connection refused'
m = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\w+) (.+)', log)
print(m.group(1), m.group(2), m.group(3))
print(m.group(4))
print(m.groups())
```

`{4}` means "exactly 4 of the previous thing" — `\d{4}` is exactly 4 digits. Numbered groups (`group(1)`, `group(2)`, ...) get confusing fast in a pattern with many groups; **named groups** (`(?P<name>...)`) are clearer and don't break if you reorder groups later.

```python run
import re

m = re.search(r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})', '2024-03-15')
print(m.group('year'))
print(m.groupdict())
```

`groupdict()` returns every named group as a ready-to-use dict — a common way to turn an unstructured string (a log line, a filename) into structured data.

## 4. Substitution — re.sub for Search-and-Replace

`re.sub(pattern, replacement, text)` replaces every match of `pattern` in `text`. The replacement can be a plain string, or a function — called once per match, receiving the match object and returning the string to substitute in its place.

```python run
import re

text = 'Contact: alice@example.com or bob@example.com'
redacted = re.sub(r'\w+@\w+\.\w+', '[EMAIL]', text)
print(redacted)

def upper_match(m):
    return m.group().upper()

result = re.sub(r'\b[a-z]+\b', upper_match, 'hello world')
print(result)
```

`\b` is a **word boundary** — it matches the invisible edge between a word character and a non-word character (or the start/end of the string), without consuming any characters itself. `\b[a-z]+\b` means "a run of lowercase letters that starts and ends at a word boundary" — useful for matching whole words rather than accidentally matching the middle of one.

## 5. Compiling Patterns and Common Flags

`re.compile(pattern)` pre-parses a pattern into a reusable object with the same `.match()`/`.search()`/`.findall()` methods as the module-level functions. Compiling once and reusing the result is both faster (no re-parsing the pattern string every call) and clearer when the same pattern is applied many times, e.g. inside a loop.

```python run
import re

pattern = re.compile(r'^\s*#')
lines = ['# comment', '  # indented comment', 'code = 1', '   not a comment']
comment_lines = [line for line in lines if pattern.match(line)]
print(comment_lines)

print(bool(re.search(r'hello', 'HELLO WORLD', re.IGNORECASE)))
```

`^` anchors a match to the **start** of the string (or line, with `re.MULTILINE`); `$` anchors to the end. `re.IGNORECASE` (or the shorter `re.I`) makes matching case-insensitive — passed as an extra argument to `search`/`match`/`compile`. `'   not a comment'` is correctly excluded above because it has non-whitespace content before any `#` at all — there is no `#` in that string.

## 6. Common Traps — Greedy Matching, Escaping, and When Not to Use Regex

By default, quantifiers (`*`, `+`) are **greedy** — they match as much as possible. `.*?` (adding `?` after a quantifier) makes it **lazy** instead, matching as little as possible.

```python run
import re

html = '<b>bold</b> and <i>italic</i>'
greedy = re.findall(r'<.*>', html)
lazy = re.findall(r'<.*?>', html)
print(greedy)
print(lazy)
```

The greedy pattern `<.*>` matches from the **first** `<` all the way to the **last** `>` in the entire string — one giant match spanning both tags — because `.*` happily consumes everything in between, including the other tags. The lazy `<.*?>` stops at the *first* `>` it can, correctly producing four separate small matches.

**Other common traps:**
- Forgetting to escape a literal special character — `.` matches *any* character, not just a literal dot; to match a real dot, write `\.`
- Forgetting the `r` prefix on a pattern string, letting Python's own string escaping interfere with regex escaping
- Reaching for regex to parse a *nested or recursive* structure (HTML, JSON, deeply nested brackets) — regex has no concept of nesting depth; a real parser (or the `json` module) is the correct tool there, not a bigger regex

**Rule of thumb:** regex is excellent for finding, validating, and extracting patterns in flat, line-oriented text (log lines, simple identifiers, dates). The moment you need to track how deep you are inside nested structure, reach for a real parser instead.
