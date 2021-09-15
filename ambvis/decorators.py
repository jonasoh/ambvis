import inspect

from ambvis import globals


def removeprefix(s, prefix):
    s = str(s)
    if s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s[:]


def public_route(f):
    '''decorator for routes that should be accessible without being logged in'''
    globals.public_routes.add(f.__name__)

    caller = inspect.currentframe().f_back
    calling_module = caller.f_globals['__name__']
    calling_module = removeprefix(calling_module, 'ambvis.')
    globals.public_routes.add(calling_module + '.' + f.__name__)
    return f


def not_while_running(f):
    '''decorator for routes that should be inaccessible while an experiment is running'''
    globals.not_while_running.add(f.__name__)

    caller = inspect.currentframe().f_back
    calling_module = caller.f_globals['__name__']
    calling_module = removeprefix(calling_module, 'ambvis.')
    globals.not_while_running.add(calling_module + '.' + f.__name__)
    return f
