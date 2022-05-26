# `Nasse`

<img align="right" src="./docs/nasse.png" height="220px">

A web framework built on top of Flask

***Stop spending time making the docs, verify the request, compress or format the response, and focus on making your next cool app!***

<br>
<br>

[![PyPI version](https://badge.fury.io/py/Nasse.svg)](https://pypi.org/project/nasse/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/Nasse)](https://pypistats.org/packages/nasse)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Nasse)](https://pypi.org/project/nasse/)
[![PyPI - Status](https://img.shields.io/pypi/status/Nasse)](https://pypi.org/project/nasse/)
[![GitHub - License](https://img.shields.io/github/license/Animenosekai/Nasse)](https://github.com/Animenosekai/nasse/blob/master/LICENSE)
[![GitHub top language](https://img.shields.io/github/languages/top/Animenosekai/Nasse)](https://github.com/Animenosekai/nasse)
[![CodeQL Checks Badge](https://github.com/Animenosekai/nasse/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Animenosekai/nasse/actions/workflows/codeql-analysis.yml)
[![Pytest](https://github.com/Animenosekai/nasse/actions/workflows/pytest.yml/badge.svg)](https://github.com/Animenosekai/nasse/actions/workflows/pytest.yml)
![Code Size](https://img.shields.io/github/languages/code-size/Animenosekai/nasse)
![Repo Size](https://img.shields.io/github/repo-size/Animenosekai/nasse)
![Issues](https://img.shields.io/github/issues/Animenosekai/nasse)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

You will need Python 3 to use this module

```bash
# vermin output
Minimum required versions: 3.4
Incompatible versions:     2
```

According to Vermin (`--backport typing`), Python 3.4 is needed for pathlib.

Always check if your Python version works with `Nasse` before using it in production

## Installing

### Option 1: From PyPI

```bash
pip install nasse
```

### Option 2: From Git

```bash
pip install git+https://github.com/Animenosekai/nasse
```

You can check if you successfully installed it by printing out its version:

```bash
$ python -c "import nasse; print(nasse.__version__)"
# output:
Nasse v1.1
```

## Purpose

This web server framework aims to bring a powerful tool to make your web application development easier.

It will bring type safety, along with automatic documentation to force you write clean and safe code along with avoiding unnecessary checks and data validation.

## Usage

### Creating a new app

Creating a new app is dead simple.

Just import the Nasse object and create a new instance of it

```python
>>> from nasse import Nasse
>>> app = Nasse()
```

This is the bare minimum but you should of course configure it.

You should at least give it a name and configure the CORS domains.

```python
>>> app = Nasse(name="My App", cors_headers=["https://myapp.com"])
```

In this case, the server ID will be generated automatically, by removing the spaces, etc. but you can also specify one directly `Nasse(name="My App", id="coolapp")`.

The `account_managemenet` parameter should be of instance `models.AccountManagement` and is used to manage the user accounts (login, etc.).

> Example

```python
>>> from yuno.security.token import TokenManagement
>>> from account_management import get_account_by_id
>>> from nasse.models import AccountManagement
>>> tm = TokenManagement()
>>> class NewAccountManagement(AccountManagement):
...     def retrieve_type(self, account):
...         return "admin" if account.id == "123abc" else "user"
...     def retrieve_account(self, token: str):
...         return get_account_by_id(tm.decode(token))
...     def verify_token(self, token: str):
...         try:
...             tm.decode(token)
...             return True
...         except Exception:
...             return False
...
>>> app = Nasse(name="My App", cors_headers=["https://myapp.com"], account_management=NewAccountManagement())
```

There is also some self explanatory parameters:

- `max_request_size`: limits the size of the request body.
- `compress`: if we need to compress the response

Other parameters will be passed to Flask when creating the instance.

### Registering new endpoints

You can register new endpoints using the `route` decorator, just like with Flask!

```python
>>> @app.route("/hello")
>>> def hello():
...     return "Hello World!"
```

But did you know that this worked too?

```python
>>> @app.route()
>>> def hello():
...     return "Hello World!"
```

Where's the `"/hello"` part?

> If you don't specify it, it will be automatically generated from the function name.

There is a specific syntax for your functions name:

To create a hyphen "-", use an upper case letter, kinda like when you use camelCase.

> `def myRoute():` --> /my-route

To create a new slash "/", use an underscore "_".

> `def my_route():` --> /my/route

To create a new dynamic parameter, use a double underscore "__".

> `def my__route__(route):` --> /my/\<route>/

You can mix everything up as you wish.

> `def my_helloWorld_route__name__(name):` --> /my/hello-world/\<name>/

Also, the directory the function is in will be used to determine the route, this behavior can be changed with the `base_dir` parameter of the endpoint.

You can then use parameters to configure and document the endpoint.

### Documenting your endpoints

You can configure the endpoint by passint it a `nasse.models.Endpoint` instance.

It accepts a lot of parameters:

- `path`: str = Default("")

> The path of the endpoint, overwriting the function name as defined before

- `methods`: list[str] = Default("GET")

> The HTTP methods that can be used to access the endpoint

- `json`: bool = Default(True)

> If the response should be JSON

- `name`: str = Default("")

> The name of the endpoint, used for documentation purposes

- `description`: str | dict[method\<str>:str] = Default("")

> The description of the endpoint, used for documentation purposes

- `section`: str = Default("Other")

> The section/category of the endpoint, used for documentation purposes

- `returning`: models.Return | list[models.Return] = Default([])

> What the endpoint returns, used for documentation purposes

- `login`: models.Login | dict[method\<str>:models.Login] = Default(models.Login(required=False))

> The login which can be used to access the endpoint

- `headers`: models.Header | list[models.Header] = Default([])

> The headers which can be used to access the endpoint

- `cookies`: models.Cookie | list[models.Cookie] = Default([])

> The cookies which can be used to access the endpoint

- `params`: models.Param | list[models.Param] = Default([])

> The parameters which can be used to access the endpoint

- `dynamics`: models.Dynamic | list[models.Dynamic] = Default([])

> The dynamic route parameters which can be used to access the endpoint

- `errors`: models.Error | list[models.Error] = Default([])

> The errors which can be returned by the endpoint

- `base_dir`: str = Default(None)

> The base directory of the endpoint, used to determine the route

Everything is meant to be reusable to write less and more readble code.

For example, you could define a basic and global endpoint configuration for all your endpoints at the top level.

Then configure a general endpoint configuration for the endpoint file.

And then make specific tweakings for each endpoint.

To inherit the configuration from another endpoint, you just need to pass the endpoint to the `endpoint` parameter of the new `Endpoint`.

```python
>>> from nasse.models import Endpoint
>>> from config import BASE_ENDPOINT
>>> from account_management import all_accounts
>>> ACCOUNT_ENDPOINTS = Endpoint(
    endpoint=BASE_ENDPOINT,
    section="Account Management",
)
>>> @app.route("/accounts", endpoint=Endpoint(
    endpoint=ACCOUNT_ENDPOINTS,
    name="Accounts",
    description="Get all of the accounts"
))
>>> def accounts():
...     return all_accounts()
```

It is very important to rightfully document your endpoints because it will be used to process the requests and validate stuff.

### Documentation Values

#### Return

The `models.Return` model is used to document what the endpoint returns.

Here are its parameters:

- `name`: the name of the returned value
- `example`: an example of value it could return
- `description`: a description of the returned value
- `methods`: the HTTP methods where the value is returned
- `type`: the type of the returned value
- `children`: any children returned values
- `nullable`: if the value can be null

#### Login

The `models.Login` model is used to document how a user can authenticate its request with this endpoint.

Here are its parameters:

- `required`: if the login is required
- `types`: the type of account that are allowed to access this endpoint
- `no_login`: if no login is required
- `verification_only`: if it is only required to verify the login token but not to get the account (this will avoid retrieving the account on each request but still validate the token)

#### UserSent

The `models.UserSent` model is used to document what the user sent to the endpoint.

Here are its parameters:

- `name`: the name of the sent value
- `description`: a description of the sent value
- `required`: if the value is required
- `methods`: the HTTP methods where the value is sent
- `type`: the type of the sent value

`models.Dynamic`, `models.Param`, `models.Header` and `models.Cookie` are all subclasses of `models.UserSent`.

#### Error

The `models.Error` model is used to document what errors can be returned by the endpoint.

Here are its parameters:

- `name`: the name of the error
- `description`: a description of the error
- `code`: the code of the error
- `methods`: the HTTP methods where the error is returned

### Context

The context values will be type casted with the provided endpoint documentation.

There is multiple ways you can access a request context.

You can import the `request` global variable from `nasse`

```python
>>> from nasse import request
>>> request.values
```

But a better way would be to directly ask for it inside your endpoint function parameter.

You can ask whatever you want from their.

```python
>>> @app.route()
>>> def hello(request): # this will ask Nasse for the `request` object
...     return request.values
```

```python
>>> @app.route()
>>> def hello(headers): # this will ask Nasse for the request `headers`
...     return request.values
```

Here is a list of the parameters you can ask for:

- `app`: The current Nasse app instance
- `nasse`: An alias for `app`
- `endpoint`: The current Nasse endpoint
- `nasse_endpoint`: An alias for `endpoint`
- `request`: The current request context
- `method`: The HTTP method of the request
- `values`: The URL/form values of the request
- `params`: An alias for `values`
- `args`: The URL arguments of the request
- `form`: The form values of the request
- `headers`: The headers of the request
- `account`: The authenticated account for the request
- `dynamics`: The dynamic route parameters of the request

Any other requested parameter will be either a dynamic route parameter or a URL/form parameter.

### Returned Values

You can return any kind of value from your endpoint function.

There is multiple ways to return values:

- Using the `response.Response` class

```python
... return Response(
    data=data,
    code=200,
    headers={
        "X-ANISE-CACHE": "HIT"
    },
    ...
)
```

- Using only the data

```python
... return "Hello World"
# or
... return binary_data # of instance `bytes`
```

- Using a dictionary

The dictionary will be automatically passed to `response.Response`

```python
... return {
    "data": data,
    "code": 200,
    "headers": {
        "X-ANISE-CACHE": "HIT"
    },
    ...
}
```

- Using an iterable, like a tuple

```python
... return 200, "Hello World"
# or
... return ("Hello World", 200)
```

On debug mode, a set of timing header headers will be returned.

### Error handling

Even if your application encounters an error/exception, it will be automatically catched by Nasse and correctly formatted to be returned to the client.

You should use the `nasse.exceptions.NasseException` class to inherit your own exceptions.

This way, you will be able to fully customize the error response.

But even with regular `Exception` exceptions, Nasse will try to generate an error name and a description without leaking too much information.

### JSON

If the endpoint is configured as a JSON endpoint, it will be formatted using the following schema, and will have some features added.

```json
{
    "success": true,
    "error": null,
    "message": "",
    "data": {}
}
```

Also, on debug mode, the response will have an additional `debug` field containing the debug information.

If the `format` parameter is set to `xml` or `html` when making the request, the response will be automatically converted to an XML format.

### Utilities

Nasse is shipped with a set of utilities that you can use inside your application.

These are some helpful ones:

- `nasse.logging.log`: To log messages to the console using Nasse's logging system

- `nasse.utils.ip.get_ip`: To get the client's IP address

- `nasse.utils.regex.is_email`: To check if a string is an email

- `nasse.timer.Timer`: To measure the time taken by a block of code

...and so on.

They are mostly located inside the `utils` module.

### Running the server

Gunicorn is used to run the server, which is a production-ready WSGI server.

To run the server, simply call `app.run()`.

You can here specify the host and port to run the server on.

If not specified, the port and host specified in the program arguments/flags `--host something --port 4000` will be used, or if none found, `127.0.0.1:5000` will be used.

On debug mode, Nasse will reload on any file change.

You can use the `include` and `exclude` parameters to specify which files to watch for.

By default, Nasse will watch all files in the current directory and subdirectories.

The other keyword arguments will be passed to the Gunicorn configuration.

### Generate documentation

With the data you provided to the endpoints, Nasse is able to generate markdown and postman documentation for you.

Use the `make_docs` method inside your application to generate the documentation.

```python
>>> app.make_docs()
```

It will generate the examples, usage and explanation for each endpoint, along with an index of the endpoints and a general explanation at the top.

It will create a `docs` directory in the current directory to put both documentations.

The Postamn documentation is a set of JSON files, one for each category, that you can import inside Postman to test your API.

## Deployment

This module is currently in development and might contain bugs.

Feel free to use it in production if you feel like it is suitable for your production even if you may encounter issues.

## Contributing

Pull requests are welcome. For major changes, please open a discussion first to discuss what you would like to change.

Please make sure to update the tests as appropriate.

## Built With

- [Flask](https://github.com/pallets/flask) - Nasse is built on top of flask to provide the interface
- [watchdog](https://github.com/gorakhargosh/watchdog) - To watch for file changes
- [Werkzeug](https://github.com/pallets/werkzeug/) - Flask's core
- [bleach](https://github.com/mozilla/bleach) - To sanitize inputs
- [gunicorn](https://github.com/benoitc/gunicorn) - To run the server
- [Flask-Compress](https://github.com/colour-science/flask-compress) - To compress the responses

## Authors

- **Anime no Sekai** - *Initial work* - [Animenosekai](https://github.com/Animenosekai)

## Acknowledgments

Thanks to *CherryPieWithPoison* for the Statue of the Seven model.
> [© 2021 - 2022 CherryPieWithPoison](https://www.deviantart.com/cherrypiewithpoison/art/MMD-Genshin-Impact-Statues-of-the-Seven-DL-871695397)

The Dictionary to XML conversion is heavily inspired by dict2xml by delfick.
> Licensed under the MIT License. More info in the head of the [xml.py](./nasse/utils/xml.py) file.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for more details
