#!/usr/bin/python

###
#
# Lists the snapshots of a system ID or displays its content into a format that can be then used with yum.
# Packages only.
#
###

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "dev"

import xmlrpclib, re

#connector class -used to initiate a connection to a satellite and to send the proper satellite the proper commands
class RHNSConnection:

    #_username = None
    #_host = None
    #_key = None
    #_client = None
    #__closed = False

    def __init__(self,username,password,host):
        """connects to the satellite db with given parameters"""
        #format the url if a part is missing
        SATELLITE_URL = host
        if re.match('^http(s)?://[\w\-.]+/rpc/api',SATELLITE_URL) == None:
            if re.search('^http(s)?://', SATELLITE_URL) == None:
                SATELLITE_URL = "https://"+SATELLITE_URL
            if re.search('/rpc/api$', SATELLITE_URL) == None:
                SATELLITE_URL = SATELLITE_URL+"/rpc/api"
        self._client = xmlrpclib.Server(URL)
        self._key = self._client.auth.login(username,password)
        self._username = username
        self._host = host
        self.__closed = False
        pass

    def close(self):
        """closes a connection. item can be destroyed then"""
        self._client.auth.logout(self._key)
        self.__closed = True
        pass

    def __exit__(self):
        """closes connection on exit"""
        if not self.__closed :
            self._client.auth.logout(self._key)
        pass

class RHNSSnapshot:

    #__conn : RHNCConnection object
    #_snapid : the id of the snapshot
    #_packages : the list of packages (dict of name version release epoch arch)

    def __init__(self,snapid, conn):
        """populates the object on creation"""
        self.__conn = conn
        self._snapid = snapid
        self._packages = self.__conn._client.system.provisioning.snapshot.listSnapshotPackages(self.__conn._key, snapid)
        #TODO: here place handlers for config files another time
        pass

    def printPackages(self):
        """displays the list of packages using the NVREA format"""
        print "List of packages for snapshot "+str(self._snapid)+":"
        for package in self._packages:
            print " %s-%s-%s.%s" % (package['name'],package['version'],package['release'],package['arch'])
        pass

class RHNSSnapshots:
    
    #__conn : connection
    #_snaplist : list of snapshots - disctionaries with snapid, reason, date, list of chanenls, list of groups, list of entitlements, list of config channels, list of tags and invalid_reason if it exists
    #_sysid : the system id

    def __init__(self,sysid,conn):
        """list of snapshots for a system"""
        self.__conn = conn
        self._sysid = sysid
        self._snaplist = self.__conn.client.system.provisioning.snapshot.listSnapshots(__conn._key, sysid)
        pass

    def printList(self):
        """displays the list of snapshots for that system"""
        print "List of snapshots for system "+str(_sysid)
        print " ID - date - reason - channels - tags"
        for snapshot in self._snaplist:
            if snapshot.get('invalid_reason') == None:
                reason = snapshot['reason']
            else:
                reason = snapshot['reason']+' F ('+ snapshot['invalid_reason']+')'
            print " %s - %s - %s - %s" % (str(snapshot['id']), str(snapshot['created']), ','.join(snapshot['channels']), ','.join(snapshot['tags']))
        pass

def __main__(__version__):
    """main function"""
    import optparse
    parser = optparse.OptionParser(description="Usage: %prog [options]\nThis program will clone all erratas and packages from the source to the destination as long as they are not already present in the destiation, depending on which settings are used", version="%prog "+versioninfo)
    parser.add_option("-u", "--url", dest="saturl", type="string", help="url or hostname of the satellite to use e.g. http://satellite.example.com/rpc/api", default="https://127.0.0.1/rpc/api")
    parser.add_option("-l", "--login", dest="satuser", type="string", help="User to connect to satellite")
    parser.add_option("-p", "--password", dest="satpwd", type="string", help="Password to connect to satellite")
    parser.add_option("--list", dest="listing", action="store_true", help="lists the snapshots for the system")
    parser.add_option("--sysid", dest="sysid", type="string", help="ID of the system to use (required)")
    (options, args) = parser.parse_args()
    #check for the required options
    if options.satuser != None  and options.satpwd != None and options.sysid != None:
        #do the magic
    else:
        parser.error('Missing parameters - make sure user, password and systemid are given. use -h for help.')
    pass

if __name__ == "__main__":
    main(__version__)

