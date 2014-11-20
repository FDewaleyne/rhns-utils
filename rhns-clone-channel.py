#!/usr/bin/python

#quick script to demonstrate the main logic before the final script

### warning experimental script ###

##### EDIT THOSE VALUES FOLLOWING YOUR NEEDS #####
SATELLITE="rhns56-6.gsslab.fab.redhat.com"
USER="satadmin"
PWD="redhat"
#for each entry in action we will do one run of the cloning
#channel to copy from, label only
actions = list()
actions.append({'SOURCE' : None,'DESTINATION' : None})
actions[0]['SOURCE']="epel-6-64-main"
#details of the channel to create that aren't read from the parent, do not change the name of the variables.
#all variables thatneed to be set
actions[0]['DESTINATION']={ 'name' : "magix epel 6 ws", 'label' : "magix-epel-ws", 'summary' : "Clone of EPEL for RHEL6.4 64bits WS" }
#if there is no parent_label set this to None or ""
actions[0]['DESTINATION']['parent_label'] = "magix-6-ws"
#optional value
#actions[0]['DESTINATION']['description'] = "the description of the channel"

#repeat and add to actions as many entries are required

import datetime #DO NOT REMOVE THIS
#dates to and from, using datetime.date(YYYY,MM,DD)
FROM_DATE=datetime.date(1971,01,01) # avoid replacing this unless you accept that erratas / packages may be missing
TO_DATE=datetime.date(2013,02,21) #release of rhel 6.4
DEBUG=2
##### DO NOT EDIT PAST THIS ######


#auth part
url = "https://%s/rpc/api" % (SATELLITE)
import xmlrpclib
client = xmlrpclib.Server(url)
key = client.auth.login(USER,PWD)
del PWD # we don't need that anyore

