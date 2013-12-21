#!/usr/bin/python

###
#
# WARNING DO A BACKUP OF THE DB BEFORE USING THIS SCRIPT
# SHOULD ONLY BE USED WHEN ASKED TO BY SUPPORT
#
###
###
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
###

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "prod"
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
        self.username = username
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

def gen_idlist_from_paths(pathfile):
    """generates the list of package IDs from a file with all paths inside it."""
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
                select id from rhnpackage where path like :apath
    """
    #read the file
    pkglistfile=open(options.file,"rb")
    pkgline=pkglistfile.readline()
    pkgpaths=[]
    while pkgline:
        pkgpaths.append(pkgline.rstrip("\n"))
        pkgline=pkglistfile.readline()
    pkglistfile.close()
    #init the db, init the list
    list_ids = []
    cursor = rhnSQL.prepare(query)
    for apath in pkgpaths:
        cursor.execute(apath=apath)
        rows = cursor.fetchall_dict()
        if not rows is None:
            c = 0
            for row in rows:
                c += 1
                list_ids.append(row['id'])
                print "\r%s of %s" % (str(c), str(len(rows))),
            print ""
        else:
            print "no entry found for "
    return list_ids

def gen_idlist_from_keyid_by_packageid(packageid):
    """docstring for gen_idlist_from_keyid_by_packageid"""
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
                select  rpka.package_id as "id", rpn.name||'-'||rpe.version||'-'||rpe.release||'.'||rpa.label as package,
                rpka.key_id, rpk.key_id as signing_key,
                coalesce((select name from rhnpackageprovider rpp where rpp.id = rpk.provider_id),'Unknown') as provider,
                rpka.created, rpka.modified
        from    rhnpackagekeyassociation rpka, rhnpackage rp, rhnpackagename rpn, rhnpackagekey rpk, rhnpackageevr rpe, rhnpackagearch rpa,
                (select key_id from rhnpackagekeyassociation where package_id = """+str(packageid)+""" ) pkginfo
        where   rpka.package_id = rp.id
        and     rpka.key_id = rpk.id
        and     rp.name_id = rpn.id
        and     rp.evr_id = rpe.id
        and     rp.package_arch_id = rpa.id
        and     rpk.id = pkginfo.key_id 
    """
    cursor = rhnSQL.prepare(query)
    cursor.execute()
    rows = cursor.fetchall_dict()
    list_ids = []
    if not rows is None:
        c = 0
        for row in rows:
            c += 1
            list_ids.append(row['id'])
            print "\r%s of %s" % (str(c), str(len(rows))),
        print ""
    else:
        print "no packages found"
    return list_ids


def gen_idlist_for_keyid(keyid = None):
    """generates the list of package IDs that have a certain keyid or no keyid if it is None"""
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
    if keyid != None:
        # query to select all packages with the same key
        query = """
                select  rpka.package_id as "id", rpn.name||'-'||rpe.version||'-'||rpe.release||'.'||rpa.label as package,
                rpka.key_id, rpk.key_id as signing_key,
                coalesce((select name from rhnpackageprovider rpp where rpp.id = rpk.provider_id),'Unknown') as provider,
                rpka.created, rpka.modified
        from    rhnpackagekeyassociation rpka, rhnpackage rp, rhnpackagename rpn, rhnpackagekey rpk, rhnpackageevr rpe, rhnpackagearch rpa
        where   rpka.package_id = rp.id
        and     rpka.key_id = rpk.id
        and     rp.name_id = rpn.id
        and     rp.evr_id = rpe.id
        and     rp.package_arch_id = rpa.id
        and     rpk.id = """+str(keyid)+"""
        """
    else:
        # query to select all packages with no keyid - will probably not return anything. Will probably never be used, but if it's required it's already there
        query = """
        select  rpka.package_id as "id", rpn.name||'-'||rpe.version||'-'||rpe.release||'.'||rpa.label as package,
                rpka.key_id, rpk.key_id as signing_key,
                coalesce((select name from rhnpackageprovider rpp where rpp.id = rpk.provider_id),'Unknown') as provider,
                rpka.created, rpka.modified
        from    rhnpackagekeyassociation rpka, rhnpackage rp, rhnpackagename rpn, rhnpackagekey rpk, rhnpackageevr rpe, rhnpackagearch rpa
        where   rpka.package_id = rp.id
        and     rpka.key_id = rpk.id
        and     rp.name_id = rpn.id
        and     rp.evr_id = rpe.id
        and     rp.package_arch_id = rpa.id
        and     rpk.id = NULL
        """
    cursor = rhnSQL.prepare(query)
    cursor.execute()
    rows = cursor.fetchall_dict()
    list_ids = []
    if not rows is None:
        c = 0
        for row in rows:
            c += 1
            list_ids.append(row['id'])
            print "\r%s of %s" % (str(c), str(len(rows))),
        print ""
    else:
        print "no packages found"
    return list_ids

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
            print "\r%s of %s" % (str(int(round(c/2))),str(int(len(rows)/2))),
        print ""
    else:
        print "no duplicates with an unknown provider detected"
    return list_ids

