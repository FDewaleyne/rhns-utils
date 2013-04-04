#!/usr/bin/python

##
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
##

###
# this script can list available erratas for the system (RHEL5 or 6), download all packages relevant from an errata or plan the installation of the errata remotely. 
# the download of all rpms has nothing to do with yum and is meant to provide a workaround when yum cannot download the information
###

####
# about the config file used by RHNSSession :
# to set the values, create a config file .satellite in the running folder or in your home folder or in /etc/sysconfig/rhn/satellite with lines :
# [baseorg]
# url = http://satellite.fqdn/rpc/api
# username = satadmin
# password = password
# no setting is mandatory and  missing elements will be requested when running.
####

#####
# author Felix Dewaleyne
# 2012-11-15 : version 0.1 - Felix Dewaleyne
# 2012-11-20 : version 1.0 - Felix Dewaleyne
# 2012-12-12 : version 2.0 - Felix Dewaleyne - creating +1 object - one to handle the list of all erratas and one to handle an errata and its comparison.
# 2013-04-13 : version 2.1 - Felix Dewaleyne - fixing several issues with the previous update
#####

#object part starts here
import xmlrpclib, warnings

class SystemControl:
    def __init__(self,systemID=None):
        """stores the system id on call"""
        if not systemID == None:
            self.serverID = systemID
        else:
            import fileinput, re
            try:
                for line in fileinput.input("/etc/sysconfig/rhn/systemid"):
                    m = re.search('ID-(\d+)', line)
                    if m:
                        self.serverID = int(m.group(1))
                        break
                    else:
                        pass
            except:
                warnings.warn("failed to read the systemid from /etc/sysconfig/rhn/systemid, is this system registered?")
                raise
            pass

    #TODO: add method to install the RPMS from the python API
    
class RHNSSession:
    def __init__(self,orgname="baseorg"):
        """initialises the connection or duplicates it"""
        if isinstance(orgname, RHNSSession):
            self.client = orgname.client
            self.key = orgname.key
            self.host = orgname.host
            self.url = orgname.url
            self.login = orgname.login
        else:
            import getpass, sys, os, ConfigParser
            config = ConfigParser.ConfigParser()
            config.read(['.satellite', os.path.expanduser('~/.satellite'), '/etc/sysconfig/rhn/satellite'])
            if config.has_section(orgname) and config.has_option(orgname,'username') and config.has_option(orgname,'password') and config.has_option('baseorg','url'):
                self.login = config.get(orgname,'username')
                password = config.get(orgname,'password') # password is not stored past running the function
                self.url = config.get('baseorg','url')
            else:
                if not config.has_option('baseorg','url'):
                    sys.stderr.write("enter the satellite url, such as https://satellite.example.com/rpc/api")
                    sys.stderr.write("\n")
                    self.url = raw_input().strip()
                else:
                    self.url = config.get('baseorg','url')
                sys.stderr.write("Login details for %s\n\n" % self.url)
                sys.stderr.write("Login: ")
                self.login = raw_input().strip()
                # Get password for the user
                password = getpass.getpass(prompt="Password: ")
                sys.stderr.write("\n")
            #inits the connection
            self.client = xmlrpclib.Server(self.url, verbose=0)
            self.key = self.client.auth.login(self.login, password)
            # removes the password from memory
            del password
            from urlparse import urlparse
            urlobj = urlparse(self.url)
            try:
                self.host = urlobj.hostname
            except AttributeError:
                #python 2.4 doesn't have attributes, instead the value will be in index 1
                self.host = urlobj[1]
    pass

    def close(self):
        """closes the session"""
        self.client.auth.logout(self.key)
        #after that you can destroy the object.
        #not using __exit__ as this needs to be compatible with python 2.4
        pass

class RhnsErratas(RHNSSession,SystemControl):

    def __init__(self,orgname="baseorg",sysID=None):
        """gets the ID, initiates the connection and gets the errata list"""
        #TODO: needs a way to be able to reuse a connection
        RHNSSession.__init__(self,orgname)
        SystemControl.__init__(self,sysID)
        self.erratas = self.client.system.getRelevantErrata(self.key,self.serverID)
        pass

    def listAvailable(self):
        """lists all available erratas for self.serverID"""
        print ("%30s | %18s | %10s | %s" % ("Type", "Name","Date","Synopsis"))
        for an_errata in self.erratas: 
            print ("%30s | %18s | %10s | %s" % (an_errata['advisory_type'], an_errata['advisory_name'], an_errata['date'], an_errata['advisory_synopsis']))
        if len(self.client.system.getRelevantErrata(self.key,self.serverID)) == 0:
            print "no errata avaiable"
        pass


