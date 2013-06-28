#!/usr/bin/python
import xmlrpclib, sys

# this can not unregister any RHEL system and can only restrain the numbers of allocatable systems in sub-organizations to the currently used values. attempting to do otherwise results in an error from the API.
#
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication.
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
# V1.0 by FDewaleyne - 30-08-2012 - versioning started

SATELLITE_URL = "http://satellite.example.com/rpc/api"
SATELLITE_LOGIN = "username"
SATELLITE_PASSWORD = "password"
SYS_ADDONS=['monitoring_entitled','enterprise_entitled','provisioning_entitled']
ALL_SYSADDONS=False #set to true to reset all system addons. use False or True (capital letter matters)
ENTITLEMENTS=[] # put a list of entitlements to have them reset, the labels should be outputed by rhn-satellite-activate
ALL_ENTITLEMENTS=True; # set to True will try to reset ALL entitlements to used values. use with caution. Set to False otherwise (capital letter matters)

client = xmlrpclib.Server(SATELLITE_URL, verbose=0)
key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)
for org in sorted(client.org.listOrgs(key)):
    # this shouldn't bee used on the base org, it will only raise errors.
    if org['id'] > 1:
        if ENTITLEMENTS != [] and not ALL_ENTITLEMENTS:
            for element in client.org.listSoftwareEntitlementsForOrg(key,org['id']):
                if element['label'] in ENTITLEMENTS:
                   try:
                       print "reseting "+element['label']+" to "+str(element['used'])+" regular and "+str(element['used_flex'])+" flex for "+org['name']
                       client.org.setSoftwareEntitlements(key,org['id'],element['label'],element['used'])
                       client.org.setSoftwareFlexEntitlements(key,org['id'],element['label'],element['used_flex'])
                   except:
                       sys.stderr.write("unable to reset "+element['label']+" aka "+element['name']+"\n")
        elif ALL_ENTITLEMENTS:
            for element in client.org.listSoftwareEntitlementsForOrg(key,org['id']):
               try:
                   print "reseting "+element['label']+" to "+str(element['used'])+" regular and "+str(element['used_flex'])+" flex for "+org['name']
                   client.org.setSoftwareEntitlements(key,org['id'],element['label'],element['used'])
                   client.org.setSoftwareFlexEntitlements(key,org['id'],element['label'],element['used_flex'])
               except:
                   sys.stderr.write("unable to reset "+element['label']+" aka "+element['name']+"\n")
        if SYS_ADDONS != [] and not ALL_SYSADDONS:
            for element in client.org.listSystemEntitlementsForOrg(key,org['id']):
                if element['label'] in SYS_ADDONS:
                    try:
                       print "reseting "+element['label']+" to "+str(element['used'])+" for "+org['name']
                       client.org.setSystemEntitlements(key,org['id'],element['label'],element['used'])
                    except:
                       sys.stderr.write("unable to reset "+element['label']+"\n")
        elif ALL_SYSADDONS:
            for element in client.org.listSystemEntitlementsForOrg(key,org['id']):
                try:
                   print "reseting "+element['label']+" to "+str(element['used'])+" for "+org['name']
                   client.org.setSystemEntitlements(key,org['id'],element['label'],element['used'])
                except:
                   sys.stderr.write("unable to reset "+element['label']+"\n")
        print "finished working on "+org['name']

client.auth.logout(key)
