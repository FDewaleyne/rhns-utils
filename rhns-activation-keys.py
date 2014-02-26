#!/usr/bin/python

#lists and offers to delete activation keys 

import xmlrpclib, sys, os, ConfigParser,getpass, optparse

#global variable
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
    if config.has_section(orgname) and config.has_option(orgname,'username') and config.has_option(orgname,'password') and config.has_option('default','url'):
        SATELLITE_LOGIN = config.get(orgname,'username')
        SATELLITE_PASSWORD = config.get(orgname,'password')
        SATELLITE_URL = config.get('default','url')
    else:
        if not config.has_option('default','url'):
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
 
def print_list(key):
    global client;
    print "Activation keys :"

    print "\t label - tree_label - name - active"
    for entry in client.activationkey.listActivationKeys(key):
        print "\t"+entry['key']+" - "+entry['description']+ " - Universal default : "+str(entry['universal_default'])+" - Base channel : "+entry['base_channel_label']

def print_info(key,label,verbose):
    global client;
    keydata = client.activationkey.getDetails(key,label)
    print "for key "+label
    print "\t- description : "+keydata['description']
    print "\t- usage limit : "+str(keydata['usage_limit'])
    print "\t- base channel : "+keydata['base_channel_label']
    try:
        channeldata = client.channel.software.getDetails(key,keydata['base_channel_label'])
        print "\t- base channel arch: "+channeldata['arch_name']
    except:
        print "\t- base channel arch: no data available"
        pass
    print "\t- child channels : "
    for childchannellabel in keydata['child_channel_labels']:
        try:
            childchanneldata = client.channel.software.getDetails(key,childchannellabel)
            print "\t\t= "+childchannellabel
            print "\t\t\t+ arch: "+childchanneldata['arch_name']
            print "\t\t\t+ parent: "+childchanneldata['parent_channel_label']
        except:
            print "\t\t= [error fetching data for "+childchannellabel+"]"
            pass
    print "\t\t= entitlements:"
    try:
        for entitlementname in keydata['entitlements']:
            print "\t\t\t+ "+entitlementname
    except:
        print "\t\t\t+ error fetching entitlements"
    if verbose:
        print "\t\t= packages:"
        for entry in keydata['packages']:
            print "\t\t\t+ "+entry['name']
    #config file part
    print "\t- config channels:"
    try:
        configchannels = client.activationkey.listConfigChannels(key,label)
    except:
        #satellite 5.5 and previous, if activation key has no config channel, just use an empty dictionary
        configchannels = {}
    for configchannel in configchannels:
        print "\t\t= "+configchannel['label']+" - "+configchannel['name']+" - "+configchannel['description']
        if verbose:
            files = client.configchannel.listFiles(key,configchannel['label'])
            for file in files:
                print "\t\t\t+ "+file['type']+" - "+file['path']

def delete_key(key,label):
    global client;
    if client.activationkey.delete(key,label) == 1:
        print "Activation key deleted"
    else:
        print "Actication Key not found or can't be deleted"

def main():
    parser = optparse.OptionParser("%prog -k activationkey  |-l [-v]")
    parser.add_option("-l", "--list", dest="listing", help="List all keys and quit", action="store_true")
    parser.add_option("-k", "--key", dest="keylabel")
    parser.add_option("-d", "--deletekey", dest="delkey",action="store_true",help="deletes the key")
    parser.add_option("-v", "--verbose",action="store_true",dest="verbose",help="activates verbose output",default=False)
    (options, args) = parser.parse_args()
    if options.listing:
        key = session_init()
        print_list(key)
        client.auth.logout(key)
    elif options.keylabel:
        key = session_init()
        if options.delkey:
            delete_key(key,options.keylabel)
        else:
            print_info(key,options.keylabel,options.verbose)
        client.auth.logout(key)
    else:
        parser.error('no action given')

    
#calls start here
if __name__=="__main__":
    main()