class RhnsErrata(RHNSSession,SystemControl):
    packages = [];

    def __init__(self,advisory,orgname="baseorg",sysID=None):
        """get the ID, sets the connection and gets the package list for the errata"""
        #TODO: needs a way to be able to reuse a connection
        RHNSSession.__init__(self,orgname)
        SystemControl.__init__(self,sysID)
        self.advisory = advisory
        self.getErrataPackages(advisory)
        pass

    def __cmp__(self,other):
        """used for == != < > <= >= ; before comparison is made, the package list needs to be filled"""
        #called from the left argument with other being the right argument.
        #return -1 if smaller, 0 if equal and 1 for greater.
        #we will return -1 if left has less packages than right
        #we will return 0 if the same pacakges are there
        #we will return 1 if left has more packages than right
        if not isinstance(other,RhnsErrata):
            return NotImplemented
        else:
            if len(self.packages) == len(other.packages):
                return 0
            elif len(self.packages) < len(other.packages):
                return -1
            elif len(self.packages) > len(other.packages):
                return 1

    def getErrataPackages(self,errata,channels=[]):
        """populates the list of packages to be downloaded as a dictionary. limits to these of the given channel if passed as a parameter. needs an errata name and a channel label if given one"""
        if channels == []:
            #get the whole list
            self.packages = self.client.errata.listPackages(self.key, errata)
        else:
            #get the list but only for packages that are for a channel this machine is registered to
            channels_set = set(channels) #turning the list into a set to compare it with the list of channels from the packages
            for packageinfo in self.client.errata.listPackages(self.key, errata):
                matches = channels_set.intersection(packageinfo['providing_channels'])
                if len(matches) > 0:
                    self.packages.append(packageinfo)
        pass

    def downloadErrata(self,errata=None,channels=[]):
        """downloads the packages in self.packages to the running folder"""
        #populate the list if required to
        if not errata == None:
            self.getErrataPackages(errata,channels)
        #TODO: support for specific destination instead of working directory
        for packageinfo in self.packages:
            import urllib2
            # creates a file name-version-release-arch.rpm in binary mode
            filename = packageinfo['name']+"-"+packageinfo['version']+'-'+packageinfo['release']+'-'+packageinfo['arch_label']+'.rpm'
            u = urllib2.urlopen(self.client.packages.getPackageUrl(self.key, int(packageinfo['id'])))
            f = open(filename, 'wb')
            filesize = int(packageinfo['size'])
            print ("Downloading: %s Bytes: %s" % (filename, str(filesize)))
            filesize_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break
                filesize_dl += len(buffer)
                f.write(buffer)
                status = r"%10d [%3.2f%%]" % (filesize_dl, (filesize_dl * 100 / filesize))
                status = status + chr(8)*(len(status)+1)
                print status,
            f.close()
        print r"All Packages Downloaded"
        pass

    def downloadRelevantPackages(self,errata):
        """if called, will download all packages present in a channel the machine is subscribed to"""
        channel = self.client.system.getSubscribedBaseChannel(self.key,int(self.serverID))
        channels = [channel['label']]
        for channel in self.client.system.listSubscribedChildChannels(self.key,int(self.serverID)):
            channels.append(channel['label'])
        self.downloadErrata(errata,channels)
        pass

#procedural part starts here
def main():
    """main function - takes in the options and selects the behaviour"""
    import optparse
    parser = optparse.OptionParser("usage : %prog [-e \"errata\" | -l]\n lists all erratas available for the system it is run from or applies an errata")
    parser.add_option("-e", "--errata", dest="errata", default=None, help="specifies which errata to apply")
    parser.add_option("-l", "--list", dest="listing", action="store_true", default=False, help="Displays the list of erratas available for this system")
    (options, args) = parser.parse_args()
    if options.listing:
        rhnsErratas = RhnsErratas()
        rhnsErratas.listAvailable()
    elif not options.errata == None:
        rhnsErrata = RhnsErrata(options.errata)
        rhnsErrata.downloadRelevantPackages(options.errata)
    else:
        parser.error('no action given')


if __name__ == "__main__":
    main()

