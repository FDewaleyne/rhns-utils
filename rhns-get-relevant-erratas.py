#!/usr/bin/python

###
#
# Lists the relevant erratas listed
#
###

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "beta"


import xmlrpclib, sys, getpass
#connection part
class RHNSConnection:

    username = None
    host = None
    url = None
    key = None
    satver = None
    client = None
    closed = False

    def __init__(self,username,password,host,orgname="baseorg"):
        """connects to the satellite db with given parameters"""
        #read configuration
        import ConfigParser,os,re
        config = ConfigParser.ConfigParser()
        config.read(['.satellite', os.path.expanduser('~/.satellite'), '/etc/sysconfig/rhn/satellite'])
        #decide what variable to use for the URL
        if host == None:
            #no host given in command line
            if config.has_section('default') and config.has_option('default', 'url'):
                #there is a config file and it has the settings for the url.
                self.url = config.get('default','url')
            else:
                #there is no config file or no option, default to the local host :
                print "Defaulting to 127.0.0.1"
                self.url = "https://127.0.0.1/rpc/api"
        else:
            #a hostname or url was given in command line. parse it to see if it is correct.
            self.url = host
            if re.match('^http(s)?://[\w\-.]+/rpc/api',self.url) == None:
                #this isn't the full url
                if re.search('^http(s)?://', self.url) == None:
                    self.url = "https://"+self.url
                if re.search('/rpc/api$', self.url) == None:
                    self.url = self.url+"/rpc/api"
            #if this is the url then nothing has to be done further to URL
        from urlparse import urlparse
        self.host = urlparse(self.url).hostname
        #check if there is a username in the options
        if username == None:
            #no username in command line
            if config.has_section(orgname) and config.has_option(orgname, 'username'):
                self.username = config.get(orgname,'username')
            else:
                #not in the config file, we have to prompt it
                sys.stderr.write("Login details for %s\n\n" % self.url)
                sys.stderr.write("Username: ")
                self.username = raw_input().strip()
        else:
            #use the value given in option
            self.username = username
        #now the password
        if password == None:
            #use the password from the config file
            if config.has_section(orgname) and config.has_option(orgname, 'password'):
                self.__password = config.get(orgname,'password')
            else:
                #no password set in the configuration file
                import getpass
                self.__password = getpass.getpass(prompt="Password: ")
                sys.stderr.write("\n")
        else:
            self.__password = password
        #connection part
        self.client = xmlrpclib.Server(self.url)
        self.key = self.client.auth.login(self.username,self.__password)
        try:
            self.satver = self.client.api.systemVersion()
            print "satellite version "+self.satver
        except:
            self.satver = None
            print "unable to detect the version"
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


#TODO: this is a reminder on how to organize the data for the csv export
#end of the class#fetch the data
#print "Fetching the list of systems and the details for each of your system. This may take some time"
#rhn_data={}
#for system in client.system.listUserSystems(key):
#    #gather the details for each system
#    rhn_data[system['id']] = {'id': system['id'], 'last_checkin': system['last_checkin']}
#    #add all the data from getDetails to this dictionary
#   rhn_data[system['id']].update(client.system.getDetails(key,int(system['id'])))
#    #add all the network details as well
#    rhn_data[system['id']].update(client.system.getNetwork(key,int(system['id'])))

def process_some_erratas(conn,systemid,type):
    """fetches all erratas for a system, returns the read erratas - one type only : 'Security Advisory', 'Product Enhancement Advisory' or 'Bug Fix Advisory' """
    data = dict()
    for errata in conn.client.system.getRelevantErrataByType(conn.key,systemid,type):
        data[errata[id]]=errata
        #contents of an errata at this stage :
        # - int "id" - Errata ID.
        # - string "date" - Date erratum was created.
        # - string "update_date" - Date erratum was updated.
        # - string "advisory_synopsis" - Summary of the erratum.
        # - string "advisory_type" - Type label such as Security, Bug Fix
        # - string "advisory_name" - Name such as RHSA, etc
    return _read_errata(conn,data)

