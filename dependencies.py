from fastapi import Request


def get_logger(request: Request):
    return request.app.state.logger
