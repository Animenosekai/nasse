from nasse import Nasse

app = Nasse()


@app.route("/solve/<exercise>")
def solve__exercise__(exercise: int = 0):
    return exercise
