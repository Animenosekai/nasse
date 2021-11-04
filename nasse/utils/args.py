import sys

# from nasse import exceptions


class NoDefault:
    pass


class _Args:
    @property
    def args(self):
        return sys.argv

    def get(self, key, default=NoDefault()):
        if isinstance(key, (list, tuple, set)):
            for k in key:
                if k not in sys.argv:
                    continue
                index = sys.argv.index(k)
                if len(sys.argv) <= index:
                    continue
                return sys.argv[index + 1]
            if isinstance(default, NoDefault):
                raise ValueError(
                    "{key} is a required command argument".format(key=key))
            else:
                return default

        key = str(key)
        if key not in sys.argv:
            if isinstance(default, NoDefault):
                raise ValueError(
                    "{key} is a required command argument".format(key=key))
            else:
                return default
        index = sys.argv.index(key)
        if len(sys.argv) <= index:
            if isinstance(default, NoDefault):
                raise ValueError(
                    "{key} is a required command argument".format(key=key))
            else:
                return default
        return sys.argv[index + 1]

    def exists(self, key):
        if isinstance(key, (list, tuple, set)):
            for k in key:
                if k in sys.argv:
                    return True
            return False
        return str(key) in sys.argv


Args = _Args()
