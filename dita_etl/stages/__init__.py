"""Pipeline stages.

Each stage has a single responsibility, accepts a typed input contract, and
returns a typed output contract. Stages contain no business logic — they
delegate to pure functions and isolate all I/O.
"""
