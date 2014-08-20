#!/usr/bin/python

#NOTE: this requires pythoon 2.3 minumum

###
# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.
###


__author__ = "Felix Dewaleyne"
__credits__ = ["Felix Dewaleyne"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Felix Dewaleyne"
__email__ = "fdewaley@redhat.com"
__status__ = "beta"


import xmlrpclib, sys, getpass
#prompt part
sys.stderr.write("please enter the hostname or ip adress of the satellite: ")
sathost = raw_input().strip()


#connection part
client = xmlrpclib.Server("https://%s/rpc/api" % sathost)
sys.stderr.write("enter your login: ")
login = raw_input().strip()
password = getpass.getpass(prompt="enter your Password: ")
sys.stderr.write("\n")
key = client.auth.login(login,password)
#remove the password from memory
del password

#fetch the data
print "Processing the list of flex systems"
rhns_allflex = []
for system in client.system.listFlexGuests(key):
    rhns_allflex.append(int(system['id']))
rhns_eligibleflex = []
for system in client.system.listEligibleFlexGuests(key):
    rhns_eligibleflex.append(int(system['id']))
print "Identifying relevant channels"
matching_channels = []
for channel in client.channel.listRedHatChannels(key):
    if "rhev-mgmt-agent" in channel['label']:
        matching_channels.append(channel['label'])
print "Fetching the list of systems attached to a rhev-mgmt-agent and their details. This may take some time"
rhns_data={}
for channel in matching_channels:
    for system in client.channel.software.listSubscribedSystems(key,channel):
        #gather the details for each system
        rhns_data[system['id']] = {'id': system['id'], 'profile_name': system['name']}
        #add all the data from getDetails to this dictionary
        rhns_data[system['id']].update(client.system.getDetails(key,system['id']))
        #read the dmi info to see if this is a flex system or not
        DMI_info = client.system.getDmi(key,system['id'])
        DMI_info['bios_infos'] = DMI_info.get('bios_vendor',"NA")+"("+DMI_info.get('bios_version',"NA")+"-"+DMI_info.get('bios_release',"NA")+")"
        rhns_data[system['id']].update(DMI_info)
        #add all the network details as well (ip adress and hostname)
        rhns_data[system['id']].update(client.system.getNetwork(key,system['id']))
        #flex test
        if int(system['id']) in rhns_allflex:
            rhns_data[system['id']].update({'flex': "virtual"})
        elif int(system['id']) in rhns_eligibleflex:
            rhns_data[system['id']].update({'flex': "elligible"})
        else:
            rhns_data[system['id']].update({'flex': "physical"})
        #channels info
        thechannels = []
        mainchannel = client.system.getSubscribedBaseChannel(key,system['id'])
        thechannels.append(mainchannel['label'])
        for channel in client.system.listSubscribedChildChannels(key,system['id']):
            thechannels.append(channel['label'])
        rhns_data[system['id']].update({'channels': ' '.join(thechannels)})

client.auth.logout(key)
#now write the csv file
print "Writing data to the csv file"
headers=['id' , 'profile_name','flex', 'hostname', 'ip', 'osa_status', 'last_boot', 'base_entitlement', 'channels', 'description', 'vendor', 'system', 'product', 'bios_infos' ]
import csv
csvfile = open('systems_'+login+'.csv', 'wb' )
csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
csv_writer.writerow(headers)
for system in rhns_data.itervalues():
    line = []
    for value in headers:
        line.append(system.get(value))
    csv_writer.writerow(line)
    del line
del rhns_data
