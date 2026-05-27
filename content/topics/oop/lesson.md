# OOP

## 1. Class Definitions and Instance Creation

A class defines attributes and methods for objects of that type. Calling the class creates an instance. Treat class definitions as domain modeling tools: each class should represent a concept with a clear responsibility.

## 2. __init__, Instance State, and self

`__init__` sets up per-instance state. Inside instance methods, `self` points to the current object. Understanding this is essential for avoiding shared-state bugs and writing predictable methods.

## 3. Class Variables vs Instance Variables

Class variables are shared across all instances, while instance variables belong to each object. Mixing them up can cause subtle bugs where one object's change affects every object unexpectedly.

## 4. Methods, Encapsulation, and API Shape

Methods should expose a clean interface and keep object internals manageable. Encapsulation does not mean hiding everything; it means presenting operations that keep object state valid and understandable.

## 5. Inheritance vs Composition

Inheritance is useful when subclasses genuinely specialize a base class contract. Composition is usually safer for assembling behavior from smaller pieces. Start with composition unless inheritance expresses a natural relationship.

## 6. Dataclasses for Data-Centric Models

When a class mainly stores structured data, dataclasses reduce boilerplate while preserving clarity. They are especially useful for configuration and record-like objects that still benefit from type hints and defaults.
