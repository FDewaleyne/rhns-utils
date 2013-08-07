#!/usr/bin/python

###
#
# WARNING not to be used without a good reason can break the satellite and will break support.
# DO A BACKUP OF THE DB BEFORE USING THIS
#
###
#
# meant to be use with satellite 5.4.1 on a rhel5 64bits.
#
###

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

    username = None
    host = None
    key = None
    client = None
    closed = False

    def __init__(self,username,password,host):
        """connects to the satellite db with given parameters"""
        URL = "https://%s/rpc/api" % host
        self.client = xmlrpclib.Server(URL)
        self.key = self.client.auth.login(username,password)
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

def gen_idlist():
    """generates the list of package IDs"""
    import sys
    sys.path.append("/usr/share/rhn")
    try:
            import spacewalk.common.rhnConfig as rhnConfig
            import spacewalk.server.rhnSQL as rhnSQL
    except ImportError:
        try:
            import common.rhnConfig as rhnConfig
            import server.rhnSQL as rhnSQL
        except ImportError:
            print "Couldn't load the libraries required to connect to the db"
            sys.exit(1)

    rhnConfig.initCFG()
    rhnSQL.initDB()


    query = """
    select id from rhnpackage where path is null
    """
    cursor = rhnSQL.prepare(query)
    cursor.execute()
    rows = cursor.fetchall_dict()

    list_ids = []
    if not rows is None:
        for row in rows:
            list_ids.append(row['id'])
    return list_ids


#the main function of the program
def main(versioninfo):
    #TODO : move to argparse for RHEL7
    import optparse
    parser = optparse.OptionParser(description="Usage: %prog [options]\nThis program will clone all erratas and packages from the source to the destination as long as they are not already present in the destiation, depending on which settings are used", version="%prog "+versioninfo)
    parser.add_option("-H", "--host", dest="sathost", type="string", help="hostname of the satellite to use, preferably a fqdn e.g. satellite.example.com", default="localhost")
    parser.add_option("-l", "--login", dest="satuser", type="string", help="User to connect to satellite")
    parser.add_option("-p", "--password", dest="satpwd", type="string", help="Password to connect to satellite")
    parser.add_option("-c", "--destChannel", dest="destChannel", default="to_delete",  type="string", help="Channel to populate with the packages that don't have a path")
    (options, args) = parser.parse_args()
    if not options.satuser or not options.satpwd:
        parser.error('username and password are required options.')
    else:
        #init
        conn = RHNSConnection(options.satuser,options.satpwd,options.sathost)
        ids = gen_idlist()
        if len(ids) == 0:
            print "nothing to do"
        else:
            print "adding "+str(len(ids))+" packages to the channel "
            conn.client.channel.software.addPackages(conn.key,options.destChannel,ids)
        conn.close()

if __name__ == "__main__":
    main(__version__)

