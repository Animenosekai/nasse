from app import app


@app.route
def wow():
    pass


@app.route(sub_category="New Sub Cat.")
def wow2():
    pass


@app.route(sub_category="New Sub Cat.")
def wow3():
    pass
