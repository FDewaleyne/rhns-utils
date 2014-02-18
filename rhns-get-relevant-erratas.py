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

#end of the class#fetch the data
print "Fetching the list of systems and the details for each of your system. This may take some time"
rhn_data={}
for system in client.system.listUserSystems(key):
    #gather the details for each system
    rhn_data[system['id']] = {'id': system['id'], 'last_checkin': system['last_checkin']}
    #add all the data from getDetails to this dictionary
    rhn_data[system['id']].update(client.system.getDetails(key,int(system['id'])))
    #add all the network details as well
    rhn_data[system['id']].update(client.system.getNetwork(key,int(system['id'])))

client.auth.logout(key)
#now write the csv file
print "Writing data to the csv file"
headers=['id' , 'profile_name', 'hostname', 'ip', 'last_checkin', 'base_entitlement', 'description', 'adress1','adress2', 'city', 'state', 'country', 'building', 'room', 'rack']
import csv
csvfile = open('systems_'+login+'.csv', 'wb' )
csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
csv_writer.writerow(headers)
for system in rhn_data.itervalues():
    line = []
    for value in headers:
        line.append(system.get(value))
    csv_writer.writerow(line)
    del line
del rhn_data
# start main function
def main(version):
    """main function - takes in the options and selects the behaviour"""
    global verbose;
    import optparse
    parser = optparse.OptionParser("%prog [-s systemid] [-e erratatype] [-o file.csv]\n Outputs the list of erratas available for a machine depending on the options selected", version=version)
    parser.add_option("-s", "--systmid", dest="systemid", type="int", default=None, help="Uses that systemid instead of the value extracted from the system's systemid file")
    parser.add_option("-e", "--erratatype", dest="erratatype", default=":", help="Type of Errata to use. Default to all, can be limited to 'Security Advisory', 'Product Enhancement Advisory' or 'Bug Fix Advisory' ; also accepted the shortenned versions 'security', 'enhangement' and 'bugfix'")
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
    #TODO rewrite logic here
    if options.entlist:
        key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        list_entitlements(key)
        client.auth.logout(key)
    elif options.entitlement and not options.syslist:
        key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        get_entitlement(key,options.entitlement)
        client.auth.logout(key)
    elif options.orgid != None:
        if options.syslist:
            parser.error("not implemented yet")
        else:
            key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
            org_consumtion(key,options.orgid) 
            client.auth.logout(key)
    elif options.syslist:
        if options.entitlement == None:
            parser.error('you forgot to select an entitlement')
            parser.print_help()
        else:
            parser.error('not implemented yet')
            #key = session_init()
            #client.auth.logout(key)
    else:
        key = session_init(options.satorg , {"url" : options.saturl, "login" : options.satuser, "password" : options.satpwd})
        general_consumption(key)
        client.auth.logout(key)

if __name__ == "__main__":
    main(__version__)