def getChannelArch(arch):
    """returns a value if it is a compatible channel or just None"""
    if arch in ['ia32', 'ia64', 'sparc', 'alpha', 's390', 's390x', 'iSeries', 'pSeries', 'x86_64', 'ppc', 'sparc-sun-solaris', 'i386-sun-solaris']:
        return "channel-"+arch
    else:
        return None
    pass

def matchArch(arch):
    """returns what a package architecture should be for that arch value"""
    # this is likely not going to work for everyone but it should cover most cases. 
    if arch == 'ia32':
        return ["i686","i386","noarch"]
    elif arch == 'ia64':
        return ["x86_64","noarch"]
    elif arch == 'x86_64':
        return ["i386","i686","x86_64","noarch"]
    #may need exceptions for *-sun-solaris and other archs - don't have any packages for these right now
    else:
        #that should work for most cases
        return [arch, "noarch"]
    pass

def filterPackagesByArch(ids,arch,conn):
    """filters the packages depending on the architecture selected"""
    global verbose
    #grab a list of the valid archs since some architectures selected could accept i386 and x86_64 packages
    testarchs = matchArch(arch)
    filtered_ids = []
    for id in ids:
        try:
            details = conn.client.packages.getDetails(conn.key, id)
            if verbose:
                print str(id)+" : "+details['name']+'-'+details['version']+'-'+details['release']+'.'+details['epoch']+'.'+details['arch_label']
            if details['arch_label'] in testarchs:
                filtered_ids.append(id)
        except:
            print "unable to find package id "+str(id)+", ignoring it and continueing"
            pass 
    return filtered_ids

#the main function of the program
def main(versioninfo):
    import optparse
    parser = optparse.OptionParser(description="Usage: %prog [options]\nThis program will clone all erratas and packages from the source to the destination as long as they are not already present in the destiation, depending on which settings are used\n REMEMBER TO BACKUP YOUR DATABASE", version="%prog "+versioninfo)
    parser.add_option("-H", "--host", dest="sathost", type="string", help="hostname of the satellite to use, preferably a fqdn e.g. satellite.example.com", default="localhost")
    parser.add_option("-l", "--login", dest="satuser", type="string", help="User to connect to satellite")
    parser.add_option("-p", "--password", dest="satpwd", type="string", help="Password to connect to satellite")
    parser.add_option("-c", "--destChannel", dest="destChannel", default="to_delete",  type="string", help="Channel to populate with the packages that don't have a path")
    parser.add_option("-A", "--arch",dest="arch", default="x86_64", type="string", help="Architecture to use when creating the channel and filtering packages. Defaults to x86_64 which accepts 64 and 32 bits packages")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Enables debug output")
    parser.add_option("--keyid", dest="keyid", type="int", help="Focuses on all the packages signed by the keyid provided. Only use if you know already what keyid to remove - value to use changes from database to database.")
    parser.add_option("--nullkeyid", dest="nullkeyid", action="store_true", default=False, help="Focuses on all packages with no key id")
    parser.add_option("--packageid", dest="packageid", type="int", help="Focuses on the packages with the same signature as this package")
    parser.add_option("--packagefile", dest="packagefile", type="string", help="Focuses on the packages with a path identical to the entries in a file")
    (options, args) = parser.parse_args()
    channel_arch = getChannelArch(options.arch)
    global verbose 
    verbose = options.verbose
    if not options.satuser or not options.satpwd:
        parser.error('username and password are required options.')
    elif channel_arch == None:
        parser.error('invalid architecture, accepted values are ia32, ia64, sparc, alpha, s390, s390x, iSeries, pSeries, x86_64, ppc, sparc-sun-solaris or i386-sun-solaris.\nPlease refer to the API documentation on software.channel.create for more information')
    else:
        #init
        conn = RHNSConnection(options.satuser,options.satpwd,options.sathost)
        channel_arch = getChannelArch(options.arch)
        try:
            conn.client.channel.software.create(conn.key,options.destChannel,options.destChannel,options.destChannel,channel_arch,"","sha1")
        except:
            cdetails = conn.client.channel.software.getDetails(conn.key,options.destChannel)
            if arch == cdetails['arch_name'] :
                print "unable to create the channel "+options.destChannel+" ... attempting to continue"
                pass
            else:
                print "unable to create the channel "+options.destChannel+" as arch "+options.arch+" ; stopping here"
                raise
        if options.packageid != None :
            ids = gen_idlist_from_keyid_by_packageid(options.packageid)
        elif options.nullkeyid :
            ids = gen_idlist_for_keyid()
        elif options.keyid != None:
            ids = gen_idlist_for_keyid(options.keyid)
        elif options.packagefile != None:
            ids = gen_idlist_from_paths(options.packagefile)
        else:
            #default mode, filter packages present in duplicate as beta and regular but also packages with null paths
            ids = gen_idlist()
        if len(ids) == 0:
            print "nothing to do"
        else:
            filtered_ids = filterPackagesByArch(ids,options.arch,conn)
            print "found "+str(len(ids))+" packages to remove, adding "+str(len(filtered_ids))+" to the channel "+options.destChannel
            conn.client.channel.software.addPackages(conn.key,options.destChannel,filtered_ids)
            print "remember to backup before deleting"
        conn.close()

if __name__ == "__main__":
    main(__version__)

