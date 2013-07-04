#!/usr/bin/python

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "dev"

import xmlrpclib, sys, getpass, ConfigParser, os, optparse, re
# import stat as well for the repodata file time edit
import stat

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

def print_snapshots(key, sysid):
    """prints the list of the snapshots for a given sysid"""
    global client;
    print "The system "+str(sysid)+" has the following snapshots:"
    print " %20s | %40s | %s " % ("snapshot id", "channel", "reason" )
    for snapshot in client.system.provisioning.snapshot.listSnapshots(key,sysid):
        print " %20s | %40s | %s" % (str(snapshot['id']), snapshot['channels'][0], snapshot['reason']+" "+snapshot['Invalid_reason']  )
        if len(snapshot['channels']) > 1 :
            snapshot['channels'].pop(0)
            for channel in snapshot['channels']:
                print " %20s | %40s |" % ( "", channel)
    pass

def print_packages(key, snapid):
    """prints the list of packages in the snapshot"""
    global client;
    print " %40s | %20s | %10s |  %5s |  %8s" % ( "Name", "Version", "Release", "Epoch", "Arch")
    for package in client.system.provisioning.snapshot.listSnapshotPackages(key,snapid):
        print " %40s | %20s | %10s |  %5s |  %8s" % ( package['name'], package['version'], package['release'], package['epoch'], package['arch'])
    pass


def main(version):
    global client;
    parser = optparse.OptionParser("%prog [-l] --id", version=version)
    parser.add_option("-l", "--list", dest="listing", help="List all snapshots and quit", action="store_true")
    parser.add_option("--id", dest="id", type="int", help="system id or snapshot id to use (required)")
    #this next 4 are required for the connection
    connect_group = OptionGroup(parser, "Connection options","Not required unless you want to bypass the details of ~/.satellite, .satellite or /etc/sysconfig/rhn/satellite or simply don't want to be asked the settings at run time"
    connect_group.add_option("--url", dest="saturl",default=None, help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    connect_group.add_option("--user", dest="satuser",default=None, help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    connect_group.add_option("--password", dest="satpwd",default=None, help="password of the user. Will be asked if not given and not in the configuration file.")
    connect_group.add_option("--org", dest="satorg", default="baseorg", help="name of the organization to use - design the section of the config file to use. Facultative, defaults to %default")
    parser.add_option_group(connect_group)
    (options, args) = parser.parse_args()
    if options.id == None :
        parser.error('please input a system id or snapshot id')
    elif options.listing :
        key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        print_snapshots(key,options.id)
        client.auth.logout(key)
    elif options.id:
        key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        print_snapshots(key,options.id)
        client.auth.logout(key)
    else:
        parser.error('unknown action')

#calls start here
if __name__=="__main__":
    main(__version__)
