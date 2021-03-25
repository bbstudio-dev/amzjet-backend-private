import functools
import pymongo
import logging
import time


# Gracefully handles a reconnection event in PyMongo.
# Based on this gist: https://gist.github.com/anthonywu/1696591
def retry_on_reconnect(mongo_func, max_retries=3):
    for attempt in xrange(max_retries):
        try:
            return mongo_func()
        except pymongo.errors.AutoReconnect as e:
            wait_t = 0.5 * pow(2, attempt)  # exponential back off
            logging.warning(
                "PyMongo auto-reconnecting... %s. Waiting %.1f seconds.",
                str(e), wait_t)
            time.sleep(wait_t)


# Automatically retries the wrapped function on a reconnection event.
# Usage:
#
# @auto_reconnect
# def do_something_with_mongo(db):
#   db.some_collection.find({...})
def auto_reconnect(mongo_func):
    @functools.wraps(mongo_func)
    def wrapper(*args, **kwargs):
        retry_on_reconnect(lambda: mongo_func(*args, **kwargs))
    return wrapper
