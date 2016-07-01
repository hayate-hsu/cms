'''
    id = Column('id', INTEGER(),
                primary_key=True, nullable=False, doc='increment id')
    Account manage module
'''
from tornado.web import HTTPError
# import # datetime
# import # math

from MySQLdb import (IntegrityError)

from common import util

# from db import mongo, mysql
from db.msg import db as mysql
# import gridfs instance
from db.file import fs

# ****************************************
#  group message type
#
#  diffenert group has its own message type
# ****************************************
@util.check_codes
def create_gmtype(group, _type):
    try:
        mysql.create_gmtype(group, _type)
    except IntegrityError:
        raise HTTPError(409, reason='name has been existed')

def get_gmtype(group, _id):
    return mysql.get_gmtype(group, _id)

def get_gmtypes(group):
    return mysql.get_gmtypes(group)

def delete_gmtype(group, _id):
    mysql.delete_gmtype(group, _id)

# # **************************************
# #
# # message type (used for all message)
# #
# # **************************************
# @util.check_codes
# def add_section(name):
#     try:
#         mysql.add_section(name)
#     except IntegrityError:
#         raise HTTPError(409, reason='duplicate message type')
# 
# def delete_section(_id):
#     mysql.delete_section(_id)
# 
# def get_section(_id):
#     return mysql.get_section(_id)
# 
# def get_sections():
#     return mysql.get_sections()

# ***************************************
#
# message operator
#
# ***************************************
@util.check_codes
def create_message(**kwargs):
    # generate message's unique id (groups, title, subtitle, content)
    code = util.md5(kwargs['groups'], kwargs['title'], kwargs['subtitle'], kwargs['content']) 
    code = code.hexdigest()
    kwargs['id'] = code
    try:
        mysql.create_message(**kwargs)
    except IntegrityError:
        raise HTTPError(409, reason='duplicate message')

@util.check_codes
def update_message(_id, **kwargs):
    mysql.update_message(_id, **kwargs)

def delete_message(_id):
    mysql.delete_message(_id)

def get_message(_id):
    return mysql.get_message(_id)

def get_messages(groups, mask, isimg, gmtype, label, pos, nums):
    '''
        get messages 
        filter  : groups, mask
        position: start , per
    '''
    return mysql.get_messages(groups, mask, isimg, gmtype, label, pos, nums)

def create_file(data, **kwargs):
    '''
        kwargs:
            _id
            filename
            content_type
            # chunk_size
            # encoding
    '''
    fs.put(data, **kwargs)

def get_file(_id):
    '''
    '''
    gridout = fs.get(_id)
    if not gridout:
        raise HTTPError(404)
    return gridout