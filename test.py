from nasse import Nasse
app = Nasse()


@app.route("/test")
def test():
    pass


app.run(debug=True)
