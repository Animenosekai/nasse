from nasse import Nasse
app = Nasse("test")


@app.route("/test", category="Testing", description="This is a cool testing endpoint")
def test():
    pass


# app.make_docs()
# app.run(debug=True)
