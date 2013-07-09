#!/usr/bin/python

##
# tool that copies a channel, creating a new channel with set relationship
##
# requires python 2.6
##
__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "dev"

# copies a configuration channel from one satellite to another

import xmlrpclib, re

#connector class -used to initiate a connection to a satellite and to send the proper satellite the proper commands
class RHNSConnection:

    #TODO: implement properties
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

    def __init__(self, infos):
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


class RHNSErrata(object):


    @property
    def advisory_name(self):
        return self._advisory_name

    @property
    def advisory_synopsis(self):
        return self._advisory_synopsis

    @property
    def advisory_type(self):
        return self._advisory_type

    @property
    def issue_date(self):
        return self._issue_date

    @property
    def update_date(self):
        return self._update_date

    @property
    def packages(self):
        return self._packages
        
    def __init__(self, connection, source):
        """creates the errata object"""
        #source sould be the same as the information present from the channel. it should otherwise be an errata name, and then will be looked up
        if type ( source ) == str:
            advisory_info = connection.client.errata.getDetails(connection.key, source)
            self._advisory_name = source
            self._advisory_synopsis = advisory_info['synopsis']
            self._advisory_type = advisory_info['type']
            self._issue_date = advisory_info['issue_date']
            self._update_date = advisory_info['update_date']
        elif type ( source ) == dict:
            #would only have elements id, date, update_date, advisory_synopsis, advisory_type, advisory_name
            self._advisory_name = source['advisory_name']
            self._advisory_synopsis = source['advisory_synopsis']
            self._avisory_type = source['advisory_type']
            self._issue_date = source['date']
            self._update_date = source['update_date']
        else:
            pass #TODO replace with raising an exception here
        #TODO : this is going to need an update.
        self._packages = {}
        for apackage in connection.client.errata.listPackages(connection.key, self.advisory_name):
            thepackage = RHNSPackage(connection,apackage)
            self.packages[thepackage['id']] = thepackage
        pass


    def __eq__(self, other):
        """compare two erratas and tells if they are the same based on the packages they contain"""
        #two erratas are identical if we have all the packages of one into the other - erratas can not include packages on the base of the architecture.
        #therefore if we compare the channel which has the least packages with the other, we can find out if all its packages are in the other.
        samepackages = True
        if len(other.packages) < len(self.packages):
            for package in other.packages:
                if not self.packages.has_key(package.packageid):
                    samepackages = False
        else:
            for package in self.packages:
                if not other.packages.has_key(package.packageid):
                    samepackages = False
        return samapackages


