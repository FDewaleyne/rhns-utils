#!/usr/bin/python


__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "stable"

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
                    URL = URL+"/rpc/api"
            #if this is the url then nothing has to be done further to URL
        #TODO: fix this and create a snippet with the connector / source for all to import
        #self.host = host
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
            self.satver = client.api.systemVersion()
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

def clean_allocation(conn,orgid,entitlements):
    """clean a selection of orgs of a selection of entitlements or all entitlements if no selection is made"""
    if orgid == None:
        orglist = sorted(conn.client.org.listOrgs(conn.key))
    else:
        orglist = orgid
    SYS_ADDONS=[]
    ENTITLEMENTS=[]
    ALL_ENTITLEMENTS = False
    ALL_SYSADDONS = False
    if entitlements == None:
        ALL_ENTITLEMENTS = True
        ALL_SYSADDONS = True
    else:
        for entry in entitlements:
            if entitlement in ['monitoring_entitled','enterprise_entitled','provisioning_entitled','virtualization_host','virtualization_host_platform']:
                SYS_ADDONS.append(entitlement)
            else:
                ENTITLEMENTS.append(entitlement)
    #don't reset ALL_* values if an entitlement or system addon has been used in the call, it would only throw confusion
    for org in orglist:
        #only if this isn't the base org
        if org['id'] > 1:
            if ENTITLEMENTS != [] and not ALL_ENTITLEMENTS:
                for element in conn.client.org.listSoftwareEntitlementsForOrg(conn.key,org['id']):
                    if element['label'] in ENTITLEMENTS:
                       try:
                           print "reseting "+element['label']+" to "+str(element['used'])+" regular and "+str(element['used_flex'])+" flex for "+org['name']
                           conn.client.org.setSoftwareEntitlements(conn.key,org['id'],element['label'],element['used'])
                           conn.client.org.setSoftwareFlexEntitlements(conn.key,org['id'],element['label'],element['used_flex'])
                       except:
                           sys.stderr.write("unable to reset "+element['label']+" aka "+element['name']+"\n")
            elif ALL_ENTITLEMENTS:
                for element in conn.client.org.listSoftwareEntitlementsForOrg(conn.key,org['id']):
                    try:
                        print "reseting "+element['label']+" to "+str(element['used'])+" regular and "+str(element['used_flex'])+" flex for "+org['name']
                        conn.client.org.setSoftwareEntitlements(conn.key,org['id'],element['label'],element['used'])
                        conn.client.org.setSoftwareFlexEntitlements(conn.key,org['id'],element['label'],element['used_flex'])
                    except:
                        sys.stderr.write("unable to reset "+element['label']+" aka "+element['name']+"\n")
            if SYS_ADDONS != [] and not ALL_SYSADDONS:
                for element in conn.client.org.listSystemEntitlementsForOrg(conn.key,org['id']):
                    if element['label'] in SYS_ADDONS:
                        try:
                           print "reseting "+element['label']+" to "+str(element['used'])+" for "+org['name']
                           conn.client.org.setSystemEntitlements(conn.key,org['id'],element['label'],element['used'])
                        except:
                           sys.stderr.write("unable to reset "+element['label']+"\n")
            elif ALL_SYSADDONS:
                for element in conn.client.org.listSystemEntitlementsForOrg(conn.key,org['id']):
                    try:
                       print "reseting "+element['label']+" to "+str(element['used'])+" for "+org['name']
                       conn.client.org.setSystemEntitlements(conn.key,org['id'],element['label'],element['used'])
                    except:
                       sys.stderr.write("unable to reset "+element['label']+"\n")
            print "finished working on "+str(org['id'])+', '+org['name']


def main(version):
    """main function"""
    import optparse
    parser = optparse.OptionParser("%prog action_option [connection_options] [-h] \n Resets the allocation of entitlements by sub organizations to the consumed values, does not unregister systems", version=version)
    # connection options
    connect_group = optparse.OptionGroup(parser, "Connection options","Not required unless you want to bypass the details of ~/.satellite, .satellite or /etc/sysconfig/rhn/satellite or simply don't want to be asked the settings at run time")
    connect_group.add_option("--url", dest="saturl", help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    connect_group.add_option("--username", dest="satuser", help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    connect_group.add_option("--password", dest="satpwd", help="password of the user. Will be asked if not given and not in the configuration file.")
    connect_group.add_option("--orgname", dest="orgname", default="baseorg", help="the name of the organization to use as per your configuration file - defaults to baseorg")
    # action options
    action_group = optparse.OptionGroup(parser, "Action options", "One of --all or an --entitlement ENTITLEMENT_LABEL is required")
    action_group.add_option("-a","--all", dest='all', action='store_true', default=False, help="Resets all entitlements to the consumed values for the sub organizations")
    action_group.add_option('-e','--entitlement', dest='entitlements', action='append', help='Entitlement to reset - one time per entitlement or system addon')
    action_group.add_option('-g','--orgid', dest='orgid', action='append', type='int', help='Limit the reset to the organizations with that id - can be used multiple times. If omitted will reset all sub organizations.')
    parser.add_option_group(action_group)
    parser.add_option_group(connect_group)
    (options, args) = parser.parse_args()
    if options.all or options.entitlements != None:
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.orgname)
        reset_allocation(conn, options.orgid, options.entitlements)
        conn.client.auth.logout(conn.key)
    else:
        #then no action is asked, exit
        parser.error("No action selected")
    pass

#calls start here
if __name__=="__main__":
    main(__version__)
    
