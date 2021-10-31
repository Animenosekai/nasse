from flask import request


def get_ip():
    """
    Retrieves the client IP address from the current request
    """
    # if the server uses a proxy
    if "HTTP_X_FORWARDED_FOR" in request.environ:
        x_forwarded_for = str(
            request.environ['HTTP_X_FORWARDED_FOR']).split(',')[0]
        try:
            if x_forwarded_for.replace('.', '').isdigit():
                return x_forwarded_for
            else:
                return request.remote_addr
        except Exception:
            return request.remote_addr
    else:
        return request.remote_addr
