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

@util.check_codes
def update_gmtype(_id, group, name):
    return mysql.update_gmtype(_id, group, name)

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
    ap_groups = kwargs.pop('ap_groups', [])
    try:
        mysql.create_message(**kwargs)
    except IntegrityError:
        raise HTTPError(409, reason='duplicate message')
    # 
    # pop ap_groups
    if ap_groups:
        mysql.create_ap_msg_tuple(code, kwargs['groups'], ap_groups)

@util.check_codes
def update_message(_id, **kwargs):
    mysql.update_message(_id, **kwargs)

def delete_message(_id):
    mysql.delete_message(_id)

def get_message(_id):
    return mysql.get_message(_id)

def get_messages(groups, mask, isimg, gmtype, label, expired, pos, nums, ismanager, ap_groups=''):
    '''
        get messages 
        filter  : groups, mask
        position: start , per
    '''
    if expired:
        # days = 0 - expired
        # expired = util.now('%Y-%m-%d', days=days)
        expired = util.now('%Y-%m-%d')
        
    return mysql.get_messages(groups, mask, isimg, gmtype, label, expired, pos, nums, ismanager, ap_groups)

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

# ***************************************
#
# jobs operator
#
# ***************************************
def get_jobs_types():
    '''
        {[{id:'', name:''}]}
    '''
    results = mysql.get_jobs_types()
    results = results if results else {}
    return {item['id']:item['name'] for item in results}

@util.check_codes
def create_jobs_type(name):
    mysql.create_jobs_type(name)

@util.check_codes
def update_jobs_type(_id, name):
    assert _id
    mysql.update_jobs_type(_id, name)

def get_jobs_address():
    '''
    '''
    results = mysql.get_jobs_address()
    results = results if results else {}
    return {item['id']:item['name'] for item in results}
        
@util.check_codes
def create_jobs_address(name):
    mysql.create_jobs_address(name)

@util.check_codes
def update_jobs_address(_id, name):
    assert _id
    mysql.update_jobs_address(_id, name)


def get_recrut_types():
    results = mysql.get_recrut_types()
    results = results if results else {}
    return {item['id']:item['name'] for item in results}

@util.check_codes
def create_recrut_type(_id, name):
    mysql.create_recrut_type(_id, name)

@util.check_codes
def update_recrut_type(_id, name):
    assert _id
    mysql.update_recrut_type(_id, name)


@util.check_codes
def create_job(**kwargs):
    assert 'groups' in kwargs
    return mysql.create_job(**kwargs)

@util.check_codes
def update_job(_id, **kwargs):
    assert _id
    kwargs.pop('id', '')
    mysql.update_job(_id, **kwargs)

def delete_job(_id):
    assert _id
    mysql.delete_job(_id)

def get_job(_id):
    return mysql.get_job(_id)

def get_jobs(groups):
    return mysql.get_jobs(groups)
