import flask
from app import app


class HttpError(Exception):

    def __init__(self, status_code, msg):
        self.status_code = status_code
        self.msg = msg


@app.errorhandler(HttpError)
def http_error_handler(error):
    response = flask.jsonify({'Error': error.msg})
    response.status_code = error.status_code
    return response