def clone_channel(SOURCE,DESTINATION):
    """clones a channel from dateX to dateY from SOURCE to DESTINATION, using the creation date of a package & errata date as a reference (not last modified)"""
    
    #globals so that this function continues to work with minor edits
    global FROM_DATE
    global TO_DATE
    global DEBUG

    #read details
    existingchannels = dict()
    orig_details = client.channel.software.getDetails(key,SOURCE)

    #create the destination if required
    for channel in client.channel.listSoftwareChannels(key):
        existingchannels[channel['label']]=channel
    if not DESTINATION['label'] in existingchannels.keys():
        new_channel = True
        print "Cloning %s to %s" % (SOURCE, DESTINATION['label']),
        #client.channel.software.create(key,DESTINATION['label'],DESTINATION['name'],DESTINATION['summary'],DESTINATION['archLabel'], DESTINATION['parentLabel'],DESTINATION['checksumType'])
        if DESTINATION['parent_label'] == None or DESTINATION['parent_label'] == "":
            #parent_label should be removed if not required (None or "")
            del DESTINATION['parent_label']
            print ""
        else:
            print "; %s will be a child of %s" % (DESTINATION['label'], DESTINATION['parent_label'])
        client.channel.software.clone(key,SOURCE,DESTINATION,True)
    else:
        print "Reusing existing channel %s" % (DESTINATION['label'])
        new_channel = False

    #build the lists of content to push
    #may fail on excevely large channels. avoid using on RHEL5 base channel.
    package_list = list()
    #for package in client.channel.software.listAllPackages(key,SOURCE, FROM_DATE.isoformat(), TO_DATE.isoformat()) :
    print "Parsing package information"
    counter = 1
    import dateutil.parser
    source_packages = client.channel.software.listAllPackages(key,SOURCE)
    nb_packages = len(source_packages)
    for package in  source_packages:
        details = client.packages.getDetails(key,package['id'])
        print '\r'+"%d / %d" % (counter, nb_packages),
        #convert the date to do the comparison 
        build_date = dateutil.parser.parse(details['build_date'])
        if build_date > datetime.datetime.combine(FROM_DATE,datetime.time()) and build_date < datetime.datetime.combine(TO_DATE,datetime.time()):
            package_list.append(package['id'])
        counter = counter + 1
    print '\r'+"Done, fetching errata list                    "
    errata_list = client.channel.software.listErrata(key,SOURCE,FROM_DATE.isoformat(), TO_DATE.isoformat())
    print "Result: %d erratas selected, %d packages selected" % (len(errata_list), len(package_list))

    print "Pushing erratas"
    if len(errata_list) > 0 :
        passes = len(errata_list) / 50
        last_pass = False
        if len(errata_list) % 50 > 0 :
            passes = passes + 1
            last_pass = True
        erratas_to_push = list()
        erratas_pushed = 0
        current_pass = 1
        for errata in errata_list:
            erratas_to_push.append(errata['advisory_name'])
            if len(erratas_to_push) == 50:
                if DEBUG >= 3:
                    print "" # new line not to overwrite the previous one
                    print "%d erratas to push in pass %d" % (len(erratas_to_push),current_pass)
                    if DEBUG >=6:
                        for errata in erratas_to_push:
                            print " - %s" % (errata)
                #result = client.channel.software.mergeErrata(key,SOURCE,DESTINATION['label'],erratas_to_push)
                result = client.errata.cloneAsOriginal(key,DESTINATION['label'],erratas_to_push)
                erratas_pushed = erratas_pushed + len(result)
                print '\r'+"%d erratas pushed out of %d (pass %d of %d)" % (erratas_pushed,len(errata_list),current_pass,passes),
                if DEBUG >= 6:
                    print "" # new line not to overwrite the previous one
                    for errata in result:
                        print " - %s, %s" % (errata['advisory_name'], errata['date'])
                current_pass = current_pass + 1
                erratas_to_push = list()
        if last_pass:
            if DEBUG >= 3:
                print "" # new line not to overwrite the previous one
                print "%d erratas to push in pass %d:" % (len(erratas_to_push),current_pass)
                if DEBUG >= 6:
                    for errata in erratas_to_push:
                        print " - %s" % (errata)
            result = client.errata.cloneAsOriginal(key,DESTINATION['label'],erratas_to_push)
            erratas_pushed = erratas_pushed + len(result)
            print '\r'+"%d erratas pushed out of %d (pass %d of %d)" % (erratas_pushed,len(errata_list),current_pass,passes),
            if DEBUG >= 6:
                print "" # new line not to overwrite the previous one
                for errata in result:
                    print " - %s, %s" % (errata['advisory_name'], errata['date'])
        print "" #avoid writing next line to the same line
    else:
        print "no errata selected"

    print "Pushing packages"
    #copy packages & erratas per group of 100
    if not new_channel or len(errata_list) > 0:
        #compare content to revise the list of packages to upload, especially if this is not a new channel or erratas were merged.
        packages_in_destination = list()
        for package in client.channel.software.listAllPackages(key,DESTINATION['label']) :
            packages_in_destination.append(package['id'])
        final_package_list = list(set(package_list) - set(packages_in_destination))
        #remove packages provided by errata that aren't part of the selection
        for package_id in package_list:
            for errata in client.packages.listProvidingErrata(key,package_id):
                if datetime.datetime.strptime(errata['issue_date'], '%Y-%m-%d %H:%M:%S') < datetime.datetime.combine(FROM_DATE,datetime.time()) or datetime.datetime.strptime(errata['issue_date'], '%Y-%m-%d %H:%M:%S') > datetime.datetime.combine(TO_DATE,datetime.time()):
                    final_package_list.remove(package_id)
        print "%d packages in source and %d packages in destination, %d to push" % (len(package_list),len(packages_in_destination),len(final_package_list))
    else:
        final_package_list = package_list
    #avoid sync issues, remove any duplicated ids
    if DEBUG>=5:
        print "Packages to push: "+", ".join(str(pkgid) for pkgid in final_package_list)
        for package_id in final_package_list:
            details = client.packages.getDetails(key,package_id)
            if details['epoch'] == '':
                epoch = '0'
            else:
                epoch = details['epoch']
            channels = ', '.join(details['providing_channels'])
            print "- %s:%s-%s-%s.%s built on the %s and present in channels %s" % (epoch,details['name'],details['version'],details['release'],details['arch_label'],details['build_date'], channels),
            #add to that info of the providing erratas
            providing_erratas = client.packages.listProvidingErrata(key,package_id)
            print "provided by %d erratas" % (len(providing_erratas)),
            if len(providing_erratas) >0:
                for errata in providing_erratas:
                    print "%s (%s) " % (errata['advisory'],errata['issue_date']),
            print ""
    if len(final_package_list) > 0 :
        passes = len(final_package_list) / 100
        last_pass = False
        if len(errata_list) % 100 > 0 :
            passes = passes + 1
            last_pass = True
        packages_to_push = list()
        packages_pushed = 0
        current_pass = 1
        for package in final_package_list:
            packages_to_push.append(package)
            if len(packages_to_push) == 100:
                if DEBUG >= 3:
                    print "" # new line not to overwrite the previous one
                    print "%d packages to push in pass %d" % (len(packages_to_push),current_pass)
                    if DEBUG >= 6:
                        for package in packages_to_push:
                            print " - ID %d" % (package)
                result = client.channel.software.addPackages(key,DESTINATION['label'],packages_to_push)
                # addpackages returns 1 if the operation was a success, otherwise throws an error
                if result == 1:
                    packages_pushed = packages_pushed + len(packages_to_push)
                print '\r'+"%d packages pushed out of %d (pass %d of %d)" % (packages_pushed,len(final_package_list),current_pass,passes),
                current_pass = current_pass + 1
                packages_to_push = list()
        if last_pass == True:
            result = client.channel.software.addPackages(key,DESTINATION['label'],packages_to_push)
            if result == 1:
                packages_pushed = packages_pushed + len(packages_to_push)
                print '\r'+"%d packages pushed out of %d (pass %d of %d)" % (packages_pushed,len(final_package_list),current_pass,passes),
        print "" #avoid writing next line to the same line
    else:
        if len(package_list) == 0:
            print "No packages to push"
        else:
            print "No packages  required to be added to the destination"

    #plan the regeneration of the repodata
    client.channel.software.regenerateYumCache(key,DESTINATION['label'])
    import time
    print "Regeneration of repodata requested for %s at %s" % (DESTINATION['label'],time.strftime("%Y-%m-%d %H:%M"))
    pass

counter = 0
for action in actions:
    counter += 1
    print "run %d / %d " % (counter, len(actions))
    clone_channel(action['SOURCE'],action['DESTINATION'])

print "Script finished"
client.auth.logout(key)
