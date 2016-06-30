#!/usr/bin/env python
#coding=utf-8
from __future__ import absolute_import, division, print_function, with_statement
# import functools
# import datetime
# 
# import util


# 0b 01111111 11111111 11111111 11111111
__MASK__ = 2147483647

# cache = CacheManager(cache_regions= {'short_term':{'type':'memory', 
#                                                    'expire':__cache_timeout__}})

from db.mysql import (Connect, Cursor, MySQL, 
                      DICT_CUR, IntegrityError)

class Manager_DB(MySQL):
    def get_manager(self, user, password):
        with Cursor(self.dbpool) as cur:
            sql = 'select * from bd_manager where name="{}"'.format(user)
            if password:
                sql = sql + ' and password="{}"'.format(password)

            cur.execute(sql)
            return cur.fetchone()


db = Manager_DB()
from config import settings
db.setup(settings['db_bidong'])
