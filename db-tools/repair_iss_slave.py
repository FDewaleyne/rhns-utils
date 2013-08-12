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
    # part relevant to path
    query = """
    select id from rhnpackage where path is null
    """
    cursor = rhnSQL.prepare(query)
    cursor.execute()
    rows = cursor.fetchall_dict()
    list_ids = []
    print "calculating which packages have no path in the database"
    if not rows is None:
        c = 0
        for row in rows:
            c += 1
            list_ids.append(row['id'])
            print "\r%s of %s" % (str(c), str(len(rows))),
        print ""
    else:
        print "no packages with no path"
    #part relevant to the duplicated packages
    query = """
        select  rpka.package_id as "id", rpn.name||'-'||rpe.version||'-'||rpe.release||'.'||rpa.label as package,
                rpka.key_id, rpk.key_id as signing_key,
                coalesce((select name from rhnpackageprovider rpp where rpp.id = rpk.provider_id),'Unknown') as provider,
                rpka.created, rpka.modified
        from    rhnpackagekeyassociation rpka, rhnpackage rp, rhnpackagename rpn, rhnpackagekey rpk, rhnpackageevr rpe, rhnpackagearch rpa,
                (select package_id,count(*) from rhnpackagekeyassociation group by package_id having count(*) > 1) dups 
        where   rpka.package_id = dups.package_id
        and     rpka.package_id = rp.id
        and     rpka.key_id = rpk.id
        and     rp.name_id = rpn.id
        and     rp.evr_id = rpe.id
        and     rp.package_arch_id = rpa.id
        order by 1, 3
    """
    print "calculating which packages are duplicates and have unknown providers"
    cursor = rhnSQL.prepare(query)
    cursor.execute()
    rows = cursor.fetchall_dict()
    if not rows is None:
        c = 0
        for row in rows:
            c += 1
            if not row['id'] in list_ids:
                list_ids.append(row['id'])
            print "\r%s of %s" % (str(c),str(len(rows))),
        print ""
    else:
        print "no duplicates with an unknown provider detected"
    return list_ids


#the main function of the program
def main(versioninfo):
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
        try:
            conn.client.channel.software.create(conn.key,options.destChannel,options.destChannel,options.destChannel,"channel-x86_64","","sha1")
        except:
            print "unable to create the channel "+options.destChannel+" ... attempting to continue"
            pass
        ids = gen_idlist()
        if len(ids) == 0:
            print "nothing to do"
        else:
            print "adding "+str(len(ids))+" packages to the channel "
            conn.client.channel.software.addPackages(conn.key,options.destChannel,ids)
            print "remember to backup before deleting"
        conn.close()

if __name__ == "__main__":
    main(__version__)

