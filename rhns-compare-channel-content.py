#!/usr/bin/python
# this script has for purpose to dump infos about the erratas of a channel

###
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
###



__author__=  "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPLv2"
__version__ = "1.0d"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "beta"

import xmlrpclib, sys, re


#connection class
class RHNSConnection:

    username = None
    host = None
    url = None
    key = None
    satver = None
    client = None
    closed = False

    def __init__(self,username,password,host,orgname="baseorg"):
        """connects to the satellite db with given parameters"""
        #read configuration
        import ConfigParser,os,re
        config = ConfigParser.ConfigParser()
        config.read(['.satellite', os.path.expanduser('~/.satellite'), '/etc/sysconfig/rhn/satellite'])
        #decide what variable to use for the URL
        if host == None:
            #no host given in command line
            if config.has_section('default') and config.has_option('default', 'url'):
                #there is a config file and it has the settings for the url.
                self.url = config.get('default','url')
            else:
                #there is no config file or no option, default to the local host :
                print "Defaulting to 127.0.0.1"
                self.url = "https://127.0.0.1/rpc/api"
        else:
            #a hostname or url was given in command line. parse it to see if it is correct.
            self.url = host
            if re.match('^http(s)?://[\w\-.]+/rpc/api',self.url) == None:
                #this isn't the full url
                if re.search('^http(s)?://', self.url) == None:
                    self.url = "https://"+self.url
                if re.search('/rpc/api$', self.url) == None:
                    self.url = self.url+"/rpc/api"
            #if this is the url then nothing has to be done further to URL
        from urlparse import urlparse
        self.host = urlparse(self.url).hostname
        #check if there is a username in the options
        if username == None:
            #no username in command line
            if config.has_section(orgname) and config.has_option(orgname, 'username'):
                self.username = config.get(orgname,'username')
            else:
                #not in the config file, we have to prompt it
                sys.stderr.write("Login details for %s\n\n" % self.url)
                sys.stderr.write("Username: ")
                self.username = raw_input().strip()
        else:
            #use the value given in option
            self.username = username
        #now the password
        if password == None:
            #use the password from the config file
            if config.has_section(orgname) and config.has_option(orgname, 'password'):
                self.__password = config.get(orgname,'password')
            else:
                #no password set in the configuration file
                import getpass
                self.__password = getpass.getpass(prompt="Password: ")
                sys.stderr.write("\n")
        else:
            self.__password = password
        #connection part
        self.client = xmlrpclib.Server(self.url)
        self.key = self.client.auth.login(self.username,self.__password)
        try:
            self.satver = self.client.api.systemVersion()
            print "satellite version "+self.satver
        except:
            self.satver = None
            print "unable to detect the version"
        pass

    def close(self):
        """closes a connection. item can be destroyed then"""
        self.client.auth.logout(self.key)
        self.closed = True
        pass

    def __exit__(self):
        """closes connection on exit"""
        if not self.closed :
            self.client.auth.logout(self.key)
        pass

#end of the class

def search_content(sat1 ,label, sat2):
    """displays the name and general info of the channel then processes the list of packages to search each of them on satellite 2."""
    global verbose;
    sat1_packages = sat1.client.channel.software.listAllPackages(sat1.key, label)
    for sat1_package in sat1_packages:
        if sat1_package.get('epoch','') == '':
            epoch = ''
        else:
            epoch = sat1_package.get('epoch','')+':'
        print "Working on %s:%s-%s-%s.%s (ID %d, checksum(%s) %s)" % (epoch, sat1_package['name'], sat1_package['version'], sat1_package['release'], sat1_package['arch_label'], sat1_package['id'], sat1_package.get('checksum_type','none'), sat1_package.get('checksum','none'))
        search_results = sat2.client.packages.search.advanced("name:\"%s\" AND version:\"%s\" AND release:\"%s\" AND arch:\"%s\"" % (sat1_package['name'], sat1_package['version'], sat1_package['release'], sat1_package['arch_label']))
        print "Found %d matches"
        for match in search_results:
            if match.get('epoch','') == sat1_package.get('epoch',''):
                mchannels = sat2.client.packages.listProvidingChannels(sat2.key,match['id'])
                merratas = sat2.client.packages.listProvidingErrata(sat2.key,match['id'])
                print " - ID %d, provided by %d channels and %d erratas" % (match['id'], len(mchannels), len(merratas))
                if verbose:
                    for channel in mchannels :
                        print "  = (channel) : %s - %s" % (channel['label'], channel['name'])
                    for errata in merratas:
                        print "  = (errata)  : %s, issued on %s" % (errata['advisory'],errata['issue_date'])
            else:
                print " - ID %d : false positive - different epoch" % (match['id'])


#main function
def main(version):
    """main function"""
    global verbose;
    import optparse,sys
    parser = optparse.OptionParser("%prog action_option [connection_options] [global_options]\n   displays the errata info of sepecific channels", version=version)
    # connection options
    connect_group = optparse.OptionGroup(parser, "Connection options","Not required unless you want to bypass the details of ~/.satellite, .satellite or /etc/sysconfig/rhn/satellite or simply don't want to be asked the settings at run time. Those are used to establish the connection to the first satellite.")
    connect_group.add_option("--url", dest="saturl", help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    connect_group.add_option("--username", dest="satuser", help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    connect_group.add_option("--password", dest="satpwd", help="password of the user. Will be asked if not given and not in the configuration file.")
    connect_group.add_option("--orgname", dest="orgname", default="baseorg", help="the name of the organization to use as per your configuration file - defaults to baseorg")
    # action options
    action_group = optparse.OptionGroup(parser, "Action options", "use -l to list the channels of the 1st satellite or -c CHANNEL for each channel to use")
    action_group.add_option("-l","--list",dest='list', action='store_true', default=False, help="List all the channels and quit")
    action_group.add_option("-c","--softchannel", dest='channellabels', action='append', help="Each call of this option indicates a software channel to use - identified by its label. If none is specified all will be used")
    # global options
    global_group = optparse.OptionGroup(parser, "Global options", "Option that affect the display of information")
    global_group.add_option("-v", "--verbose",dest='verbose', action='store_true', default=False, help="Increase the verbosity of the script")
    #integrate the groups
    parser.add_option_group(action_group)
    parser.add_option_group(connect_group)
    parser.add_option_group(global_group)
    (options, args) = parser.parse_args()
    verbose = options.verbose
    if options.list:
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.orgname)
        print "%50s | %50s | %15s | %s\n" % ("Label","parent", "Arch", "Name")
        for softchannel in conn.client.channel.listSoftwareChannels(conn.key):
            print "%50s | %50s | %15s | %s" % (softchannel['label'],softchannel['parent_label'],softchannel['arch'],softchannel['name'])
        conn.client.auth.logout(conn.key)
    elif options.channellabels != None:
        #normal run against a set list of channels
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.orgname)
        sat2url = raw_input("Please enter the url of the second satellite's api (e.g. http://satellite.example.com/rpc/api): ").strip()
        sat2user = raw_input("Please enter a username for the second satellite : ").strip()
        import getpass                                                                                                                                                                                                                                                  
        sat2pwd = getpass.getpass(prompt="Password: ")                                                                                                                                                                                                          
        sys.stderr.write("\n")
        conn2 = RHNSConnection(sat2user, sat2pwd, sat2url)
        for channellabel in options.channellabels:
            search_content(conn,channellabel,conn2)
        conn.client.auth.logout(conn.key)
        conn2.client.auth.logout(conn2.key)
    else:
        parser.error('incorrect option usage')
        parser.print_help()
    pass

#calls start here
if __name__=="__main__":
    main(__version__)
    
