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

def allocate_flex(conn,orgid,entitlements,novirt):
    """Allocates the usage into flex entitlements (all phy + flex already used) ; will use that number or the max that can be used."""
    if orgid == None:
        orglist = sorted(conn.client.org.listOrgs(conn.key))
    else:
        orglist = orgid
    #keeping this because we still need to separate any system addon from any entitlement
    SYS_ADDONS=[]
    ENTITLEMENTS=[]
    ENTITLEMENTS_REQUIRED = {'enterprise_entitled': 0}
    ALL_ENTITLEMENTS = False
    ALL_SYSADDONS = False
    if entitlements == None:
        ALL_ENTITLEMENTS = True
        ALL_SYSADDONS = True
    else:
        for entitlement in entitlements:
            if entitlement in ['monitoring_entitled','enterprise_entitled','provisioning_entitled','virtualization_host','virtualization_host_platform']:
                SYS_ADDONS.append(entitlement)
            else:
                ENTITLEMENTS.append(entitlement)
    #don't reset ALL_* values if an entitlement or system addon has been used in the call, it would only throw confusion
    for org in orglist:
        #only if this isn't the base org
        if org['id'] > 1:
            #we need to access the list of systems for the novirt flag meaning we need to establish conn2 first
            print "Attempting to log in as admin of org "+str(org['id'])
            #attempt to log in against org ID ; to avoid this create a section using the [ID] with the username and password.
            conn2 = RHNSConnection(None,None,conn.url,org['id'])
            #check the consumption of flex systems and compute the entitlements required for their migration
            for guest in conn2.client.system.listEligibleFlexGuests(conn2.key):
                #this won't work for systems that aren't RHEL
                try:
                    #add a management, add an entitlement of all the system is subscribed to
                    ENTITLEMENTS_REQUIRED['enterprise_entitled'] += 1
                    #add base channel
                    base = conn2.client.system.listSubscribableBaseChannels(conn2.key,guest['id'])
                    if base['label'] in ENTITLEMENTS_REQUIRED.keys():
                        ENTITLEMENTS_REQUIRED[base['label']] += 1
                    else:
                        ENTITLEMENTS_REQUIRED[base['label']] = 1
                    #add the childs
                    for channel in conn2.client.system.listSubscribedChildChannels(conn2.key,guest['id']):
                        if channel['label'] in ENTITLEMENTS_REQUIRED.keys():
                            ENTITLEMENTS_REQUIRED[channel['label']] += 1
                        else:
                            ENTITLEMENTS_REQUIRED[channel['label']] = 1
                except e:
                    sys.stderr.write("unable to take into account a guest of system "+str(system['id'])+" ; ignore if this is a system not consuming any channels")
                    pass
            #do we need to break virtualization hosts
            #TODO: confirm if systems in here can be converted without breaking the host
            #TODO: are guests of a virt host of the old type detected  by listFlexGuests?
            if novirt:
                #add virtualization addons to the cleaning list for later.
                if not ALL_SYSADDONS and not 'virtualization_host' in SYS_ADDONS:
                    entitlements.append('virtualization_host')
                if not ALL_SYSADDONS and not 'virtualization_host_platform' in SYS_ADDONS:
                    entitlements.append('virtualization_host_platform')
                #count how many additional entitlements are required to break the virtualization systems.
                for system in conn2.client.system.listVirtualHosts(conn2.key):
                    system_entitlements = conn2.client.system.getEntitlements(conn2.key,system['id'])
                    if 'virtualization_host' in system_entitlements or 'virtualization_host_platform' in system_entitlements:
                        for guest in conn2.client.listVirtualGuests(conn2.key,system['id']):
                            #this won't work for systems that aren't RHEL
                            try:
                               #add a management, add an entitlement of all the system is subscribed to
                               ENTITLEMENTS_REQUIRED['enterprise_entitled'] += 1
                               #add base channel
                               base = conn2.client.system.listSubscribableBaseChannels(conn2.key,guest['id'])
                               if base['label'] in ENTITLEMENTS_REQUIRED.keys():
                                   ENTITLEMENTS_REQUIRED[base['label']] += 1
                               else:
                                   ENTITLEMENTS_REQUIRED[base['label']] = 1
                               #add the childs
                               for channel in conn2.client.system.listSubscribedChildChannels(conn2.key,guest['id']):
                                   if channel['label'] in ENTITLEMENTS_REQUIRED.keys():
                                       ENTITLEMENTS_REQUIRED[channel['label']] += 1
                                   else:
                                       ENTITLEMENTS_REQUIRED[channel['label']] = 1
                            except e:
                                sys.stderr.write("unable to take into account a guest of system "+str(system['id'])+" ; ignore if there are non RHEL guests running there")
                                pass
            #treating all entitlements, adding what is required to fix flex consumption.
            #this code will never be able to force systems that aren't detected as flex. it only makes sense to use the numbers we detected with the previous two runs
            #This will not try to reduce to more than flex used and let's not allocate all the usage either. it won't do anything if no system is detected as flex
            if ENTITLEMENTS != [] and not ALL_ENTITLEMENTS:
                for element in conn.client.org.listSoftwareEntitlementsForOrg(conn.key,org['id']):
                    if element['label'] in ENTITLEMENTS:
                        try:
                            if  element['label'] in ENTITLEMENTS_REQUIRED:
                                needed_flex = element['used'] + element['used_flex'] + ENTITLEMENTS_REQUIRED['label']
                            else:
                                needed_flex = element['used_flex']
                            max_alloc = element['unallocated_flex']
                            #allocate the maximum value or the needed_flex depending on wether or not the requirement is too large or not.
                            if max_alloc >= needed_flex:
                                conn.client.org.setSoftwareFlexEntitlements(conn.key,org['id'],element['label'],needed_flex)
                                status = "setting" +element['label']+" to "+str(needed_flex)+" flex"
                            else:
                                conn.client.org.setSoftwareFlexEntitlements(conn.key,org['id'],element['label'],max_alloc)
                                sys.stderr.write("warning : unable to allocate all the flex entitlements "+element['label']+" would need to convert all physical subscriptions")
                                status = "setting "+element['label']+" to "+str(max_alloc)+" flex"
                            print status
                        except:
                            sys.stderr.write("unable to alter  "+element['label']+" aka "+element['name']+"\n")
            elif ALL_ENTITLEMENTS:
                for element in conn.client.org.listSoftwareEntitlementsForOrg(conn.key,org['id']):
                    try:
                        if element['label'] in ENTITLEMENTS_REQUIRED:
                            needed_flex = element['used'] + element['used_flex'] + ENTITLEMENTS_REQUIRED['label']
                        else:
                            needed_flex = element['used_flex']
                        max_alloc = element['unallocated_flex']
                        #allocate the maximum value or the needed_flex depending on wether or not the requirement is too large or not.
                        if max_alloc >= needed_flex:
                            conn.client.org.setSoftwareFlexEntitlements(conn.key,org['id'],element['label'],needed_flex)
                            status = "setting" +element['label']+" to "+str(needed_flex)+" flex"
                        else:
                            conn.client.org.setSoftwareFlexEntitlements(conn.key,org['id'],element['label'],max_alloc)
                            sys.stderr.write("warning : unable to allocate all the flex entitlements "+element['label']+" would need to convert all physical subscriptions")
                            status = "setting "+element['label']+" to "+str(max_alloc)+" flex"
                        print status
                    except:
                        sys.stderr.write("unable to alter "+element['label']+" aka "+element['name']+"\n")
            print "Allocation of flex finished on Org %d (%s)" % (org['id'], org['name'])
            #part where we do the additional magic for the virtualization consummers
            if novirt:
                for system in conn2.client.system.listVirtualHosts(conn2.key):
                    try:
                        entitlements = conn2.client.system.getEntitlements(conn2.key,system['id'])
                        if 'virtualization_host' in entitlements:
                            conn2.client.system.removeEntitlements(conn2.key,server['id'],['virtualization_host'])
                        elif 'virtualization_host_platform' in entitlements:
                            conn2.client.system.removeEntitlements(conn2.key,server['id'],['virtualization_host_platform'])
                    except e:
                        sys.stderr.write("unable to break the virtualization entitlement of system %d for reason :\n%e\n" % (system['id'],str(e)))
            print "Now attempting to migrate to flex"
            for system in conn2.client.system.listEligibleFlexGuests(conn2.key):
                try:
                    conn2.client.system.convertToFlexEntitlement(conn2.key,system['id'])
                    print "converted %d to flex" % (system['id'])
                except e:
                    print "unable to convert %d to flex with reason\n%s" % (system['id'],str(e))
                    pass
            conn2.close()
            print "now trying to reset consumption to usage before moving on to the next organization"
            #this allows to also reset the consumption in case in a later patch dealing with virtualization entitlements is possible.
            clean_allocation(conn,org['id'],entitlements)
        else:
            print "trying to migrate to flex directly since we are in org 1"
            for system in conn.client.system.listEligibleFlexGuests(conn.key):
                try:
                    conn2.client.system.convertToFlexEntitlement(conn2.key,system['id'])
                    print "converted %d to flex" % (system['id'])
                except e:
                    print "unable to convert %d to flex with reason\n%s" % (system['id'],str(e))
                    pass
            print "convertion attempt finished"
    pass

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
        for entitlement in entitlements:
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
            print "Finished working on Org "+str(org['id'])+', '+org['name']
        else:
            print "Skpping Org 1 - the base organization isn't affected by resets"



def main(version):
    """main function"""
    import optparse
    parser = optparse.OptionParser("%prog action_option [connection_options] [-h] \n Adds as much flex entitlements as there is usage on each entitlement consumed then attempt to migrate systems, then the consumption is reset to usage", version=version)
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
    action_group.add_option('--novirt',dest='novirt', action='store_true', default=False, help="use this flag to attempt to break any system found using virtualization or virtualization platform entitlements (depredicated for flex)")
    parser.add_option_group(action_group)
    parser.add_option_group(connect_group)
    (options, args) = parser.parse_args()
    if options.all or options.entitlements != None:
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.orgname)
        allocate_flex(conn, options.orgid, options.entitlements, options.novirt)
        conn.client.auth.logout(conn.key)
    else:
        #then no action is asked, exit
        parser.error("No action selected")
    pass

#calls start here
if __name__=="__main__":
    main(__version__)
    
