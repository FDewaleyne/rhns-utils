#!/usr/bin/python

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "dev"
__version__ = "0.01"

###
#
# Script to detect the base channel to attach from the version of RHEL installed. 
#
###
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
###
# NOTE: this version supposes the systems still are subscribed to their channels when listing the channels through certain api calls

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

def get_base(key,systemid):
    """gathers the data on what base channel should be set"""
    global client
    data = client.system.listSubscribableBaseChannels(key,systemid)
    return data['label']

def get_childs(key,systemid):
    """gathers the list of child channels that should be set"""
    data = client.system.listSubscribedChildChannels(key,systemid)
    childs = []
    for channel in data:
        childs.append(channel['label']
    return childs

def set_channels(key,systemid,base,childs):
    """sets the channels or displays an error indicating that the operation failed, then offers to continue or retry. childs needs to be None or a list."""
    global client
    print "Working on system "+str(systemid)
    try:
        client.system.setBaseChannel(key,systemid,base)
        print "\tBase channel restored to "+base
    except e:
        print "unable to reattach the base channel with the reason"
        print str(e) 
        while True:
            answer = raw_input("Do you want to continue, retry or stop? (c, r, [s])").strip()
            if answer == 'c':
                print "Failed to assign to the base channel "+base
                print "continueing with the child channels"
                pass
            elif answer == 'r':
                set_channels(systemid,base,None)
                pass
            else:
                raise
    if childs != None and len(childs) > 0:
        try:
            client.system.setChildChannels(key,systemid,childs)
            print "\tChild channels restored to "+str(childs)
        except e:
            print "unable to reattach the child channels with the reason"
            print str(e)
            while True:
                answer = raw_input("Do you want to continue, retry or stop? (c, r, [s])").strip()
                if answer == 'c':
                    print "Failed to alter this system with child channels"
                    for channel in childs:
                        print "\t"+channel
                    pass
                elif answer == 'r':
                    set_channels(systemid,base,None)
                    pass
                else:
                    raise
    return

def main(version):
    """main function - takes in the options and selects the behaviour"""
    global verbose;
    import optparse
    parser = optparse.OptionParser("%prog [-e \"entitlement_label\" [-s]] [-o orgid] [-l]\n by default displays the general consumption information of the satellite", version=version)
    #parser.add_option("-e", "--entitlement", dest="entitlement", default=None, help="Displays the allocation details of that entitlement for all sub organizations. Use a label ; Does not work pre satellite 5.3")
    #parser.add_option("-s", "--syslist", dest="syslist", action="store_true", default=False, help="Displays the systems in the organization of the user consuming that entitlement at the moment")
    #parser.add_option("-l", "--list", dest="entlist", action="store_true", default=False, help="Displays the entitlements available on the satellite and their names")
    #parser.add_option("-o", "--orgid", dest="orgid",type="int", default=None, help="Number of the organization to report entitlements for")
    parser.add_option("--url", dest="saturl",default=None, help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    parser.add_option("--user", dest="satuser",default=None, help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    parser.add_option("--password", dest="satpwd",default=None, help="password of the user. Will be asked if not given and not in the configuration file.")
    parser.add_option("--org", dest="satorg", default="baseorg", help="name of the organization to use - design the section of the config file to use. Facultative, defaults to %default")
    parser.add_option("-v","--verbose",dest="verbose",default=False,action="store_true",help="activate verbose output")
    (options, args) = parser.parse_args()
    #set verbosity globally
    verbose = options.verbose
#    if options.entlist:
        #key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        #list_entitlements(key)
        #client.auth.logout(key)
    #elif options.entitlement and not options.syslist:
        #key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        #get_entitlement(key,options.entitlement)
        #client.auth.logout(key)
    #elif options.orgid != None:
        #if options.syslist:
            #parser.error("not implemented yet")
        #else:
            #key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
            #org_consumtion(key,options.orgid) 
            #client.auth.logout(key)
    #elif options.syslist:
        #if options.entitlement == None:
            #parser.error('you forgot to select an entitlement')
            #parser.print_help()
        #else:
            #parser.error('not implemented yet')
   ##key = session_init()
            ##client.auth.logout(key)
    #else:
        #key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        #general_consumption(key)
        #client.auth.logout(key)

if __name__ == "__main__":
    main(__version__)

