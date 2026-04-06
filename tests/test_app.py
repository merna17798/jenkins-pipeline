"""Tests for the sample application."""

from src.app import add, multiply, divide, is_even, fibonacci, greet


def test_greet():
    """Test the greet function."""
    assert greet("Alice") == "Hello, Alice! Welcome to Jenkins CI/CD."


def test_add():
    """Test the add function."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_multiply():
    """Test the multiply function."""
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0
    assert multiply(-2, 3) == -6


def test_divide():
    """Test the divide function."""
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5


def test_divide_by_zero():
    """Test that dividing by zero raises ValueError."""
    try:
        divide(1, 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_is_even():
    """Test the is_even function."""
    assert is_even(2) is True
    assert is_even(3) is False
    assert is_even(0) is True


def test_fibonacci():
    """Test the fibonacci function."""
    assert fibonacci(0) == []
    assert fibonacci(1) == [0]
    assert fibonacci(5) == [0, 1, 1, 2, 3]
    assert fibonacci(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
