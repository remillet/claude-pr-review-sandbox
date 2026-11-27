"""Small module that test pull requests change."""


def average(values):
    """Return the mean of a non-empty list of numbers."""
    if not values:
        raise ValueError("values must not be empty")
    return sum(values) / len(values)
