#!/usr/bin/env python
#coding=utf-8
from __future__ import absolute_import, division, print_function, with_statement

# from DBUtils.PooledDB import PooledDB
from DBUtils.PersistentDB import PersistentDB
# import functools

import MySQLdb
import MySQLdb.cursors

# import settings

__cache_timeout__ = 600

# 0b 01111111 11111111 11111111 11111111
__MASK__ = 2147483647

DICT_CUR = MySQLdb.cursors.DictCursor
IntegrityError = MySQLdb.IntegrityError

class Connect:
    def __init__(self, dbpool):
        self.conn = dbpool.connect()

    def __enter__(self):
        self.conn.begin()
        return self.conn

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.conn.close()

class Cursor:
    def __init__(self, dbpool):
        self.conn = dbpool.connect()
        self.cursor = dbpool.cursor(self.conn)

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.conn.close()

class MySQLPool():
    def __init__(self, config):
        self.dbpool = PersistentDB(
            creator=MySQLdb,
            db=config['db'],
            host=config['host'],
            port=config['port'],
            user=config['user'],
            passwd=config['passwd'],
            charset=config['charset'],
            maxusage=config['maxusage'],

            # set read & write timeout
            read_timeout=config['read_timeout'],
            write_timeout=config['write_timeout'],
        )

    def cursor(self, conn):
        return conn.cursor(MySQLdb.cursors.DictCursor)

    def connect(self):
        return self.dbpool.connection()

pool_class = {'mysql':MySQLPool}

class MySQL():
    def setup(self, config):
        self.dbpool = MySQLPool(config)

    def combine_kwargs(self, sep=' and ', **kwargs):
        '''
            convert query kwargs to str
        '''
        query_list = []
        for key,value in kwargs.items():
            if isinstance(value, int):
                query_list.append('{}={}'.format(key, value))
            else:
                query_list.append('{}="{}"'.format(key, value))
        return sep.join(query_list)

