"""A bunch of test endpoints"""
from nasse import Nasse

app = Nasse()


@app.route
def saiki(username: str, password: str, limit: int = 10):
    """
    Calls Saiki

    Parameters
    ----------
    username: str
        The username of the user
    """
    return {
        "username": username,
        "password": password,
        "limit": limit
    }

@app.route
def _():
    return "OK"