class RHNSChannel(object):

    ###
    # properties
    ###

    #l abel property
    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        if self.__new_channel:
            self._label = value
        else:
            print "cannot change the label on a channel already created"
    
    # name property
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self):
        self._name = value
        # name can be updated after creation of the channel
        if not __new_channel:
            self.__udpdates['name'] = self._name

    # arch property (arch_name or arch_label depending which parts of the api)
    @property
    def arch(self):
        return self._arch

    @arch.setter
    def arch(self,value):
        if self.__new_channel:
            self._arch = value
        else:
            print "cannot change the arch on a channel already created"

    # description property
    @property
    def description(self):
        return self._description

    @description.setter
    def description(self,value):
        self._description = value
        #this setting can be written to the db if this is an existing channel
        if not __new_channel:
            self.__updates['description'] = self._description
            
    # summary property
    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self,value):
        self._summary = value
        #this setting can be written to the db if this is an existing channel
        if not __new_channel:
            self.__updates['summary'] = self._summary

    #original property (clone relation)
    @property
    def original(self):
        return self._original

    @original.setter
    def original(self,value):
        if self.__new_channel:
            self._original = value
        else:
            print "cannot change the clone relation on a channel already created"

    #parent property (channel relation)
    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self,value):
        if self.__new_channel:
            self._parent = value
        else:
            print "cannot change the parent relation on a channel already created"

    #label property
    @property
    def checksum_label(self):
        return self._checksum_label

    @checksum_label.setter
    def checksum_label(self,value):
        self._checksum_label = value
        if self.__update_channel:
            self.__updates['checksum_label'] = self._checksum_label

    #the dictionaries

    # children property ; this shouldn't be set.
    @property
    def children(self):
        return self._children
    #this should only be manipulated by the functions of the channel object, no setter.

    # packages handling
    @property
    def packages(self):
        return self._packages
    #this should only be manipulated by the functions of the channel object, no setter.

    # systems handling
    @property
    def systems(self):
        return self._systems

    #TODO : replace the list of systems with a list of system objects so that adding, removing and other operations is possible (long term)

    # errata handling
    @property
    def erratas(self):
        return self._erratas
    #this should only be manipulated by functions around the channel or by the object stored...
    #TODO: implement setter and deleter around the notion of an errata object

    # maintainer properties

    @property
    def maintainer(self):
        return self._maintainer

    @maintainer.setter
    sef maintainer(self,values):
        """sets the values of maintainer, using name, email and phone"""
        if 'name' in values:
            self._maintainer['name'] = values['name']
        if 'email' in values:
            self._maintainer['email'] = values['email']
        if 'phone' in values :
            self._maintainer['phone'] = values['phone']
        if 'support_policy' in values:
            self._maintainer['support_policy'] = values['support_policy']
        if self.__new_channel:
            if 'name' in self._maintainer:
                self.__updates['maintainer_name'] = self._maintainer['name']
            if 'email' in self._maintainer:
                self.__updates['maintainer_email'] = self._maintainer['email']
            if 'phone' in self._maintainer :
                self.__updates['maintainer_phone'] = self._maintainer['phone']
            if 'support_policy' in self._maintainer:
                self.__updates['support_policy'] = self._maintainer['support_policy']

    # gpg_key properties
    @property
    def gpg_key(self):
        return self._maintainer

    @gpg_key.setter
    sef gpg_key(self,values):
        """sets the values of gpg_key, using url, id and fp"""
        if 'url' in values:
            self._maintainer['url'] = values['url']
        if 'id' in values:
            self._maintainer['id'] = values['id']
        if 'fp' in values :
            self._maintainer['fingerprint'] = values['fp']
        if self.__new_channel:
            if 'url' in self._gpg_key:
                self.__updates['gpg_key_url'] = self._gpg_key['url']
            if 'id' in self._gpg_key:
                self.__updates['gpg_key_id'] = self._gpg_key['id']
            if 'fingerprint' in self._gpg_key :
                self.__updates['gpg_key_fp'] = self._gpg_key['fingerprint']

    # hidden settings : 
    # - id (used to update the channel, required nowhere else

    def __init__(self, connection, label, source == None):
        """populates the object with the data from the channel"""
        #TODO : add maintainer support & handler to ignore if it is empty
        __connection = connection
        if isinstance(source, RHNSChannel):
            #code to create an object from the details
            self._label = label
            self._name = source.name
            self._description = source.description
            self._summary = source.summary
            #the rest needs to relatively stay the same
            self._arch = source.arch
            self._erratas = source.erratas
            self._parent = source.parent
            self._original = source.original
            self._checksum_label = source.checksum_label
            self._systems = source.systems
            self._children = source.children
            self._original = source.original
            self._maintainer = source._maintainer
            self._gpg_key = source._gpg_key
            self._systems = source.systems
            self.__id = None
            #prepare for the first push
            self.__update = {'description': self._description}
            self.__new_channel = True
        else
            # create the object by fetching it piece by piece
            self._label = label
            infos = connection.channel.software.getDetails(connection.key, self.label)
            self.__id = infos['id']
            self._name = infos['name']
            self._arch = infos['arch_name']
            self._description = infos['description']
            self._summary = infos['summary']
            self._parent = infos['parent_channel_label']
            self._original = infos['clone_original']
            self._checksum_label = infos['checksum_label']
            self._maintainer['name'] = infos["maintainer_name"]
            self._maintainer['email'] = sinfos["maintainer_email"]
            self._maintainer['phone'] = infos["maintainer_phone"]
            self._maintainer['support_policy'] = infos["support_policy"]
            self._gpg_key['url'] = infos["gpg_key_url"]
            self._gpg_key['id'] = infos["gpg_key_id"]
            self._gpg_key['fingerprint'] infos["gpg_key_fp"]
            self.__populate_children()
            self.__populate_packages()
            self.__populate_systems()
            self.__populate_erratas()
            self.__new_channel = False
        self.__updates = {} # used to update content after the channel has been created
        pass

    def commit(self):
        """creates the object or saves changes pending. needs to be called after a change to make the change persistant. called by destructor to ensure changes are saved"""
        if self.__new_channel :
            #create the channel
            self.__create()
            #update fields that can't be set at creation time
            self.__update_details()
            del __updates
            self.__updates = {}
            #close changes
            self.__new_channel = False
        elif len(self.__updates) > 0:
            #commit updates pending
            self.__update_details()
            del self.__updates
            self.__updates = {}
        else:
            #TODO : replace with exception or reaction to verbosity level
            print "nothing to save"
        pass

    def refresh(self):
        """refreshes the contents of the channel"""
        #TODO: refresh contents of the object here
        #TODO: refresh childs
        #TODO: refresh packages
        #TODO: refresh systems
        #TODO: refresh errata
        #TODO: refresh details of the channel
        pass

    def __update_details(self):
        """updates the details of the channel"""
        if 'support_policy' in self.__updates:
            #this call is the only thing that can set support_policy
            self.__connection.client.channel.software.setContactDetails( self.__connection.key, self._label, self._maintainer['name'], self._maintainer['email'], self._maintainer['phone'], self._maintainer['support_policy'])
        self.__connection.client.channel.software.setDetails( self.__connection.key, self._id, self.__updates )

    def __create(self):
        """creates the channel from the elements stored"""
        #instead of create use, clone if a clone should be created
        if self._original == None
            #arch : channel-ia32, channel-ia64n, channel-sparc, etc. refer to the channel.software.create call for details
            #checksum_label should be sha1 or sha256 but from experience it's not down to only that.
            self.__connection.client.channel.software.create( self.__connection.key, self._label, self._name, self._summary, self._arch, self._parent, self._checksum_label, self._gpg_key)
        else:
            #call to the clone creation function
            #forcing to include the original state since we want it and not the current state to avoid removing packges
            self.__connection.client.channel.software.clone( self.__connection.key, self._original, self.__generate_details(), True) 

        #this call is the only thing that can set support_policy
        self.__connection.client.channel.software.setContactDetails( self.__connection.key, self._label, self._maintainer['name'], self._maintainer['email'], self._maintainer['phone'], self._maintainer['support_policy'])
        infos = self.__connection.client.channel.software.getDetails(self.__connection.key, self._label)
        self._id = infos['id']
        pass

    def __generate_details(self):
        """generates the dictionary required by the clonning call, depending on the elements set"""
        details = {'name': self._name, 'label': self._label, 'summary': self._summary}
        if not self._description == None :
            details['description'] = self._description
        if not self._parent == None:
            details['parent_label'] = self._parent
        if not self._arch == None:
            #TODO: make sure that the clone uses the same arch format as the create call.
            #NOTE: if omited the one of the original will be used
            details['arch_label'] = self._arch
        if not len(self._gpg_key) == 0:
            if 'url' in self._gpg_key:
                details['gpg_key_url'] = self._gpg_key['url']
            if 'id' in self._gpg_key:
                details['gpg_key_id'] = self._gpg_key['id']
            if 'fingerprint' in self._gpg_key:
                details['gpg_key_fp'] = self._gpg_key['fingerprint']
        pass

    def __populate_erratas(self):
        """populates the erratas"""
        self._erratas = {}
        for errata in self.__connection.client.channel.software.listErrata(self.__connection.key, self._label):
            self._erratas[errata['advisory_name']] = RHNSErrata(errata)

    def __populate_subscribed_machines(self):
        """populates the list of subscribed machines (ids subscrubed to that channel)"""
        self._systems = {}
        for system in self.__connection.client.channel.listSubscribedSystems(self.__connection.key, self.label):
            self._systems[system['id']] = system['name']
        pass

    def __populate_packages(self):
        """populates the list of packages """
        self._packages = {}
        for package in self.__connection.client.channel.software.listAllPackages(self.__connection.key, self.label):
            self._packages[package[id]] = RHNSPackge(package)
        pass

    def __populate_children(self):
        """populates the list of child channels one by one"""
        self._children = {}
        for channel in self.__connection.client.channel.software.listChildren(self.__connection.key, self.label):
            self._children[channel['label']] = RHNSChannel(self.__connection, channel['label'])
        pass

    def __find_erratas(self):
        """finds the erratas of the parent channel that are associated with the packages listed in the channel."""
        #TODO : work on this later (find all erratas in the original, go through all erratas and find the ones that have packages in the channel, then clone these in the channel)
        pass

    def __delete_channel(self):
        """deletes the channel"""
        for child in self._children:
            self.__connection.channel.software.delete(self.__connection.key, child.label)
        del self._children[:]
        self.__connection.channel.software.delete(self.__connection.key, self._label)

    def __exit__(self):
        """runs on exit"""
        self.commit()


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