def process_all_erratas(conn,systemid):
    """fetches all erratas for a system, returns the read erratas."""
    data = dict()
    for errata in conn.client.system.getRelevantErrata(conn.key,systemid):
        data[errata[id]]=errata
        #contents of an errata at this stage :
        # - int "id" - Errata ID.
        # - string "date" - Date erratum was created.
        # - string "update_date" - Date erratum was updated.
        # - string "advisory_synopsis" - Summary of the erratum.
        # - string "advisory_type" - Type label such as Security, Bug Fix
        # - string "advisory_name" - Name such as RHSA, etc
    return _read_errata(conn,data)

def _read_errata(client,erratas):
    """treats the list of erratas and returns the object wanted to be processed for display or csvcreate"""
    pass

def csv_create(filename,data):
    """creates a csv file with the data provided"""
    print "Writing data to the csv file"
    #TODO: redo headers 
    headers=['id' , 'profile_name', 'hostname', 'ip', 'last_checkin', 'base_entitlement', 'description', 'adress1','adress2', 'city', 'state', 'country', 'building', 'room', 'rack']
    import csv
    csvfile = open('systems_'+login+'.csv', 'wb' )
    csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    csv_writer.writerow(headers)
    #browse the errata data depending on the header
    for errata in data.itervalues():
        line = []
        for value in headers:
            line.append(errata.get(value))
        csv_writer.writerow(line)
        del line
    del data
    pass

# start main function
def main(version):
    """main function - takes in the options and selects the behaviour"""
    global verbose;
    import optparse
    parser = optparse.OptionParser("%prog [-s systemid] [-e erratatype] [-o file.csv]\n Outputs the list of erratas available for a machine depending on the options selected", version=version)
    parser.add_option("-s", "--systemid", dest="systemid", type="int", default=None, help="Uses that systemid instead of the value extracted from the system's systemid file")
    parser.add_option("-e", "--erratatype", dest="erratatype", default=None, help="Type of Errata to use. Default to all, can be limited to 'Security Advisory', 'Product Enhancement Advisory' or 'Bug Fix Advisory' ; also accepted the shortenned versions 'security', 'enhangement' and 'bugfix'")
    parser.add_option("-o", "--output", dest="output",default=None, help="Name of the csv file to generate - if not used, will display output on terminal")
    #connection config group
    connectgroup = OptionGroup(parser,"Connection Options", "These options can be used to specify what server to connect to")
    connectgroup.add_option("-H", "--url", dest="saturl",default=None, help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    connectgroup.add_option("-U", "--user", dest="satuser",default=None, help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    connectgroup.add_option("-P", "--password", dest="satpwd",default=None, help="password of the user. Will be asked if not given and not in the configuration file.")
    connectgroup.add_option("-O", "--org", dest="satorg", default="baseorg", help="name of the organization to use - design the section of the config file to use. Facultative, defaults to %default")
    parser.add_option_group(connectgroup)
    #debug options
    debuggroup = OptionGroup(parser,"Debugging Option", "these options can be used to collect debugging information")
    debuggroup.add_option("-v","--verbose",dest="verbose",default=False,action="store_true",help="activate verbose output")
    parser.add_option_group(debuggroup)
    #parse everything
    (options, args) = parser.parse_args()
    #set verbosity globally
    verbose = options.verbose
    #set the systemid
    if options.systemid == None:
        systemid = getsystemid()
    else:
        systemid = options.systemid
    #session init
    conn = RHNSConnection(options.satuser,options.satpwd,options.saturl,options.satorg)
    if options.erratatype == None:
        #select all
    elif options.erratatype in ('Security Advisory','security advisory', 'security'):
        #select all security advisories
    elif options.erratatype in ('Product Enhancement Advisory', 'product enhancement advisory', 'enhancement'):
        #select all product enhancement advisories
    elif options.erratatype in ('Bug Fix Advisory', 'bug fix advisory', 'bugfix'):
        #select bugfix advisories
    else:
        sys.stderr.write("Incorrect errata type, use 'Security Advisory', 'Product Enhancement Advisory' or 'Bug Fix Advisory' ; also accepted the shortenned versions 'security', 'enhangement' and 'bugfix'")
        #list all erratas
    client.auth.logout(key)
    if options.output != None:
        #print data
    else:
        if verbose:
            #print data
        #create file
    conn.close()
    pass

if __name__ == "__main__":
    main(__version__)

