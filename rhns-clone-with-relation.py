#!/usr/bin/python

##
# tool that copies a channel, creating a new channel with set relationship
##

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "dev"

# copies a configuration channel from one satellite to another

import xmlrpclib, warnings, re

#connector class -used to initiate a connection to a satellite and to send the proper satellite the proper commands
class RHNSConnection:

    username = None
    host = None
    key = None
    client = None
    closed = False

    def __init__(self,username,password,host):
        """connects to the satellite db with given parameters"""
        URL = "https://%s/rpc/api" % host
        self.client = xmlrpclib.Server(URL)
        self.key = client.auth.login(username,password)
        self.usernams = username
        self.host = host
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

class RHNSPackage:

    id = None
    name = None
    version = None
    release = None
    epoch = None
    arch = None
    checksum = None
    checksum_type = None
    last_modified_date = None

    def __init__(self, infos = {}):
        """creates an object from all the info stored"""
        self.id = infos['id']
        self.name = infos['name']
        self.version = infos['version']
        self.release = infos['release']
        self.epoch = infos['epoch']
        self.arch = infos['arch_label']
        self.checksum = infos['checksum']
        self.checksum_type = infos['checksum_type']
        self.last_modified_date = infos['last_modified_date']
        pass


class RHNSChannel:

    label = None
    name = None
    arch = None
    description = None
    erratas = {}
    packages = {}
    systems = {}
    original = None
    parent = None
    children = {}
    checksum_label = None
    new_channel = False

    def __init__(self, connection, details):
        """populates the object with the data from the channel"""
        if isinstance(details, dict):
            #code to create an object from the details
            self.label = details['label']
            self.name = details['name']
            self.arch = details['arch']
            self.description = details['description']
            self.parent = details['parent']
            self.original = details['original']
            self.checksum_label = details['checksum_label']
            self.new_channel = True
        else
            # create the object by fetching it piece by piece
            self.label = details
            infos = connection.channel.software.getDetails(connection.key, self.label)
            self.name = infos['name']
            self.arch = infos['arch_name']
            self.description = infos['description']
            self.parent = infos['parent_channel_label']
            self.original = infos['clone_original']
            self.checksum_label = infos['checksum_label']
        pass

    def create(self, connection):
        """creates the object from all the settings the object was created with"""
        if self.new_channel :
            #code
            #close changes
            self.new_channel = False
        else:
            print "ignoring order to create a channel - this channel already exists"
        pass

    def set_parent(self, label):
        """setter for a parent"""
        if self.new_channel :
            self.parent = label
        else:
            print "ignoring setter call - can't be edited after channel is saved"
        pass

    def __fetch_subscribed_machines(self, connection):
        """populates the list of subscribed machines (ids subscrubed to that channel)"""
        for system in connection.client.channel.listSubscribedSystems(connection.key, self.label):
            self.systems[system['id']] = system['name']
        pass

    def __fetch_packages(self, connection):
        """populates the list of packages """
        for package in connection.client.channel.software.listAllPackages(key, self.label):
            self.packages[package[id]] = RHNSPackge(package)
        pass

    def __fetch_children(self, connection):
        """populates the list of child channels one by one"""
        for channel in connection.client.channel.software.listChildren(connection.key, self.label):
            self.children[channel['label']] = RHNSChannel(connection, channel['label'])
        pass

    def __find_erratas(self, connection):
        """finds the erratas of the parent channel that are associated with the packages listed in the channel."""
        pass


