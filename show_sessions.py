#!/usr/bin/env python
'''
Session manipulation


show all sessions
delete all sessions
'''

import site
#site.addsitedir('/path/to/virtualenv/lib/python2.6/site-packages')
#site.addsitedir('/path/to/project-settings')

import settings
import psycopg2
from datetime import datetime
import getopt
import sys

from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session


progname = sys.argv[0]
do_list_all = False
do_clean_expired = False
do_list = False
do_delete = False
do_logout = False
do_user = False
do_logged_in = False
do_summary = False
shortname = None
user = None


def dump_sessions ():
    global do_list_all
#    ss = Session.objects.filter (expire_date__gt = datetime.today ())
    ss = Session.objects.all ()

    for session in ss:
        if do_list_all or (datetime.today () < session.expire_date):
            sys.stdout.write ('\n')
            sys.stdout.write ('%s\n' % session.session_key)

            sstore = SessionStore (session.session_key)
            for key, val in sstore.items ():
                if key == '_auth_user_id':
                    sys.stdout.write ('\tkey[%s] val[%s] name[%s]\n' % (
                            key, val, User.objects.get (pk = int(val)).username))
                else:
                    sys.stdout.write ('\tkey[%s] val[%s]\n' % (key, val))
            sys.stdout.write ('\texpire-date[%s]\n' % session.expire_date)
            sys.stdout.write ('\texpiry-age[%d]\n' % sstore.get_expiry_age ())
            sys.stdout.write ('\n')

def summarize_sessions (pname=None):
    num_sessions = 0
    num_current_sessions = 0
    expired_sessions = 0
    num_attendees = 0
    ss = Session.objects.all ()

    for session in ss:
        num_sessions += 1
        if datetime.today () < session.expire_date:
            sstore = SessionStore (session.session_key)
            if '_auth_user_id' in sstore.keys ():
                num_current_sessions += 1
                if pname and 'pname' in sstore.keys () and pname == sstore['pname']:
                    num_attendees += 1
        else:
            expired_sessions += 1

    sys.stdout.write ('Sessions[%d] logged-in[%d] expired[%d]\n' %
                      (num_sessions, num_current_sessions, expired_sessions))
    if pname:
        sys.stdout.write ('%s had %d attendees\n' % (pname, num_attendees))

def show_logged_in_sessions ():
    ss = Session.objects.all ()

    for session in ss:
        sstore = SessionStore (session.session_key)
        if '_auth_user_id' in sstore.keys ():
            for key, val in sstore.items ():
                if '_auth_user_id' == key:
                    sys.stdout.write ('\tkey[%s] val[%s] type(val)[%s] ' % (key, val, type(val)))
                    sys.stdout.write ('name[%s]\n' % User.objects.get (pk = val).username)
                else:
                    sys.stdout.write ('\tkey[%s] val[%s]\n' % (key, val))
            sys.stdout.write ('\texpire-date[%s]\n' % session.expire_date)
            sys.stdout.write ('\texpiry-age[%d]\n' % sstore.get_expiry_age ())
            sys.stdout.write ('\n')


def show_sessions_for_user (user):
    ss = Session.objects.all ()

    sys.stdout.write ('type (user) is [%s]; user is [%s]\n' % (type(user), user))

    for session in ss:
        sstore = SessionStore (session.session_key)
        if '_auth_user_id' in sstore.keys ():
            sys.stdout.write ('_auth_user_id is in sstore.keys\n')
            sys.stdout.write ('sstore[_auth_user_id] is %s; type is %s\n' %
                              (sstore['_auth_user_id'], type (sstore['_auth_user_id'])))

            if int(user) == sstore['_auth_user_id']:
                for key, val in sstore.items ():
                    if '_auth_user_id' == key:
                        sys.stdout.write ('\tkey[%s] val[%s] ' % (key, val))
                        sys.stdout.write ('name[%s]\n' % User.objects.get (pk = val).username)
                    else:
                        sys.stdout.write ('\tkey[%s] val[%s]\n' % (key, val))
                sys.stdout.write ('\texpire-date[%s]\n' % session.expire_date)
                sys.stdout.write ('\texpiry-age[%d]\n' % sstore.get_expiry_age ())
                sys.stdout.write ('\n')

def delete_all_sessions ():
    '''
    Delete all sessions from django_session table
    '''
    ss = Session.objects.all ()
    for session in ss:
        session.delete ()

def logout_all_sessions ():
    '''
    Logout all the sessions

    i.e., remove the _auth_user_id and other keys
    from the session store
    _and_ blow away all the cookiejars
    '''
    ss = Session.objects.all ()
    for session in ss:
        if datetime.today () < session.expire_date:
            sstore = SessionStore (session.session_key)
            if '_auth_user_id' in sstore.keys ():
                del sstore['_auth_user_id']

            if '_auth_user_backend' in sstore.keys ():
                del sstore['_auth_user_backend']

            if 'pname' in sstore.keys():
                del sstore['pname']

            sstore.save ()


def clean_expired ():
    '''
    remove the expired session entries
    '''
    ss = Session.objects.all ()
    for session in ss:
        if datetime.today () > session.expire_date:
            session.delete ()


def usage (exit_code):
    global progname

    sys.stderr.write ('Usage:  %s [-a][-l][-g][-d][-o][-u userid][-s][-n shortname]\n' % progname)
    sys.stderr.write ('\t-a\tlist all sessions\n')
    sys.stderr.write ('\t-c\tclean expired sessions - remove expired sessions from DB\n')
    sys.stderr.write ('\t-l\tlist current sessions\n')
    sys.stderr.write ('\t-g\tlist logged-in sessions\n')
    sys.stderr.write ('\t-o\tlogout sessions\n')
    sys.stderr.write ('\t-u uid\tshow sessions for user uid\n')
    sys.stderr.write ('\t-d\tdelete sessions\n')
    sys.stderr.write ('\t-s\tsummarize num sessions or num attendees for name\n')
    sys.stderr.write ('\t-nname\tsummarize attendees for session "name"\n')
    sys.exit (exit_code)


if 2 > len (sys.argv):
    usage (1)

opts, args = getopt.getopt (sys.argv[1:], 'aclgdou:sn:')
for opt, arg in opts:
    if '-a' == opt:
        do_list_all = True
        do_list = True
    if '-c' == opt:
        do_clean_expired = True
    if '-l' == opt:
        do_list = True
    if '-g' == opt:
        do_logged_in = True
    if '-d' == opt:
        do_delete = True
    if '-o' == opt:
        do_logout = True
    if '-u' == opt:
        do_user = True
        user = arg
    if '-s' == opt:
        do_summary = True
    if '-n' == opt:
        shortname = arg


if do_list:
    dump_sessions ()

if do_summary:
    summarize_sessions (shortname)

if do_logout:
    logout_all_sessions ()

if do_delete:
    delete_all_sessions ()

if do_logged_in:
    show_logged_in_sessions ()

if do_user:
    show_sessions_for_user (user)

if do_clean_expired:
    clean_expired ()

