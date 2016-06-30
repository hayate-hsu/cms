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

class Example_DB(MySQL):
    def query(self, table, **kwargs):
        '''
            query special records in table
        '''
        with Cursor(self.dbpool) as cur:
            query_str = self.combine_kwargs(**kwargs)
            sql = 'select * from {} where {}'.format(table, query_str)
            cur.execute(sql)

            return cur.fetchall()

    def query2(self, table, **kwargs):
        '''
            query special records in table
            first commit connection, refresh records
        '''
        with Connect(self.dbpool) as conn:
            conn.commit()
            cur = conn.cursor(DICT_CUR)
            query_str = self.combine_kwargs(**kwargs)
            sql = 'select * from {} where {}'.format(table, query_str)
            cur.execute(sql)

            return cur.fetchall()

    def insert(self, table, **kwargs):
        '''
            insert new records
        '''
        with Connect(self.dbpool) as conn:
            cur = conn.cursor(DICT_CUR)
            keys,values = kwargs.keys(),kwargs.values()
            keys = ['"{}"'.format(key) for key in keys]
            values = ['"{}"'.format(value) for value in values]
            keys, values = ', '.join(keys), ', '.join(values)

            sql = 'insert into {} ({}) values({})'.format(table, keys, values)
            cur.execute(sql)
            conn.commit()

    def update(self, table, filters, **kwargs):
        '''
            update records's value (**kwargs) where matched filters
        '''
        with Connect(self.dbpool) as conn:
            cur = conn.cursor(DICT_CUR)
            filters = self.combine_kwargs(filters)
            modify_str = self.combine_kwargs(', ', **kwargs)

            sql = 'update {} set {} where {}'.format(table, modify_str, filters)
            cur.execute(sql)
            conn.commit()

    def delete(self, table, filters):
        '''
            delete records where matched filters
        '''
        with Connect(self.dbpool) as conn:
            if not filters:
                return

            cur = conn.cursor(DICT_CUR)
            filters = self.combine_kwargs(filters)

            sql = 'delete from {} where {}'.format(table, filters)
            cur.execute(sql)
            conn.commit()

