# `Nasse`

> A web framework built on top of Flask

***Stop spending time making the docs, verify the request, compress or format the response, and focus on making your next cool app!***

[![PyPI version](https://badge.fury.io/py/Nasse.svg)](https://pypi.org/project/Nasse/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/Nasse)](https://pypistats.org/packages/Nasse)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/Nasse)](https://pypi.org/project/Nasse/)
[![PyPI - Status](https://img.shields.io/pypi/status/Nasse)](https://pypi.org/project/Nasse/)
[![GitHub - License](https://img.shields.io/github/license/Animenosekai/Nasse)](https://github.com/Animenosekai/Nasse/blob/master/LICENSE)
[![GitHub top language](https://img.shields.io/github/languages/top/Animenosekai/Nasse)](https://github.com/Animenosekai/Nasse)
[![CodeQL Checks Badge](https://github.com/Animenosekai/Nasse/workflows/CodeQL%20Python%20Analysis/badge.svg)](https://github.com/Animenosekai/Nasse/actions?query=workflow%3ACodeQL)
[![Pytest](https://github.com/Animenosekai/Nasse/actions/workflows/pytest.yml/badge.svg)](https://github.com/Animenosekai/Nasse/actions/workflows/pytest.yml)
![Code Size](https://img.shields.io/github/languages/code-size/Animenosekai/Nasse)
![Repo Size](https://img.shields.io/github/repo-size/Animenosekai/Nasse)
![Issues](https://img.shields.io/github/issues/Animenosekai/Nasse)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

You will need Python 3 to use this module

```bash
# vermin output
Minimum required versions: 3.2
Incompatible versions:     2
```

According to Vermin (`--backport typing`), Python 3.2 is needed for the backport of typing but some may say that it is available for python versions higher than 3.0

Always check if your Python version works with `Nasse` before using it in production

## Installing

### Option 1: From PyPI

```bash
pip install Nasse
```

### Option 2: From Git

```bash
pip install git+https://github.com/Animenosekai/Nasse
```

You can check if you successfully installed it by printing out its version:

```bash
$ python -c "import Nasse; print(Nasse.__version__)"
# output:
Nasse v1.0
```

<!--If a CLI version is available-->

or just:

```bash
$ Nasse --version
# output:
Nasse v2.0
```

## Usage

You can use Nasse in Python by importing it in your script:

```python
import Nasse

Nasse.function()
```

### CLI usage

You can use Nasse in other apps by accessing it through the CLI version:

```bash
$ Nasse
output
```

#### Interactive Shell (REPL)

An interactive version of the CLI is also available

```bash
$ Nasse shell
>>> 

```

### As a Python module

#### Class Name

Paragraph explaining the class

#### How to use

Paragraph to explain

#### Cache

Paragraph to explain

#### Example

Examples

```python
from Nasse import function

function()
```

## Deployment

This module is currently in development and might contain bugs.

Feel free to use it in production if you feel like it is suitable for your production even if you may encounter issues.

## Built With

- [dependency](https://dependency-home-page.com) - To do this
- [dependency](https://dependency-home-page.com) - To do this

## Authors

- **Anime no Sekai** - *Initial work* - [Animenosekai](https://github.com/Animenosekai)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for more details

## Acknowledgments

- Thanks to *someone* for helping me with [...]
