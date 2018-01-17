#!/usr/bin/python
__author__ = 'ebmacbp'

from time import sleep
import datetime
import argparse
from xml.etree.ElementTree import parse
import boto
import boto.s3.connection

"""
Set  a logbackconfig.xml file logging level in s3 bucket
example set_s3loglevel.py -e stage -l DEBUG -t 120

if setting to DEBUG, timeout for <timeout>, and then revert to info after debug, otherwise just set to info and quit.
"""


class S3Edit:
    def __init__(self):
        self.timeout = 30
        self.level = 'INFO'
        self.env = 'stage'
        self.lbfilename = 'logback.xml'
        self.logbackconfig_edit = 'logback_edit.xml'
        self.lbconfbucket = None
        self.buckets = {
            'stage': None,
            'prod': None
        }

    # not using these util fx now
    def show_all_buckets(self, conn):
        print "\n all stage buckets:"
        for bucket in conn.get_all_buckets():
                print "{name}\t{created}".format(
                        name = bucket.name,
                        created = bucket.creation_date,
              )

    def ls_bucket(self, lbconf_bucket):
        now = datetime.datetime.now()
        print "\n Current logback config bucket contents at %s:" % now
        for key in lbconf_bucket.list():
            print "{name}\t{size}\t{modified}".format(
                name=key.name,
                size=key.size,
                modified=key.last_modified,
            )

    def update_logging(self):
        now = datetime.datetime.now()
        conn = boto.connect_s3(calling_format=boto.s3.connection.OrdinaryCallingFormat())
        # conn = u.s3_conn()
        lbconf_bucket = conn.get_bucket(self.buckets[self.env])
        key = lbconf_bucket.get_key(self.lbfilename)
        key.get_contents_to_filename(self.lbfilename)

        tree = parse(self.lbfilename)
        root = tree.getroot()
        # print root.tag

        lroot = root.find('root')
        loglevel = lroot.find('level')
        print 'Updating %s at: %s' % (self.lbfilename, now)
        print '\n %s -------------------> : %s ' % (loglevel.attrib, self.level)
        loglevel.set('value', self.level)

        tree.write(self.logbackconfig_edit)

        newLogback_key = lbconf_bucket.new_key(self.lbfilename)
        newLogback_key.set_contents_from_filename(self.logbackconfig_edit)
        # newLogback_key.set_contents_from_string('Hello World!')
        # newLogback_key.set_contents_from_stream()


def main():
    # all = lbconf_bucket.get_all_keys()
    u = S3Edit()
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", help="Level to set logging to, default = INFO",
                        action="store")
    parser.add_argument("-t", "--timeout", help="Time to wait (minutes) before reverting to previous setting",
                        action="store")
    parser.add_argument("-e", "--environment", help="charter environment",
                        action="store")
    flags = parser.parse_args()
    if flags.level:
        u.level = flags.level
    if flags.timeout:
        u.timeout = int(flags.timeout)
    if flags.environment:
        u.environment = flags.environment

    u.update_logging()

    if u.level == 'DEBUG':
        print 'Waiting for timeout of %s, then reverting debug level to info' % u.timeout
        sleep(u.timeout * 60)
        u.level = 'INFO'
        u.update_logging()

    print "Update cycle complete"

if __name__ == '__main__':
    main()
