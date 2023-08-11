"""
A utility to retrieve the IP address of the client
"""
import flask


def get_ip():
    """
    Retrieves the client IP address from the current request
    """
    # if the server uses a proxy
    if "HTTP_X_FORWARDED_FOR" in flask.request.environ:
        x_forwarded_for = str(flask.request.environ['HTTP_X_FORWARDED_FOR']).split(',')[0]
        try:
            if x_forwarded_for.replace('.', '').isdigit():
                return x_forwarded_for
            else:
                return flask.request.remote_addr
        except Exception:
            return flask.request.remote_addr
    else:
        return flask.request.remote_addr
