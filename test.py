"""Simple test"""
from nasse import Nasse

app = Nasse("test")


@app.route(category="Testing")
def test(testing: int, testing2: float = 2.3):
    """
    This is a cool testing endpoint

    Parameters
    ----------
    testing
        Testing an argument description
    testing2
        Testing another argument description
    """
    print(testing)


@app.route
def hey(a: int, b: float = 2.3):
    """We are testing argument-less endpoints"""
    return "Yay!"

# app.make_docs()
# app.run(debug=True)
