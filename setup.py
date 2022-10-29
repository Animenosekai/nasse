from os import path

from setuptools import setup

import nasse

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    readme_description = f.read()

setup(
    name="nasse",
    packages=["nasse"],
    version=nasse.__version_string__(),
    license=nasse.__license__,
    description=nasse.__doc__,
    author=nasse.__author__,
    author_email=nasse.__email__,
    url="https://github.com/Animenosekai/nasse",
    download_url="https://github.com/Animenosekai/nasse/archive/v2.0.tar.gz",
    keywords=["Anime no Sekai", "nasse" "flask", "framework", "web", "web-server", "web-framework"],
    install_requires=[
        "Flask>=2.0",
        "watchdog==2.1.6",
        "bleach==3.3.0",
        "Flask-Compress==1.10.1"
    ],
    extra_requires={
        "gunicorn": ["gunicorn"]
    },
    classifiers=['Development Status :: 5 - Production/Stable', 'License :: OSI Approved :: MIT License', 'Programming Language :: Python :: 3'],
    long_description=readme_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    python_requires='>=3.6, <4',
    entry_points={
        'console_scripts': [
            'nasse = nasse.__main__:main'
        ]
    },
    package_data={
        'nasse': ['LICENSE'],
    },
)
