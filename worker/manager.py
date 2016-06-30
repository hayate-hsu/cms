'''
'''
# from tornado.web import HTTPError
# import # datetime
# import # math

_MANAGER_CACHE_ = {}

# from db import mongo, mysql
from db.manager import db as mysql

def check_location(manager):
    '''
        get manager's location.
        if found in cached:
            return cached value 
        else:
            query from db
            write query result to cache
    '''
    record = _MANAGER_CACHE_.get(manager, '')
    if record:
        return record['_location']

    # can't found record, query from database
    record = get_manager(manager)
    
    if record:
        record.pop('password')
        _location = record['_location']
        record['location'] = _location.split(',')[-1]
        _MANAGER_CACHE_['manager'] = record

        return record['_location']

    raise ValueError('can\'t found {}\'s group'.format(manager))

def get_manager(user, password=''):
    '''
    '''
    return mysql.get_manager(user, password)

