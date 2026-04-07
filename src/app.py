"""
Sample Python application.
This file exists so that the Black formatter has Python files to check.
"""


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}! Welcome to Jenkins CI/CD."


def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def is_even(n: int) -> bool:
    """Check if a number is even."""
    return n % 2 == 0


def fibonacci(n: int) -> list:
    """Return the first n numbers in the Fibonacci sequence."""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    sequence = [0, 1]
    for _ in range(2, n):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence


if __name__ == "__main__":
    print(greet("Developer"))
    print(f"2 + 3 = {add(2, 3)}")
    print(f"4 * 5 = {multiply(4, 5)}")
    print(f"Fibonacci(10) = {fibonacci(10)}")
x=1;y=2;z=x+y
x=1;y=2;z=x+y
