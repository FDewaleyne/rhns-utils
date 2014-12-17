#!/usr/bin/python

###
#
# Lists the relevant erratas listed
#
###

__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "prod"


import xmlrpclib, sys
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
        import ConfigParser, os, re
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
            if re.match('^http(s)?://[\w\-.]+/rpc/api', self.url) == None:
                #this isn't the full url
                if re.search('^http(s)?://', self.url) == None:
                    self.url = "https://" + self.url
                if re.search('/rpc/api$', self.url) == None:
                    self.url = self.url+"/rpc/api"
            #if this is the url then nothing has to be done further to URL
        from urlparse import urlparse
        self.host = urlparse(self.url).hostname
        #check if there is a username in the options
        if username == None:
            #no username in command line
            if config.has_section(orgname) and config.has_option(orgname, 'username'):
                self.username = config.get(orgname, 'username')
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
                self.__password = config.get(orgname, 'password')
            else:
                #no password set in the configuration file
                import getpass
                self.__password = getpass.getpass( prompt = "Password: ")
                sys.stderr.write("\n")
        else:
            self.__password = password
        #connection part
        self.client = xmlrpclib.Server(self.url)
        self.key = self.client.auth.login(self.username,self.__password)
        try:
            self.satver = self.client.api.systemVersion()
            print "satellite version "+self.satver
        except xmlrpclib.Fault:
            self.satver = None
            print "unable to detect the version"

    def close(self):
        """closes a connection. item can be destroyed then"""
        self.client.auth.logout(self.key)
        self.closed = True

def get_systemid():
    """fetches the systemid of the system if a systemid file exists"""
    import fileinput, re
    systemid = None
    try:
        for line in fileinput.input("/etc/sysconfig/rhn/systemid"):
            m = re.search('ID-(\d+)', line)
            if m:
                systemid = int(m.group(1))
                break
            else:
                pass
    except:
        sys.stderr.write("failed to read the systemid from /etc/sysconfig/rhn/systemid")
        raise
    return int(systemid)

def process_all_systems(conn):
    """fetches the list of systems and calls on each the collection that will fill the array, then return the array of systems."""
    data = dict()
    #extract the scores from the api, then adds the name of the system on top of that 
    for system in conn.client.system.getSystemCurrencyScores(conn.key):
        data[system['sid']] = _system_facts(system)
        facts = conn.client.system.getName(system['sid'])
        data[system['sid']].update({ 'system name': facts['name'], 'id': str(facts['id']), 'last checkin': str(facts['last_checkin'])})
    return data

def _system_facts(element):
    """fetches the details of the system and returns them as a dictionary object"""
    #all updates : numer of updates
    #security errata : number of security errata
    #bugfix errata : number of bugfix errata
    #enhancement errata : number of enhancement errata
    data = dict()
    data['all updates'] = element['enh'] + element['imp'] + element['low'] + element['crit'] + element['bug'] + element['mod']
    data['security errata'] = element['imp'] + element['mod'] + element['low']
    data['bugfix errata'] = element['bug']
    data['enhancement errata'] = element['enh']
    return data

def csv_create(filename, data):
    """creates a csv file with the data provided"""
    print "Writing data to the csv file"
    headers = [ 'system name', 'all updates', 'security errata', 'bugfix errata' , 'enhancement errata', 'last checkin']
    #there may be more information read - depending what is neede
    import csv,re
    csvfile = open(filename, 'wb' )
    csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting = csv.QUOTE_NONNUMERIC)
    csv_writer.writerow(headers)
    #browse the errata data depending on the header
    for errata in data.itervalues():
        line = []
        for value in headers:
            lval = errata.get(value)
            if isinstance(lval, basestring):
                #encode in utf-8
                line.append(lval.encode('utf-8'))
            else:
                line.append(errata.get(value))
        csv_writer.writerow(line)
        del line

def print_data(data):
    """Displays on screen the information read"""
    print " %50s | %5d | %5d | %5d | %5d | %s" % ('system name', 'all updates', 'security errata', 'bugfix errata' , 'enhancement errata', 'last checkin')
    for line in data.itervalues():
        print " %50s | %5d | %5d | %5d | %5d | %s" % (line['system name'], line['all updates'], line['security errata'], line['bugfix errata'], line['enhancement errata'], line['last checkin'])

# start main function
def main(version):
    """main function - takes in the options and selects the behaviour"""
    global verbose
    import optparse
    parser = optparse.OptionParser("%prog [-s systemid] [-o file.csv]\n Outputs the list of erratas available for a machine depending on the options selected", version=version)
    parser.add_option("-o", "--output", dest="output", default=None, help="Name of the csv file to generate - if not used, will display output on terminal")
    #connection config group
    connectgroup = optparse.OptionGroup(parser,"Connection Options", "These options can be used to specify what server to connect to")
    connectgroup.add_option("-H", "--url", dest="saturl",default=None, help="URL of the satellite api, e.g. https://satellite.example.com/rpc/api or http://127.0.0.1/rpc/api ; can also be just the hostname or ip of the satellite. Facultative.")
    connectgroup.add_option("-U", "--user", dest="satuser",default=None, help="username to use with the satellite. Should be admin of the organization owning the channels. Faculative.")
    connectgroup.add_option("-P", "--password", dest="satpwd",default=None, help="password of the user. Will be asked if not given and not in the configuration file.")
    connectgroup.add_option("-O", "--org", dest="satorg", default="baseorg", help="name of the organization to use - design the section of the config file to use. Facultative, defaults to %default")
    parser.add_option_group(connectgroup)
    #debug options
    debuggroup = optparse.OptionGroup(parser, "Debugging Option", "these options can be used to collect debugging information")
    debuggroup.add_option("-v", "--verbose", dest="verbose", default=False,action="store_true", help="activate verbose output")
    parser.add_option_group(debuggroup)
    #parse everything
    (options, args) = parser.parse_args()
    #set verbosity globally
    verbose = options.verbose
    #session init
    conn = RHNSConnection(options.satuser, options.satpwd, options.saturl, options.satorg)
    data = process_all_systems(conn)
    conn.close()
    if options.output == None:
        print_data(data)
    else:
        if verbose:
            print_data(data)
        csv_create(options.output, data)

if __name__ == "__main__":
    main(__version__)

