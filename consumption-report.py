#!/usr/bin/python

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "dev"
__version__ = 0.9

#dumps the consumption of the satellite along with how many subscriptions are unused but assgned to a custom channel
#confirmed to work for 5.4, and 5.3, will not work with 5.2.

# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication.
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
# V0.1 by FDewaleyne - 13-09-2012 - versioning started
# V0.2 by FDewaleyne - 20-09-2012 - more readable output, only displays flex if there is a flex entitlement
# V0.3 by FDewaleyne - 19-10-2012 - changing to allow more features that will gradually be built in
# V0.4 by FDewaleyne - 03-01-2013 - merged the code that lists entitlements with this script, minor display fixes
# V0.5 by FDewaleyne - 22-01-2013 - altered a bit the output and fixed listing options to not display the consumption when used
# V0.6 by FDewaleyne - 17-05-2013 - replaced error tracking, updated test for the flex entitlements
# V0.7 by FDewaleyne - 18-06-2013 - displays used values for all entitlements
# V0.8 by FDewaleyne - 18-06-2013 - update to the session init to be able to take settings in option
# V0.9 by FDewaleyne - 18-06-2013 - handling of organizations added

import xmlrpclib, os, ConfigParser, re, sys, getpass

#global variables
client=None;
SATELLITE_LOGIN=None;
config = ConfigParser.ConfigParser()
config.read(['.satellite', os.path.expanduser('~/.satellite'), '/etc/sysconfig/rhn/satellite'])

# this will initialize a session and return its key.
# for security reason the password is removed from memory before exit, but we want to keep the current username.
def session_init(orgname='baseorg', settings={} ):
    global client;
    global config;
    global SATELLITE_LOGIN;
    if 'url' in settings and not settings['url'] == None:
        SATELLITE_URL = settings['url']
    elif config.has_section('default') and config.has_option('default', 'url'):
        SATELLITE_URL = config.get('default','url')
    else:
        sys.stderr.write("enter the satellite url, such as https://satellite.example.com/rpc/api")
        sys.stderr.write("\n")
        SATELLITE_URL = raw_input().strip()
    #format the url if a part is missing
    if re.match('^http(s)?://[\w\-.]+/rpc/api',SATELLITE_URL) == None:
        if re.search('^http(s)?://', SATELLITE_URL) == None:
            SATELLITE_URL = "https://"+SATELLITE_URL
        if re.search('/rpc/api$', SATELLITE_URL) == None:
            SATELLITE_URL = SATELLITE_URL+"/rpc/api"
    if 'login' in settings and not settings['login'] == None:
        SATELLITE_LOGIN = settings['login']
    elif config.has_section(orgname) and config.has_option(orgname, 'username'):
        SATELLITE_LOGIN = config.get(orgname, 'username')
    else:
        sys.stderr.write("Login details for %s\n\n" % SATELLITE_URL)
        sys.stderr.write("Login: ")
        SATELLITE_LOGIN = raw_input().strip()
    if 'password' in settings and not settings['password'] == None:
        SATELLITE_PASSWORD = settings['password']
    elif config.has_section(orgname) and config.has_option(orgname, 'password'):
        SATELLITE_PASSWORD = config.get(orgname, 'password')
    else:
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
    print("%44s %s %s %s %s %s" % ("Entitlement Label", "   Total  ", " Used ", "Allocated", "Unallocated", "Unused"))
    print("%44s %s %s %s %s %s" % ("-----------------", "----------", "------", "---------", "-----------", "------"))
    for entry in client.org.listSystemEntitlements(key):
        try:
            print("%44s %8s %6s %9s %11s %6s" % (entry['label'], str(entry['unallocated']+entry['allocated']), str(entry['used']), str(entry['allocated']), str(entry['unallocated']),  str(entry['free'])))
        except:
            sys.stderr.write("error handling "+entry['label']+" aka "+entry['name']+", skipping\n")
            continue
    print("\n")
    print("%s" % ("[================================[software   entitlements]================================]"))
    print("%44s %s %s %s %s %s %s" % ("Entitlement Label"," Flex ", "   Total  ", " Used ", "Allocated", "Unallocated", "Unused"))
    print("%44s %s %s %s %s %s %s" % ("-----------------","------", "----------", "------", "---------", "-----------", "------"))
    for entry in client.org.listSoftwareEntitlements(key):
        try:
            print("%44s %6s %8s %6s %9s %11s %6s" % (entry['label'], "", str(entry['unallocated']+entry['allocated']), str(entry['used']) ,str(entry['allocated']), str(entry['unallocated']),  str(entry['free'])))
            if 'used_flex' in entry and 'free_flex' in entry:
                # only print flex entries if they exist
                print("%44s %6s %8s %6s %9s %11s %6s" % (entry['label'], " Flex ", str(entry['unallocated_flex']+entry['allocated_flex']), str(entry['used_flex']) ,str(entry['allocated_flex']), str(entry['unallocated_flex']),  str(entry['free_flex'])))
        except:
            sys.stderr.write("error handling "+entry['label']+" aka "+entry['name']+", skipping.\n")
            continue

