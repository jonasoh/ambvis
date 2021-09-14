import inspect

import globals


def public_route(f):
    '''decorator for routes that should be accessible without being logged in'''
    caller = inspect.currentframe().f_back
    globals.public_routes.add(f.__name__)
    globals.public_routes.add(caller.f_globals['__name__'] + '.' + f.__name__)
    return f


def not_while_running(f):
    '''decorator for routes that should be inaccessible while an experiment is running'''
    caller = inspect.currentframe().f_back
    globals.not_while_running.add(f.__name__)
    globals.not_while_running.add(caller.f_globals['__name__'] + '.' + f.__name__)
    return f
