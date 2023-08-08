from nasse import Nasse
app = Nasse()

@app.route
def solve__exercice__(exercice: str, limit: int = 10):
    """Solves the given exercice"""
    return [exercice] * limit
