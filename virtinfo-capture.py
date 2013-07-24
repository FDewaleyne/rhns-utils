#!/usr/bin/python

###
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
###

import xmlrpclib, sys, getpass, ConfigParser, os, optparse, warnings, stat, re

#global variables
client=None;
SATELLITE_LOGIN=None;
config = ConfigParser.ConfigParser()
config.read(['.satellite', os.path.expanduser('~/.satellite'), '/etc/sysconfig/rhn/satellite'])

# this will initialize a session and return its key.
# for security reason the password is removed from memory before exit, but we want to keep the current username.
def session_init(orgname='baseorg'):
    global client;
    global config;
    global SATELLITE_LOGIN;
    if config.has_section("default") and config.has_section(orgname) and config.has_option(orgname,'username') and config.has_option(orgname,'password') and config.has_option('default','url'):
        SATELLITE_LOGIN = config.get(orgname,'username')
        SATELLITE_PASSWORD = config.get(orgname,'password')
        SATELLITE_URL = config.get('default','url')
    else:
        if not config.has_section("default") and not config.has_option('default','url'):
            sys.stderr.write("enter the satellite url, such as https://satellite.example.com/rpc/api")
            sys.stderr.write("\n")
            SATELLITE_URL = raw_input().strip()
        else:
            SATELLITE_URL = config.get('default','url')
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

def print_systems(key):
    """prints all the systems with their bios info and system addons in use"""
    global client;
    print ""
    print "%50s | %30s | %30s | %s" % ("Profile name", "BIOS vendor", "BIOS info", "System addons")
    print ""
    for system in client.system.listSystems(key):
        dmiinfo = client.system.getDmi(key,system["id"])
        addons = client.system.getEntitlements(key,system["id"])
        try:
            biosvendor = dmiinfo["bios_vendor"]
        except:
            biosvendor = ""
            pass
        try:
            biosinfo = dmiinfo["bios_version"]+" "+dmiinfo["bios_release"]
        except:
            biosinfo = ""
            pass
        entitlements = ""
        for addon in addons:
            entitlements += addon
        print "%50s | %30s | %30s | %s" % (system["name"], biosvendor, biosinfo, entitlements) 
    pass

def main():
    global client;
    parser = optparse.OptionParser("%prog\n Generates a list of systems, displaying their bios information and system addons")
    #parser.add_option("-l", "--list", dest="listing", help="List all channels and quit", action="store_true")
    #parser.add_option("-c", "--channel", dest="channel", help="Label of the channel to querry regeneration for")
    #parser.add_option("-a", "--all", action="store_true",dest="regen_all",help="Causes a global regeneration instead of just one channel")
    #parser.add_option("-f", "--force", action="store_true",dest="force_operation",help="Forces the operation ; can only work if the script is run on the satellite itself",default=False)
    #parser.add_option("--db", action="store_true", dest="use_db", help="Use the database instead of the api ; can only be used from the satellite itself. Implies --force",default=False)
    #parser.add_option("--cleandb", action="store_true", dest="clean_db", help="Get rid of the pending actions before adding the new ones. implies --db and force.", default=False)
    (options, args) = parser.parse_args()
    key = session_init()
    print_systems(key)
    client.auth.logout(key)

#calls start here
if __name__=="__main__":
    main()
