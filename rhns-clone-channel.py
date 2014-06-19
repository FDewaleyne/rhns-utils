#!/usr/bin/python

#quick script to demonstrate the main logic before the final script

### warning experimental script ###

##### EDIT THOSE VALUES FOLLOWING YOUR NEEDS #####
SATELLITE="rhns56-6.gsslab.fab.redhat.com"
USER="satadmin"
PWD="redhat"
#channel to copy from, label only
SOURCE="epel-ws-6"
#details of the channel to create that aren't read from the parent, do not change the name of the variables.
#all variables need to be set except parentLabel that should be set to "" for channels that don't have a parent
DESTINATION={ name:"magic epel 5", label:"magic-epel-6", parentLabel:"magic-6U4-64b", summary:"Clone of EPEL for RHEL6.4 64bits" }
import datetime
#dates to and from, using datetime.date(YYYY,MM,DD)
FROM_DATE=datetime.date(2001,01,01) # first january 2001
TO_DATE=datetime.date(2013,02,21) #release of rhel 6.4
##### DO NOT EDIT PAST THIS ######

#auth part
url = "https://%s/rpc/api" % (SATELLITE)
import xmlrpclib
client = xmlrpclib.Server(url)
key = client.auth.login(USER,PWD)
del PWD # we don't need that anyore

#read details
existingchannels = dict()
orig_details = client.channel.software.getDetails(key,SOURCE)

#create the destination if required
for channel in client.channel.listSoftwareChannels(key)):
    existingchannels[channel['label']]=channel
#minimal version of this test
if orig_details['arch_name'] == 'x86_64':
    DESTINATION['archLabel'] = 'channel-x86_64'
elif orig_details['arch_name'] == 'IA-32':
    DESTINATION['archLabel'] = 'channel-ia32'
elif orig_details['arch_name'] == 'IA-64':
    DESTINATION['archLabel'] = 'channel-ia64'
else
    print "unknown arch %s" % (orig_details['arch_name'])
DESTINATION['checksumType'] == origin_details['checksum_label']
if not DESTINATION['label'] in existingchannels.keys():
    client.channel.software.create(key,DESTINATION['label'],DESTINATION['NAME'],DESTINATION['summary'], DESTINATION['parentLabel'],DESTINATION['checksumType'])

#build the lists of content to push
#may fail on excevely large channels. avoid using on RHEL5 base channel.
package_list = client.channel.software.listAllPackages(key,SOURCE, FROM_DATE, TO_DATE)
errata_list = client.channel.software.listErrata(key,SOURCE,FROM_DATE, TO_DATE)

if len(errata_list) > 0 :
    print "%d erratas selected" % (len(errata_list))
    passes = errata_list : 50
    last_pass = False
    if errata_list % 50 > 0 :
        passes = passes + 1
        last_pass = True
    erratas_to_push = list()
    count = 0
    erratas_parsed = 0
    erratas_pushed = 0
    current_pass = 0
    for errata in list_errata:
        erratas_to_push.append(errata['advisory_name'])
        count = count +1
        erratas_parsed = erratas_parsed + 1
        if count == 49:
            result = client.channel.software.mergeErrata(key,SOURCE,DESTINATION['label'],erratas_to_push)
            erratas_pushed = erratas_pushed + len(result)
            current_pass = current_pass + 1
            print "%d erratas pushed out of %d (pass %d of %d)" % (erratas_pushed,len(errata_list),current_pass,passes)
            errata_to_push = list()
            count = 0
    if last_pass == True:
        result = client.channel.software.mergeErrata(key,SOURCE,DESTINATION['label'],erratas_to_push)
        erratas_pushed = erratas_pushed + len(result)
        current_pass = current_pass + 1
        print "%d erratas pushed out of %d (pass %d of %d)" % (erratas_pushed,len(errata_list),current_pass,passes)
else:
    print "no errata selected"

#copy packages & erratas per group of 100

client.auth.logout(key)
