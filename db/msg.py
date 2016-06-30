#!/usr/bin/env python
#coding=utf-8
from __future__ import absolute_import, division, print_function, with_statement
# import functools
# import datetime
# 
# import util
from tornado.log import access_log


# 0b 01111111 11111111 11111111 11111111
__MASK__ = 2147483647

# cache = CacheManager(cache_regions= {'short_term':{'type':'memory', 
#                                                    'expire':__cache_timeout__}})

from db.mysql import (Connect, Cursor, MySQL, 
                      DICT_CUR, IntegrityError)

class MSG_DB(MySQL):
    def get_manager(self, user, password):
        with Cursor(self.dbpool) as cur:
            sql = 'select * from bd_manager where user="{}"'.format(user)
            if password:
                sql = sql + ' and password="{}"'.format(password)

            cur.execute(sql)
            return cur.fetchall()

    # ********************************************
    # group message type operator 
    # ********************************************
    def create_gmtype(self, group, name):
        with Connect(self.dbpool) as conn:
            cur = conn.cursor(DICT_CUR)
            sql = 'insert into gmtype (group, name) values({}, "{}")'.format(group, name)
            cur.execute(sql)
            conn.commit()

    def get_gmtype(self, group, _id):
        with Cursor(self.dbpool) as cur:
            sql = 'select * from gmtype where id = {} and groups = {}'.format(_id, group)
            cur.execute(sql)
            return cur.fetchone()

    def get_gmtypes(self, group):
        with Cursor(self.dbpool) as cur:
            sql = 'select * from gmtype where groups = {} order by id'.format(group)
            cur.execute(sql)
            results = cur.fetchall()
            return results if results else []

    def delete_gmtype(self, group, _id):
        with Connect(self.dbpool) as conn:
            cur = conn.cursor(DICT_CUR)
            sql = 'delete from gmtype where id = {} and groups = {}'.format(_id, group)
            cur.execute(sql)
            conn.commit()

    # ********************************************
    # message operator
    # ********************************************
    def create_message(self, **kwargs):
        '''
            create new message
            each message distinguished by id [md5(groups, title, subtitle, content)]
        '''
        with Connect(self.dbpool) as conn:
            cur = conn.cursor(DICT_CUR)
            key_str = ', '.join(kwargs.keys())
            value_str = ', '.join(["'{}'".format(item) for item in kwargs.values()])
            sql = 'insert into message ({}) values({})'.format(key_str, value_str)
            cur.execute(sql)
            conn.commit()

    def update_message(self, _id, **kwargs):
        '''
            update message's property
        '''
        with Connect(self.dbpool) as conn:
            cur = conn.cursor(DICT_CUR)
            modify_str = ', '.join("{} = '{}'".format(key,value) for key,value in kwargs.iteritems())
            sql = 'update message set {} where id = "{}"'.format(modify_str, _id)
            cur.execute(sql)
            conn.commit()

    def delete_message(self, _id):
        '''
            delete special message
        '''
        with Connect(self.dbpool) as conn:
            cur = conn.cursor(DICT_CUR)
            sql = 'delete from message where id = "{}"'.format(_id)
            cur.execute(sql)
            conn.commit()

    def get_message(self, _id):
        '''
            get special message
        '''
        with Cursor(self.dbpool) as cur:
            # sql = '''select message.*, section.name as section from message, section 
            # where message.id="{}" and message.section = section.id'''.format(_id)
            sql = 'select *from message where id="{}"'.format(_id)
            cur.execute(sql)
            return cur.fetchone()

    def get_messages(self, groups, mask, isimg, gmtype, label, pos, nums=10):
        '''
            id title subtitle section mask author groups status ctime content image
            get groups's messages excelpt content filed
            order by ctime desc 
            groups : message's group
            mask : message type (combine by bit operator)
            pos : where to get special messages
            isimg : search messages which image <> '';
        '''
        with Cursor(self.dbpool) as cur:
            # filters = 'message.id, message.title, message.subtitle, message.mask, message.author, message.groups, message.status, message.ctime, message.image'
            # sql = ''
            # gmtype = 'message.gmtype = {} and '.format(gmtype) if gmtype else ''
            # isimg = 'message.image <> "" and '.format(isimg) if isimg else ''
            # label = " and label like'%{}%'".format(label) if label else ''

            # if mask:
            #     sql = '''select {}, section.name as section from message, section 
            #     where {}{}message.groups = {} and message.mask & {} = {} and 
            #     message.section = section.id order by message.status desc, message.ctime desc limit {},{}
            #     '''.format(filters, gmtype, isimg, groups, __MASK__, mask, pos, nums)
            # else:
            #     # doesn't check message type
            #     sql = '''select {}, section.name as section from message, section 
            #     where {}{}message.groups = {} and message.section = section.id{} 
            #     order by message.status desc, message.ctime desc limit {},{}
            #     '''.format(filters, gmtype, isimg, groups, label, pos, nums)
            filters = 'id, title, subtitle, mask, author, groups, status, ctime, image'
            sql = ''
            gmtype = 'gmtype = {} and '.format(gmtype) if gmtype else ''
            isimg = 'image <> "" and '.format(isimg) if isimg else ''
            label = " and label like'%{}%'".format(label) if label else ''

            if mask:
                sql = '''select {} from message where {}{} groups = {} and mask & {} = {} 
                order by message.status desc, message.ctime desc limit {},{}
                '''.format(filters, gmtype, isimg, groups, __MASK__, mask, pos, nums)
            else:
                # doesn't check message type
                sql = '''select {}, section.name as section from message, section 
                where {}{}message.groups = {} and message.section = section.id{} 
                order by message.status desc, message.ctime desc limit {},{}
                '''.format(filters, gmtype, isimg, groups, label, pos, nums)

            cur.execute(sql)
            results = cur.fetchall()
            return results if results else []


db = MSG_DB()
from config import settings
db.setup(settings['db_cms'])
