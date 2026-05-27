# Functions and Clean Code

## 1. Function Signatures and Basic Calls

A function starts with `def`, then a name, parameter list, and indented body. Each call supplies argument values that bind to parameters. Naming and ordering matter, because signatures define how other code can safely call your function.

## 2. Default Argument Values and the Mutable Default Trap

Default values are evaluated once when the function is defined, not every time it is called. This is why mutable defaults can retain state across calls. Use `None` as a default sentinel, then create a new list or dict inside the function body.

## 3. Keyword Arguments and Readable Call Sites

Keyword arguments improve readability, especially when functions have many parameters or optional settings. Python lets you mix positional and keyword calls, but readability should lead your choice. Clear call sites reduce mistakes in production code.

## 4. Special Parameters, *args, and **kwargs

Python supports flexible signatures with positional-only, keyword-only, variadic positional (`*args`), and variadic keyword (`**kwargs`) parameters. Learn these to read modern library APIs and design wrappers without brittle argument handling.

## 5. Return Values, Scope, and Side Effects

Functions should return values that callers can reuse. Prefer returning data over printing. Keep scope explicit: names created inside a function are local unless declared otherwise. Reduce hidden side effects so tests and debugging remain predictable.

## 6. Docstrings, Annotations, and Function Clarity

Docstrings explain behavior and intent. Type annotations document expected input and output shapes. They do not replace tests, but they improve code comprehension and tooling support. Together they make functions easier for other developers to use correctly.
