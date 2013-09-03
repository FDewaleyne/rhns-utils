#!/usr/bin/python


###
#
# Clones into the destination the erratas of the origin that are from between startdate and enddate
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

class RHNSConnection:


    def __init__(self,user,password,host):
        """connects to the satellite db with given parameters"""
        #transformation of saturl into a full url if only given the hostname or an ip adress
        if re.match('^http(s)?://[\w\-.]+/rpc/api',host) == None:
            if re.search('^http(s)?://', host) == None:
                URL = "https://"+host
            else:
                URL = host
            if re.search('/rpc/api$', URL) == None:
                URL = URL+"/rpc/api"
        self.client = xmlrpclib.Server(URL)
        self.key = self.client.auth.login(user,password)
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
        if not self.closed :
            self.client.auth.logout(self.key)
            print "connection closed"
        pass

def confirm(question):
    """asks a question 3 times then returns the answer"""
    loop = 0
    test = False
    while loop < 3:
        loop += 1
        answer = raw_input(question.' (y/n):').strip()
        if answer.lower() in ['y','yes']:
            test = True
            break
        elif answer.lower() in ['n','no']:
            break
    return test

def main(versioninfo):
    import optparse
    parser = optparse.OptionParser(description="Usage: %prog [options]\nThis program will add all packages that aren't provided by an errata in the origin to the destination depending on which settings are used", version="%prog "+versioninfo)
    parser.add_option("--url", dest="saturl",default="localhost", help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    parser.add_option("--user", dest="satuser",default=None, help="username to use with the satellite. Should be admin of the organization owning the channels (required)")
    parser.add_option("--password", dest="satpwd",default=None, help="password of the user (required)")
    parser.add_option("--startdate",dest="startdate",default=None, help="the start date in YYYY-MM-DD. don't omit if using enddate")
    parser.add_option("--enddate",dest="enddate",default=None, help="the end date in YYYY-MM-DD. don't omit if using startdate")
    parser.add_option("--source",dest="source",default=None, help="the source channel to use (required)")
    parser.add_option("--destination",dest="destination",default=None, help="the destination channel to use (required)")
    parser.add_option("--errata",dest="erratas",action="append",default=[],help="the advisory to add (e.g. RHBA-2013:1438). Can be called multiple times.")
    (options, args) = parser.parse_args()
    if options.source == None or options.destination == None or options.satuser == None or options.satpwd == None:
        parser.error('missing required parameters detected - use -h for help')
    else:
        conn = RHNSConnection(options.satuser,options.satpwd,options.saturl)
        print "starting the operation, it may take a while"
        if len(options.erratas) > 0:
            if confirm("merging erratas given as parmeter ?"):
                conn.client.channel.software.mergeErrata(conn.key,options.source,options.destination,options.erratas)
        elif options.startdate != None and options.enddate != None:
            ifconfirm("merging erratas from "+options.startdate+" to "+options.enddate+" ?"):
                conn.client.channel.software.mergeErrata(conn.key,options.source,options.destination,options.startdate,options.enddate)
        else:
            if confirm( "merging all erratas ?"):
                conn.client.channel.software.mergeErrata(conn.key,options.source,options.destination)
 
#calls start here
if __name__=="__main__":
    main(__version__)
