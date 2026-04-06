"""Utility functions for the sample application."""

import os
import datetime


def get_current_timestamp() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return datetime.datetime.isoformat() + "Z"


def file_exists(path: str) -> bool:
    """Check if a file exists at the given path."""
    return os.path.isfile(path)


def read_file_content(path: str) -> str:
    """Read and return the content of a file."""
    with open(path, "r") as f:
        return f.read()


def flatten_list(nested: list) -> list:
    """Flatten a nested list into a single-level list."""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def chunk_list(data: list, size: int) -> list:
    """Split a list into chunks of the given size."""
    return [data[i : i + size] for i in range(0, len(data), size)]
