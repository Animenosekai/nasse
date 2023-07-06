from nasse import Nasse
app = Nasse()


@app.route("/test")
def test():
    pass


app.make_docs()
app.run(debug=True)
