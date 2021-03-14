import os

__all__ = ["change_dir"]


def change_dir(path):
    def outter_wrapper(func):

        def wrapper(*args, **kwargs):
            origin_dir = os.path.abspath(".")
            os.chdir(path)
            ret = func(*args, **kwargs)
            os.chdir(origin_dir)
            return ret
        return wrapper
    return outter_wrapper
