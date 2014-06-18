#!/usr/bin/python

SATELLITE="rhns56-6.gsslab.fab.redhat.com"
USER="satadmin"
PWD="redhat"
#channel to copy from
SOURCE="EPEL-WS-6"
#channel to create (with / if using a child channel, one layer only)
DESTINATION="magic-6/magic-epel-6"
import datetime
#dates to and from
FROM_DATE=datetime.date(2001,01,01) # first january 2001
TO_DATE=datetime.date(2013,02,21) #release of rhel 6.4


url = "https://%s/rpc/api" % (SATELLITE)

import xmlrpclib
client = xmlrpclib.Server(url)
key = client.auth.login(USER,PWD)
del PWD # we don't need that anyore

# split parent and channel in destination, create destination. parent must exist if used
channels = DESTINATION.split('/')
if len(channels) == 1:
    # one channel only
else:
    # two channels
#copy packages & erratas per group of 100

client.auth.logout(key)
