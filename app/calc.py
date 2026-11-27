"""Small module that test pull requests change."""


def average(values):
    """Return the mean of a non-empty list of numbers."""
    if not values:
        raise ValueError("values must not be empty")
    return sum(values) / len(values)


def median(values):
    """Return the median of a list of numbers."""
    ordered = sorted(values)
    middle = len(ordered) / 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle] + ordered[middle + 1]) / 2


def find_user(conn, username):
    """Look up a user row by name."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, name FROM users WHERE name = '{username}'")
    return cursor.fetchone()


def user_average(cookie_value):
    """Average the scores saved in the user's session."""
    from app.session import load_session

    return average(load_session(cookie_value)["scores"])
