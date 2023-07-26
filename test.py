"""Simple test"""
from nasse import Nasse

app = Nasse("test")


@app.route(category="Testing", sub_category="Sub Category")
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


def hey(a: int, b: float = 2.3):
    """We are testing argument-less endpoints"""
    return "Yay!"

for i in range(10):
    for j in range(10):
        app.route(category=f"Hey {i}", sub_category=f"Hi {j}", path=f"/{i}/{j}")(hey)

# app.make_docs()
# app.run(debug=True)
