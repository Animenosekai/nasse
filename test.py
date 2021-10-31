from nasse import Nasse
from nasse.models import Endpoint, Header, Return

app = Nasse(cors=True)


@app.route(Endpoint(
    path="/test-hello",
    methods="GET",
    name="Hello Test",
    description="This is an endpoint to test Nasse",
    section="Test",
    returning=Return(
        name="message",
        example="A message",
        description="This is a message describing what happened",
        methods="HEY",
        type="string"
    ),
    headers=[
        Header(name="Hello", required=False),
        {
            "name": "X-ANISE",
            "required": False
        }
    ],
    params={
        "hello": {
            "required": True,
            "description": "A param"
        }
    },
    errors=ValueError()
))
def test_helloWorld():
    return {
        "hello": "world"
    }, 404


app.run()
