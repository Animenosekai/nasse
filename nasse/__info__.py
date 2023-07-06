"""Stores information on the current module version"""


# Authors
__author__ = 'Anime no Sekai'
__maintainer__ = 'Anime no Sekai'
__credits__ = ['animenosekai']
__email__ = 'animenosekai.mail@gmail.com'

# Module
__module__ = "Nasse"
__status__ = 'Beta'
__year__ = 2023
__license__ = 'MIT License'

__version_tuple__ = (2, 0, 0)
if __status__ == "Beta":
    __version_tuple__ = (*__version_tuple__, "(beta)")
elif __status__ == "Alpha":
    __version_tuple__ = (*__version_tuple__, "(alpha)")


def __version_string__():
    last = __version_tuple__[-1]
    if isinstance(last, str):
        return '.'.join(str(el) for el in __version_tuple__[:-1]) + __version_tuple__[-1]
    return '.'.join(str(i) for i in __version_tuple__)


__copyright__ = f'Copyright {__year__}, {__module__}'
__version__ = f'{__module__} v{__version_string__()}'
