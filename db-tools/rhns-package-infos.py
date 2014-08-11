#!/usr/bin/python

# script aimed at running a couple sql commands against satellite 5.6 to fetch info for a package we have ID from
__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.1beta"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "prod"


def package_details(packageid):
    """displays the details for that package id"""
    #db access
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
            print "Couldn't load the modules required to connect to the db"
        sys.exit(1)
    rhnConfig.initCFG()
    rhnSQL.initDB()

   query="""
    select  
        rp.id as "package_id",  
        rpn.name||'-'||rpe.version||'-'||rpe.release||'.'||rpa.label as "package",  
        rc.label as "channel_label",  
        rc.id as "channel_id",  
        coalesce((select name from rhnpackageprovider rpp where rpp.id = rpk.provider_id),'Unknown') as "provider"  
    from rhnpackage rp  
        inner join rhnpackagename rpn on rpn.id = rp.name_id  
        inner join rhnpackageevr rpe on rpe.id = rp.evr_id  
        inner join rhnpackagearch rpa on rpa.id = rp.package_arch_id  
        left outer join rhnchannelpackage rcp on rcp.package_id = rp.id  
        left outer join rhnchannel rc on rc.id = rcp.channel_id  
        left outer join rhnpackagekeyassociation rpka on rpka.package_id = rp.id  
        inner join rhnpackagekey rpk on rpk.id = rpka.key_id  
    where rp.id = :packageid  
        order by 2, 3;  
    """
    cursor = dbaccess.prepare(query)
    cursor.execute(packageid=packageid)
    rows = cursor.fetchall_dict()
    if not rows is None:
        c = 0
        print "Package %d : %s" % (row[0]['package_id'],rows[0]['package'])
        for row in rows:
            c += 1
            if row.channel_id != None:
                pkg_channels[row['channel_id']] = row['channel_label']
                pkg_provider[row['channel_id']] = row['provider']
            else:
                pkg_channel[0] = "Not in a channel"
                pkg_provider[0] = row['provider']
            print "\r%s of %s" % (str(c), str(len(rows))),
        print "Provided by channels : %s" % (pkg_channels.join(', '))
        print "With providers (same order): %s" % (pkg_provider.join(', '))
    else:
        print "no package found for the id %d" % (packageid)


#the main function of the program
def main(versioninfo):
    import optparse
    parser = optparse.OptionParser(description="This script will output informations related to a specific package, using the database directly", version="%prog "+versioninfo)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Enables debug output")
    parser.add_option("-p", "--packageid",dest="packageid",type="int",action="store",help="the package ID to get info from")
    parser.add_option_group(advanced_group)
    (options, args) = parser.parse_args()
    channel_arch = getChannelArch(options.arch)
    global verbose 
    verbose = options.verbose
    if not options.packageid :
        parser.error('A package ID is required.')
    else:
        

if __name__ == "__main__":
    main(__version__)

