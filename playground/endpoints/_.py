"""_.py: a nasse test"""
from nasse import Nasse, Response, Return
app = Nasse()


@app.route
def hello(username: str = "someone") -> Response[Return("hello"), Return("hi")]:
    """A hello world"""
    return Response({"hello": username})
