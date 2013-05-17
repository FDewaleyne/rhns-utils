#!/usr/bin/python

#version 0.5

#dumps the consumption of the satellite along with how many subscriptions are unused but assgned to a custom channel
#confirmed to work for 5.4, should work with 5.3, will not work with 5.2.

# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication.
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
# V0.1 by FDewaleyne - 13-09-2012 - versioning started
# V0.2 by FDewaleyne - 20-09-2012 - more readable output, only displays flex if there is a flex entitlement
# V0.3 by FDewaleyne - 19-10-2012 - changing to allow more features that will gradually be built in
# V0.4 by FDewaleyne - 03-01-2013 - merged the code that lists entitlements with this script, minor display fixes
# V0.5 by FDewaleyne - 22-01-2013 - altered a bit the output and fixed listing options to not display the consumption when used

import xmlrpclib, os, ConfigParser, warnings

#global variables
client=None;
SATELLITE_LOGIN=None;
key=None;
config = ConfigParser.ConfigParser()
config.read(['.satellite', os.path.expanduser('~/.satellite'), '/etc/sysconfig/rhn/satellite'])

# this will initialize a session and return its key.
# for security reason the password is removed from memory before exit, but we want to keep the current username.
# to set the values, create a config file .satellite in the running folder or in your home folder or in /etc/sysconfig/rhn/satellite with lines :
# [baseorg]
# url = http://satellite.fqdn/rpc/api
# username = satadmin
# password = password
# no setting is mandatory and  missing elements will be requested when running.
def session_init(orgname='baseorg'):
    import getpass, sys
    global client;
    global config;
    global SATELLITE_LOGIN;
    if config.has_section(orgname) and config.has_option(orgname,'username') and config.has_option(orgname,'password') and config.has_option('baseorg','url'):
        SATELLITE_LOGIN = config.get(orgname,'username')
        SATELLITE_PASSWORD = config.get(orgname,'password')
        SATELLITE_URL = config.get('baseorg','url')
    else:
        if not config.has_option('baseorg','url'):
            sys.stderr.write("enter the satellite url, such as https://satellite.example.com/rpc/api")
            sys.stderr.write("\n")
            SATELLITE_URL = raw_input().strip()
        else:
            SATELLITE_URL = config.get('baseorg','url')
        sys.stderr.write("Login details for %s\n\n" % SATELLITE_URL)
        sys.stderr.write("Login: ")
        SATELLITE_LOGIN = raw_input().strip()
        # Get password for the user
        SATELLITE_PASSWORD = getpass.getpass(prompt="Password: ")
        sys.stderr.write("\n")
    #inits the connection
    client = xmlrpclib.Server(SATELLITE_URL, verbose=0)
    key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)
    # removes the password from memory
    del SATELLITE_PASSWORD
    return key

def general_consumption(key):
    """ displays the general consumtion information of the satellite """
    global client;
    print("\n")
    print("%s" % ("[=================================[system  entitlements]===========================]"))
    print("%44s %s %s %s %s" % ("Entitlement Label", "   Total  ", "Allocated", "Unallocated", "Unused"))
    print("%44s %s %s %s %s" % ("-----------------", "----------", "---------", "-----------", "------"))
    for entry in client.org.listSystemEntitlements(key):
        try:
            print("%44s %8s %9s %11s %6s" % (entry['label'], str(entry['unallocated']+entry['allocated']), str(entry['allocated']), str(entry['unallocated']),  str(entry['free'])))
        except:
            warnings.warn("error handling "+entry['label']+" aka "+entry['name']+", skipping")
            continue
    print("\n")
    print("%s" % ("[================================[software   entitlements]================================]"))
    print("%44s %s %s %s %s %s" % ("Entitlement Label"," Flex ", "   Total  ", "Allocated", "Unallocated", "Unused"))
    print("%44s %s %s %s %s %s" % ("-----------------","------", "----------", "---------", "-----------", "------"))
    print "second line is for the flex values"
    for entry in client.org.listSoftwareEntitlements(key):
        try:
            print("%44s %6s %8s %9s %11s %6s" % (entry['label'], "", str(entry['unallocated']+entry['allocated']), str(entry['allocated']), str(entry['unallocated']),  str(entry['free'])))
            if entry['used_flex'] or entry['free_flex']:
                # only print flex entries if they exist
                print("%44s %6s %8s %9s %11s %6s" % (entry['label'], " Flex ", str(entry['unallocated_flex']+entry['allocated_flex']), str(entry['allocated_flex']), str(entry['unallocated_flex']),  str(entry['free_flex'])))
        except:
            warnings.warn("error handling "+entry['label']+" aka "+entry['name']+", skipping.")
            continue


def list_entitlements(key):
    """ displays the list of entitlements for the satellite """
    global client;
    print("\n")
    print("%s" % ("[=================================[system  entitlements]===========================]"))
    print("%44s %s %s " % ("Entitlement Label", "|", " Entitlement Name"))
    print("%44s %s " % ("-----------------", "------------------------------------"))
    for entry in client.org.listSystemEntitlements(key):
        try:
            print("%44s %s %s" % (entry['label'], "|", entry['name']))
        except:
            warnings.warn("error handling "+entry['label']+" aka "+entry['name']+", skipping")
            continue
    print("\n")
    print("%s" % ("[================================[software   entitlements]================================]"))
    print("%44s %s %s " % ("Entitlement Label","|"," Entitlement Name "))
    print("%44s %s %s " % ("-----------------","|","------------------------------------------"))
    for entry in client.org.listSoftwareEntitlements(key):
        try:
            print("%44s %s %s" % (entry['label'], "|", entry['name']))
            #if entry['used_flex'] or entry['free_flex']:
            #    # only print flex entries if they exist
            #    print("%44s %6s %8s %9s %11s %6s" % (entry['label'], " Flex ", str(entry['unallocated_flex']+entry['allocated_flex']), str(entry['allocated_flex']), str(entry['unallocated_flex']),  str(entry['free_flex'])))
        except:
            warnings.warn("error handling "+entry['label']+" aka "+entry['name']+", skipping.")
            continue


def main():
    """main function - takes in the options and selects the behaviour"""
    import optparse
    parser = optparse.OptionParser("usage : %prog [-e \"entitlement_label\" [-s]] [-o orgid] [-l]\n by default displays the general consumption information of the satellite")
    parser.add_option("-e", "--entitlement", dest="entitlement", default=None, help="Displays the allocation details of that entitlement for all sub organizations. Use a label ; Does not work pre satellite 5.3")
    parser.add_option("-s", "--syslist", dest="syslist", action="store_true", default=False, help="Displays the systems in the organization of the user consuming that entitlement at the moment")
    parser.add_option("-l", "--list", dest="entlist", action="store_true", default=False, help="Displays the entitlements available on the satellite and their names")
    parser.add_option("-o", "--org", dest="orgid", default=None, help="Displays the consumption and allocation for one org ID only.")
    (options, args) = parser.parse_args()
    if options.entlist:
        key = session_init()
        list_entitlements(key)
        client.auth.logout(key)
    elif not options.orgid == None:
        parser.error('not implemented yet')
    elif options.syslist:
        if options.entitlement == None:
            parser.error('you forgot to select an entitlement')
            parser.print_help()
        else:
            parser.error('not implemented yet')
            #key = session_init()
            #client.auth.logout(key)
    else:
        key = session_init()
        general_consumption(key)
        client.auth.logout(key)

if __name__ == "__main__":
    main()

