from os import path

from setuptools import setup

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    readme_description = f.read()

setup(
    name="nasse",
    packages=["nasse"],
    version="2.0.0",
    license="MIT License",
    description="""A web server framework written on top of Flask""",
    author="Animenosekai",
    author_email="niichannomail@gmail.com",
    url="https://github.com/Animenosekai/nasse",
    download_url="https://github.com/Animenosekai/nasse/archive/v2.0.tar.gz",
    keywords=["Anime no Sekai", "nasse" "flask", "framework", "web", "web-server", "web-framework"],
    install_requires=[
        "Flask>=2.2.2,<3",
        "nh3>=0.2.14",
        "Flask_Compress>=1.10.1,<2",
        "watchdog>=2.1.6,<3",
        "rich>=13.0.0,<14",
        "requests>=2,<3",
        "miko>=1.0,<2"
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
            'nasse = nasse.__main__:entry'
        ]
    },
    package_data={
        'nasse': ['LICENSE'],
    },
)
