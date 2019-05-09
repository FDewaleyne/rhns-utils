#!/usr/bin/python


###
#
# Clones into the destination the packages of the origin that are from between startdate and enddate but are not provided by any errata.
# This allows to have full clones along with spacewalk-clone-by-date
#
###
# pylint: disable = line-too-long
__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "prod"


import xmlrpclib, re

class RHNSConnection:


    def __init__(self, user, password, host):
        """connects to the satellite db with given parameters"""
        #transformation of saturl into a full url if only given the hostname or an ip adress
        if re.match('^http(s)?://[\w\-.]+/rpc/api', host) == None:
            if re.search('^http(s)?://', host) == None:
                URL = "https://"+host
            else:
                URL = host
            if re.search('/rpc/api$', URL) == None:
                URL = URL+"/rpc/api"
        self.client = xmlrpclib.Server(URL)
        self.key = self.client.auth.login(user, password)
        self.closed = False
        self.user = user
        self.host = host
        pass

    def close(self):
        """closes a connection. item can be destroyed then"""
        self.client.auth.logout(self.key)
        self.closed = True
        pass

    def __exit__(self):
        """closes connection on exit"""
        if not self.closed:
            self.client.auth.logout(self.key)
            print "connection closed"
        pass

def copy_into_channel(conn, channel, packages):
    """adds the packages into the channel. packages is a list of package ids"""
    content_destination = conn.client.channel.software.listAllPackages(conn.key, channel)
    for package in content_destination:
        if package['id'] in packages:
            packages.remove(package['id'])
    if len(packages) > 0:
        print "Adding "+str(len(packages))+" packages to "+channel
        conn.client.channel.software.addPackages(conn.key, channel, packages)
    else:
        print "all packages already in the channel"

def get_ids(conn, channel, startdate=None, enddate=None):
    """returns the list of packages that have no errata."""
    if not startdate == None and not enddate == None:
        content = conn.client.channel.software.listAllPackages(conn.key, channel, startdate, enddate)
    elif enddate == None and not startdate == None:
        content = conn.client.channel.software.listAllPackages(conn.key, channel, startdate)
    else:
        content = conn.client.channel.software.listAllPackages(conn.key, channel)
    packages_noerrata = []
    for package in content:
        if len(conn.client.packages.listProvidingErrata(conn.key, package['id'])) == 0:
            packages_noerrata.append(package['id'])
    return packages_noerrata

def main(versioninfo):
    import optparse
    parser = optparse.OptionParser(description="Usage: %prog [options]\nThis program will add all packages that aren't provided by an errata in the origin to the destination depending on which settings are used", version="%prog "+versioninfo)
    parser.add_option("--url", dest="saturl", default="localhost", help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    parser.add_option("--user", dest="satuser", default=None, help="username to use with the satellite. Should be admin of the organization owning the channels (required)")
    parser.add_option("--password", dest="satpwd", default=None, help="password of the user (required)")
    parser.add_option("--startdate", dest="startdate", default=None, help="the start date in YYYY-MM-DD. If omitted will use all packages of the origin!")
    parser.add_option("--enddate", dest="enddate", default=None, help="the end date in YYYY-MM-DD. If omitted will use all packages since startdate!")
    parser.add_option("--source", dest="source", default=None, help="the source channel to use (required)")
    parser.add_option("--destination", dest="destination", default=None, help="the destination channel to use (required)")
    (options, args) = parser.parse_args()
    if options.source == None or options.destination == None or options.satuser == None or options.satpwd == None:
        parser.error('missing required parameters detected - use -h for help')
    else:
        conn = RHNSConnection(options.satuser, options.satpwd, options.saturl)
        print "starting the operation, it may take a while"
        copy_into_channel(conn, options.destination, get_ids(conn, options.source, options.startdate, options.enddate))

#calls start here
if __name__ == "__main__":
    main(__version__)
