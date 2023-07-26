from nasse import Nasse
app = Nasse("test")


@app.route("/test", category="Testing", description="This is a cool testing endpoint", parameters=[{"name": "test", "description": "testing description"}])
def test():
    pass


# app.make_docs()
# app.run(debug=True)
