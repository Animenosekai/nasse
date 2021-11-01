from nasse import Nasse
app = Nasse()


@app.route()
def test_helloWorld(params):
    if "username" in params:
        return {"hello": params["username"]}, 200
    return {"hello": "world"}, 404


app.run()
