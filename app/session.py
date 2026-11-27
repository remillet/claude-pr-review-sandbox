"""Session helpers (deliberately unsafe sample code for the review test)."""
import base64
import pickle


def load_session(cookie_value):
    """Decode the session stored in the browser cookie."""
    return pickle.loads(base64.b64decode(cookie_value))
