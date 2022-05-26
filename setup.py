from setuptools import setup
from os import path

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    readme_description = f.read()

setup(
    name="Nasse",
    packages=["nasse"],
    version="1.1",
    license="MIT License",
    description="A web server framework written on top of Flask",
    author="Anime no Sekai",
    author_email="niichannomail@gmail.com",
    url="https://github.com/Animenosekai/nasse",
    download_url="https://github.com/Animenosekai/nasse/archive/v1.1.tar.gz",
    keywords=['python', 'Anime no Sekai', "animenosekai", "Nasse", "flask", "framework", "web", "web-server", "web-framework"],
    install_requires=[
        'typing; python_version<"3.5"',
        "Flask==1.1.2",
        "watchdog==2.1.6",
        "Werkzeug==1.0.1",
        "bleach==3.3.0",
        "gunicorn==20.1.0",
        "Flask-Compress==1.10.1"
    ],
    classifiers=['Development Status :: 5 - Production/Stable', 'License :: OSI Approved :: MIT License', 'Programming Language :: Python :: 3', 'Programming Language :: Python :: 3.2', 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4', 'Programming Language :: Python :: 3.5', 'Programming Language :: Python :: 3.6', 'Programming Language :: Python :: 3.7', 'Programming Language :: Python :: 3.8', 'Programming Language :: Python :: 3.9'],
    long_description=readme_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    python_requires='>=3.4, <4',
    # if a cli version is available
    # entry_points={
    #       'console_scripts': [
    #           'Nasse = Nasse.__main__:main'
    #       ]
    # },
    package_data={
        'nasse': ['LICENSE'],
    },
)
