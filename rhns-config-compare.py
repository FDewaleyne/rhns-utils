#!/usr/bin/python

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "test"

import xmlrpclib, sys, re

##
#
# this can not unregister any RHEL system and can only restrain the numbers of allocatable systems in sub-organizations to the currently used values. attempting to do otherwise results in an error from the API.
#
##
##
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication.
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
##
# V1.0 by FDewaleyne - 30-08-2012 - versioning started
# v2.0 by FDewaleyne - 21-12-2013 - rewrite of the script to be object oriented and take options

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
        import ConfigParser,os
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
        #read the host from the url
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

def _check_osad(conn,systemid):
    """checks that the given systemid has osad installed, then tries to ping the machine. returns true if the systemid has osad installed"""
    global verbose;
    try:
        installed_packages = conn.client.system.listPackages(conn.key,systemid)
        for package in installed_packages:
            if package['name'] == 'osad':
                if verbose:
                    print "found %s-%s-%s.%s on system %s" % (package['name'], package['version'], package['release'], package['arch'], str(systemid))
                return True
            else:
                continue
    except:
        return False
    return False

def _check_action_finished(conn,actionid):
    """returns true if the action has finished, false if not"""
    global verbose;
    systems = conn.schedule.listInProgressSystems(conn.key,actionid)
    for system in systems:
        if system.get('timestamp',None) == None:
            return False
        elif verbose == True:
            print "action completed on system %s (%d) at %s" % (system['server_name'],system['server_id'],str(system['timestamp']))
    return True
    

def run_channel(conn,channellabel,noosad,delay):
    """runs the check against a channel and waits compares file by file, waiting for the execution of a channel to be done every 5 minutes"""
    global verbose;
    if delay < 1:
        sys.stderr.write("Invalid value for delay, defaulting to 5 minutes")
        delay = 5
    configfiles = conn.client.configchannel.listFiles(conn.key,channellabel)
    # each file is in configfiles[X]['path']
    systems = conn.client.configchannel.listSubscribedSystems(conn.key,channellabel)
    run_systems = []
    # each system is in systems[X]['id']
    if noosad:
        print "not running the osad checks - this may make the execution of the configuration channel test take a long time"
        for system in systems:
            run_systems.append(system['id'])
    else:
        for system in systems:
            if _check_osad(conn,system['id']):
                #add the system only if it passes the osad test
                run_systems.append(system['id'])
                if verbose:
                    print "system %s (%d) will be checked" % (system['name'],system['id'])
            else:
                print "system %s (%d) doesn't have osad installed, skipping" % (system['name'],system['id'])
    from time import sleep
    progress = 1
    for configfile in configfiles:
        #plan one action per config file
        print "\nProcessing file %s (%d out of %d)" % (file['path'], progress, len(configfiles))
        progress+=1
        actionid = conn.client.configchannel.scheduleFileComparisons(conn.key,channellabel,file['path'],run_systems)
        try:
            sleep(delay * 60)
            while(not _check_action_finished(conn,actionid)):
                sleep (delay * 60)
        except KeyboardInterrupt:
            sys.stderr.write('Keyboard interrupt captured - skipping to next call')
            sys.stderr.write("Details available at https://+"conn.host"+/rhn/schedule/ActionDetails.do?aid="+str(actionid) % (conn.host, actionid)
            continue
        # display the output
        failed = conn.schedule.listFailedSystems(conn.key,actionid)
        passed = conn.schedule.listCompletedSystems(conn.key,actionid)
        print "Completed : %d, Failed : %d, ran on %d systems" % (len(passed), len(failed), len(run_systems))
        print "Details available at https://%s/rhn/schedule/ActionDetails.do?aid=%d" % (conn.host, actionid)

#main function
def main(version):
    """main function"""
    global verbose;
    import optparse
    parser = optparse.OptionParser("%prog action_option [connection_options] [action_options] \n Adds as much flex entitlements as there is usage on each entitlement consumed then attempt to migrate systems, then the consumption is reset to usage", version=version)
    # connection options
    connect_group = optparse.OptionGroup(parser, "Connection options","Not required unless you want to bypass the details of ~/.satellite, .satellite or /etc/sysconfig/rhn/satellite or simply don't want to be asked the settings at run time")
    connect_group.add_option("--url", dest="saturl", help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    connect_group.add_option("--username", dest="satuser", help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    connect_group.add_option("--password", dest="satpwd", help="password of the user. Will be asked if not given and not in the configuration file.")
    connect_group.add_option("--orgname", dest="orgname", default="baseorg", help="the name of the organization to use as per your configuration file - defaults to baseorg")
    # action options
    action_group = optparse.OptionGroup(parser, "Action options", "use -c for each channel you wish to try in one run or no option to try all the configuration channels.")
    action_group.add_option("-l","--list",dest='list', action='store_true', default=False, help="List all the channels and quit")
    action_group.add_option("-c","--configchannel", dest='channellabels', action='append', help="Each call of this option indicates a configuration channel to use - identified by its label. If none is specified all will be used")
    action_group.add_option("--noosad", dest='noosad', action='store_true', default=False, help="Indicate that the osad check should be bypassed.\nWarning : machines without osad running can delay considerably the execution of the script")
    # global options
    global_group = optparse.OptionGroup(parser, "Global options", "Option that affect the display of information")
    global_group.add_option("-v", "--verbose",dest='verbose', action='store_true', default=False, help="Increase the verbosity of the script")
    global_group.add_option("-d", "--delay", dest='delay', default=5, type='int', help="Delay between each check on the execution of a systemid in minutes. defaults to 5")
    #integrate the groups
    parser.add_option_group(action_group)
    parser.add_option_group(connect_group)
    parser.add_option_group(global_group)
    (options, args) = parser.parse_args()
    verbose = options.verbose
    if options.list:
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.orgname)
        print "%30s | %5s | %s" % ("Label","OrgID","Name")
        for configchannel in conn.client.configchannel.listGlobals(conn.key):
            print "%30s | %5s | %s" % (configchannel['label'],str(configchannel['orgId']),configchannel['name'])
        conn.client.auth.logout(conn.key)
    elif len(options.channellabels == 0):
        #run agains all channel
        print "running against all channels - this can take a long time."
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.orgname)
        for configchannel in conn.client.configchannel.listGlobals(conn.key):
            run_channel(conn,configchannel['label'],options.noosad,options.delay)
        conn.client.auth.logout(conn.key)
    else:
        #normal run against a set list of channels
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.orgname)
        for channellabel in options.channellabels:
            run_channel(conn,channellabel,options.noosad,options.delay)
        conn.client.auth.logout(conn.key)
    pass

#calls start here
if __name__=="__main__":
    main(__version__)
    
