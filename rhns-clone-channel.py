#!/usr/bin/python

#quick script to demonstrate the main logic before the final script

### warning experimental script ###

##### EDIT THOSE VALUES FOLLOWING YOUR NEEDS #####
SATELLITE="rhns56-6.gsslab.fab.redhat.com"
USER="satadmin"
PWD="redhat"
#channel to copy from, label only
SOURCE="epel-6-64-ws"
#details of the channel to create that aren't read from the parent, do not change the name of the variables.
#all variables need to be set except parentLabel that should be set to "" for channels that don't have a parent
DESTINATION={ 'name' : "magix epel 6 ws", 'label' : "magic-epel-ws", 'parentLabel' : "magix-6-ws", 'summary' : "Clone of EPEL for RHEL6.4 64bits WS" }
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
for channel in client.channel.listSoftwareChannels(key):
    existingchannels[channel['label']]=channel
#minimal version of this test
if orig_details['arch_name'] == 'x86_64':
    DESTINATION['archLabel'] = 'channel-x86_64'
elif orig_details['arch_name'] == 'IA-32':
    DESTINATION['archLabel'] = 'channel-ia32'
elif orig_details['arch_name'] == 'IA-64':
    DESTINATION['archLabel'] = 'channel-ia64'
else:
    print "unknown arch %s" % (orig_details['arch_name'])
DESTINATION['checksumType'] = orig_details['checksum_label']
if not DESTINATION['label'] in existingchannels.keys():
    new_channel = True
    client.channel.software.create(key,DESTINATION['label'],DESTINATION['name'],DESTINATION['summary'],DESTINATION['archLabel'], DESTINATION['parentLabel'],DESTINATION['checksumType'])
else:
    new_channel = False

#build the lists of content to push
#may fail on excevely large channels. avoid using on RHEL5 base channel.
package_list = list()
for package in client.channel.software.listAllPackages(key,SOURCE, FROM_DATE.isoformat(), TO_DATE.isoformat()) :
    package_list.append(package['id'])
errata_list = client.channel.software.listErrata(key,SOURCE,FROM_DATE.isoformat(), TO_DATE.isoformat())

if len(errata_list) > 0 :
    print "%d erratas selected" % (len(errata_list))
    passes = len(errata_list) / 50
    last_pass = False
    if len(errata_list) % 50 > 0 :
        passes = passes + 1
        last_pass = True
    erratas_to_push = list()
    count = 0
    erratas_pushed = 0
    current_pass = 0
    for errata in errata_list:
        erratas_to_push.append(errata['advisory_name'])
        count = count +1
        if count == 49:
            result = client.channel.software.mergeErrata(key,SOURCE,DESTINATION['label'],erratas_to_push)
            erratas_pushed = erratas_pushed + len(result)
            current_pass = current_pass + 1
            print '\r'+"%d erratas pushed out of %d (pass %d of %d)" % (erratas_pushed,len(errata_list),current_pass,passes),
            errata_to_push = list()
            count = 0
    if last_pass == True:
        result = client.channel.software.mergeErrata(key,SOURCE,DESTINATION['label'],erratas_to_push)
        erratas_pushed = erratas_pushed + len(result)
        current_pass = current_pass + 1
        print '\r'+"%d erratas pushed out of %d (pass %d of %d)" % (erratas_pushed,len(errata_list),current_pass,passes),
    print "" #avoid writing next line to the same line
else:
    print "no errata selected"

#copy packages & erratas per group of 100
if not new_channel or len(errata_list) > 0:
    #compare content to revise the list of packages to upload, especially if this is not a new channel or erratas were merged.
    packages_in_destination = list()
    for package in client.channel.software.listAllPackages(key,DESTINATION['label'], FROM_DATE.isoformat(), TO_DATE.isoformat()) :
        packages_in_destination.append(package['id'])
    import itertools 
    final_package_list = list(itertools.filterfalse(lambda x: x in packages_in_destination, package_list)) + list(itertools.filterfalse(lambda x: x in package_list, packages_in_destination))
else:
    final_package_list = package_list
#avoid sync issues, remove any duplicated ids
final_package_list = list(set(final_package_list))
if len(final_package_list) > 0 :
    print "%d unique packages selected" % (len(final_package_list))
    passes = len(final_package_list) / 100
    last_pass = False
    if len(errata_list) % 100 > 0 :
        passes = passes + 1
        last_pass = True
    packages_to_push = list()
    count = 0
    packages_pushed = 0
    current_pass = 0
    for package in final_package_list:
        packages_to_push.append(package)
        count = count +1
        if count == 49:
            result = client.channel.software.addPackages(key,DESTINATION['label'],packages_to_push)
            packages_pushed = packages_pushed + len(result)
            current_pass = current_pass + 1
            print '\r'+"%d packages pushed out of %d (pass %d of %d)" % (packages_pushed,len(packages_list),current_pass,passes),
            packages_to_push = list()
            count = 0
    if last_pass == True:
        result = client.channel.software.mergeErrata(key,SOURCE,DESTINATION['label'],erratas_to_push)
        erratas_pushed = erratas_pushed + len(result)
        current_pass = current_pass + 1
        print '\r'+"%d erratas pushed out of %d (pass %d of %d)" % (erratas_pushed,len(errata_list),current_pass,passes),
    print "" #avoid writing next line to the same line
else:
    print "no package selected"

#plan the regeneration of the repodata
client.channel.software.regenerateYumCache(key,DESTINATION['label'])
print "regeneration of repodata requested for %s" % (DESTINATION['label'])

print "script finished"
client.auth.logout(key)
