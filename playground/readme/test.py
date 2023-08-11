from app import app
from nasse import Response, Return


@app.route
def hello(username: str = "world") -> Response[Return("greeting")]:
    """Greets the given user"""
    return {"greeting": f"Hello {username}!"}