def org_consumtion(key,orgid):
    """displays the consumption information for one org"""
    global client;
    #TODO : figure out what Free is for an organization here.
    print("\n")
    print("%s" % ("[=================================[system  entitlements]===========================]"))
    print("%44s %s %s %s %s %s" % ("Entitlement Label", "   Total  ", " Used ", "Allocated", "Unallocated", " Free "))
    print("%44s %s %s %s %s %s" % ("-----------------", "----------", "------", "---------", "-----------", "------"))
    for entry in client.org.listSystemEntitlementsForOrg(key,orgid):
        try:
            print("%44s %8s %6s %9s %11s %6s" % (entry['label'], str(entry['unallocated']+entry['allocated']), str(entry['used']), str(entry['allocated']), str(entry['unallocated']),  str(entry['free'])))
        except:
            sys.stderr.write("error handling "+entry['label']+" aka "+entry['name']+", skipping\n")
            continue
    print("\n")
    print("%s" % ("[================================[software   entitlements]================================]"))
    print("%44s %s %s %s %s %s %s" % ("Entitlement Label"," Flex ", "   Total  ", " Used ", "Allocated", "Unallocated", " Free "))
    print("%44s %s %s %s %s %s %s" % ("-----------------","------", "----------", "------", "---------", "-----------", "------"))
    for entry in client.org.listSoftwareEntitlementsForOrg(key,orgid):
        try:
            print("%44s %6s %8s %6s %9s %11s %6s" % (entry['label'], "", str(entry['unallocated']+entry['allocated']), str(entry['used']) ,str(entry['allocated']), str(entry['unallocated']),  str(entry['free'])))
            if 'used_flex' in entry and 'free_flex' in entry:
                # only print flex entries if they exist
                print("%44s %6s %8s %6s %9s %11s %6s" % (entry['label'], " Flex ", str(entry['unallocated_flex']+entry['allocated_flex']), str(entry['used_flex']) ,str(entry['allocated_flex']), str(entry['unallocated_flex']),  str(entry['free_flex'])))
        except:
            sys.stderr.write("error handling "+entry['label']+" aka "+entry['name']+", skipping.\n")
            continue
   pass


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
            sys.stderr.write("error handling "+entry['label']+" aka "+entry['name']+", skipping\n")
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
            sys.stderr.write("error handling "+entry['label']+" aka "+entry['name']+", skipping.")
            continue


def main(version):
    """main function - takes in the options and selects the behaviour"""
    import optparse
    parser = optparse.OptionParser("usage : %prog [-e \"entitlement_label\" [-s]] [-o orgid] [-l]\n by default displays the general consumption information of the satellite", version=version)
    parser.add_option("-e", "--entitlement", dest="entitlement", default=None, help="Displays the allocation details of that entitlement for all sub organizations. Use a label ; Does not work pre satellite 5.3")
    parser.add_option("-s", "--syslist", dest="syslist", action="store_true", default=False, help="Displays the systems in the organization of the user consuming that entitlement at the moment")
    parser.add_option("-l", "--list", dest="entlist", action="store_true", default=False, help="Displays the entitlements available on the satellite and their names")
    parser.add_option("-o", "--orgid", dest="orgid", default=None, help="Number of the organization to report entitlements for ; not implemented yet")
    parser.add_option("--url", dest="saturl",default=None, help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    parser.add_option("--user", dest="satuser",default=None, help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    parser.add_option("--password", dest="satpwd",default=None, help="password of the user. Will be asked if not given and not in the configuration file.")
    parser.add_option("--org", dest="satorg", default="baseorg", help="name of the organization to use - design the section of the config file to use. Facultative, defaults to %default")
    (options, args) = parser.parse_args()
    if options.entlist:
        key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        list_entitlements(key)
        client.auth.logout(key)
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
    main(__version__)

