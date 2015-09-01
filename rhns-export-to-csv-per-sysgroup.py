#!/usr/bin/python

#NOTE: this requires pythoon 2.3 minumum

###
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
###


__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "0.4"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "prod"


import xmlrpclib, sys, getpass
#connection part
client = xmlrpclib.Server("https://xmlrpc.rhn.redhat.com/rpc/api")
sys.stderr.write("enter your RHN login: ")
login = raw_input().strip()
password = getpass.getpass(prompt="enter your RHN Password: ")
sys.stderr.write("\n")
key = client.auth.login(login,password)
#remove the password from memory
del password

#fetch the data
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