#the main function of the program
def main(versioninfo):
    #TODO : move to argparse for RHEL7
    import optparse
    parser = optparse.OptionParser(description="Usage: %prog [options]\nThis program will clone all erratas and packages from the source to the destination as long as they are not already present in the destiation, depending on which settings are used", version="%prog "+versioninfo)
    parser.add_option("-u", "--url", dest="saturl", type="string", help="url or hostname of the satellite to use e.g. http://satellite.example.com/rpc/api", default="https://127.0.0.1/rpc/api")
    parser.add_option("-l", "--login", dest="satuser", type="string", help="User to connect to satellite")
    parser.add_option("-p", "--password", dest="satpwd", type="string", help="Password to connect to satellite")
    parser.add_option("-c", "--destChannel", dest="destChannel", type="string", help="Label of the destination channel to parse. Will be created if doesn't exist")
    parser.add_option("-s", "--sourceChannel", dest="sourceChannel", type="string", help="Label of the source channel to clone from")
    parser.add_option("-v", "--verbose", dest="verbose", action="count", help="Turns up the verbosity by one for each v" )
    parser.add_option("--listChannels", dest="listChannels", action="store_true", default=False, help="List all the channels")
    parser.add_option("--listErratas", dest="listErratas", action="store_true", default=False, help="Lists all the erratas of the source.")
    parser.add_option("--errataType", dest="errataType", type="string", help="The type of errata to display - one of 'Security Advisory', 'Product Enhancement Advisory', 'Bug Fix Advisory' ")
    parser.add_option("--maxIssueDate",dest="maxIssueDate", default=None, type="string", help="Maximum issue date for the erratas and packages to be included (YYYY-MM-DD HH24:MI:SS)")
    parser.add_option("--maxUpdateDate", dest="maxUpdateDate", default=None, type="string", help="Maximum update date for the erratas and packages to be included (YYYY-MM-DD H24:MI:SS)")
    parser.add_option("--onlyErratas", dest="onlyErratas", default=False, action="store_true", help="only process erratas")
    parser.add_option("--onlyPackages", dest="onlyPackages", default=False, action="store_true", help="only process packages")
    parser.add_option("-C", "--clean-channel", dest="cleanChannel", default=False, action="store_true", help="clean the destination channel before starting")
    (options, args) = parser.parse_args()
    #transformation of saturl into a full url if only given the hostname or an ip adress
    if re.match('^http(s)?://[\w\-.]+/rpc/api',options.saturl) == None:
        if re.search('^http(s)?://', options.saturl) == None:
            saturl = "https://"+options.saturl
        else:
            saturl = options.saturl
        if re.search('/rpc/api$', saturl) == None:
            saturl = saturl+"/rpc/api"
    if not options.satuser or not options.satpwd:
        parser.error('username and password are required options.')
    else:
        #init
        co = RHNSConnection(options.satuser,options.satpwd,saturl)
        if options.listChannels :
            print " %40s | %10s | %20s | %s " % ("Label", "Arch", "Provider", "Name")
            for channel in co.client.channel.listAllChannels(co.key):
                print " %40s | %10s | %20s | %s " % (channel['label'], channel['arch_name'],  channel['provider'], channel['name'])
        elif options.listErratas:
            if options.sourceChannel == None:
                parser.error('Need to specify the source channel when listing the erratas')
            else:
                print " %30s | %30s | %22s | %s" % ("Errata", "Type", "Update date", "Synopsis")
                if options.errataType and options.errataType in ('Security Advisory','Product Enhancement Advisory','Bug Fix Advisory'):
                    for errata in co.client.channel.software.listErrataByType(co.key,options.sourceChannel, options.errataType):
                        print " %30s | %30s | %22s | %s" % (errata['advisory_name'], errata['advisory_type'], errata['issue_date'], errata['advisory_synopsis']) #warning may be depredicated with no actual replacement in 5.6
                elif options.errataType:
                    print "Errata type "+str(options.errataType)+" not known"
                    for errata in co.client.channel.software.listErrata(co.key,options.sourceChannel):
                        print " %30s | %30s | %22s | %s" % (errata['advisory_name'], errata['advisory_type'], errata['issue_date'], errata['advisory_synopsis']) #warning may be depredicated with no actual replacement in 5.6
                else:
                    for errata in co.client.channel.software.listErrata(co.key,options.sourceChannel):
                        print " %30s | %30s | %22s | %s" % (errata['advisory_name'], errata['advisory_type'], errata['issue_date'], errata['advisory_synopsis']) #warning may be depredicated with no actual replacement in 5.6
        elif options.sourceChannel and options.destChannel and options.sourceChannel != options.destChannel :
            print "Aquiring information from the channels"
            source=RHNSChannel(co, options.sourceChannel)
            destination=RHNSChannel(co, options.sourceChannel)
            erratalist={}
            packagelist={}
            import time
            if maxIssueDate != None:
                if len(maxIssueDate) > 10:
                    maxIssueDate = time.strptime(options.maxIssueDate,"%Y-%m-%d %H:%M:%S")
                else:
                    maxIssueDate = time.strptime(options.maxIssueDate+" 23:50:59", "%Y-%m-%d %H:%M:%S")
            if maxUpdateDate != None:
                if len(maxUpdateDate) > 10:
                    maxUpdateDate = time.strptime(options.maxUpdateDate,"%Y-%m-%d %H:%M:%S")
                else:
                    maxUpdateDate = time.strptime(options.maxUpdateDate+" 23:50:59", "%Y-%m-%d %H:%M:%S")
            if not options.onlyPackages:
                #code to handle erratas comparison
                print "Comparing the erratas between "+source.label+" and "+destination.label
                erratalist = destination.buildErrataList(source, maxIssueDate, maxUpdateDate)
                print "Clonning "+str(len(erratalist))+" erratas to "+destination.label
                added = destination.addErratas(co, erratalist)
                print "Cloned "+str(len(added))+" erratas to the new channel"
            if not options.onlyErratas:
                #code to handle package comparison
                if not options.onlyPackages:
                    #refresh the list of packages since we synced the erratas!
                    destination.refresh(connection)
                print "Comparing the packages between "+source.label+" and "+destination.label
                packagelist = destination.buildPackageList(source, maxIssueDate, maxUpdateDate)
                print "Adding "+str(len(packagelist))+" packages to "+destination.label
                destination.addPackages(co, packagelist)
            print "Done"
        else:
            parser.error("unable to determine what to do - use -h for usage information")

        client.auth.logout(key)

if __name__ == "__main__":
    main(__version__)

