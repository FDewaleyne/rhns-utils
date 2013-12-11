#!/usr/bin/python

# To the extent possible under law, Red Hat, Inc. has dedicated all copyright to this software to the public domain worldwide, pursuant to the CC0 Public Domain Dedication. 
# This software is distributed without any warranty.  See <http://creativecommons.org/publicdomain/zero/1.0/>.

# this script is intended to remove packages from /var/satellite when their intended md5sum (which can be found in the path) does not match the actual md5sum of the file. it will only work on Red Hat packages as of this version.

# 2012-08-90 : version 1.0 - versioning started - Felix Dewaleyne
# 2012-02-29 stephan.duehr@dass-it.de
# the original version of this script comes from the Red Hat Knowledgebase Article
# https://access.redhat.com/knowledge/solutions/41427 (Attachment clean_varsat.py.zip)
# 
# Enhancements:
# - first only verify the checksums, displaying counters of ok and bad files found
# - after all files are checked, display the list only of files with incorrect checksum
# - let the user confirm the deletion of the listed files
# - catch file deletion errors
#
# 2012-11-24 : version 2.0 - now able to scans the packages provided for organizations
# 2012-11-25 : version 2.1 - debugged 2.0
# 2012-11-25 : version 2.2 - added a force option


#path to the Red Hat data. edit this if you want to treat other packages
VARSAT="/var/satellite/redhat" #/NULL and /\d should be the ones taken into account.
#note : the full file path is VARSAT/XYZ/packagename/version/arch/md5sum/rpmfile.rpm
#note : don't put a / at the end of the VARSAT value

import os, hashlib, re, sys

def sumfile(fobj):
    m = hashlib.md5()
    while True:
        d = fobj.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()

def sum2file(fobj):
    m = hashlib.sha256()
    while True:
        d = fobj.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()

def yesno(prompt):
    valid = {'y': True, 'n': False}
    answer = raw_input(prompt)
    while answer not in valid.keys():
        print "please answer with 'y' or 'n'"
        answer = raw_input(prompt)
    return valid[answer]

import optparse
parser = optparse.OptionParser("usage : %prog [-f]\n checks if the rpms stored on the satellite match their checksums")
parser.add_option("-f", "--force", dest="force", action="store_true", default=False, help="does not ask for confirmation before removing bad files")
(options, args) = parser.parse_args()

print "script started, exploring the folders. this may take some time as each time a md5sum of the rpm files will be made."
ok_count = 0
bad_count = 0
bad_files = []
#this level is /NULL for Red Hat packages, /1 or any number for an org
for entry_layer0 in os.listdir(VARSAT):
    if re.match("NULL|\d+",entry_layer0) == None:
        continue; # this is not a folder we should scan.
    else:
        currentpath_l0=VARSAT+"/"+entry_layer0
        print ""
        print "checking "+currentpath_l0
        print "    ok count    bad count"
        if os.path.isdir(currentpath_l0) == True:
            #layer 1 : the XYZ list
            for entry_layer1 in os.listdir(currentpath_l0):
                currentpath_l1=currentpath_l0+"/"+entry_layer1
                if os.path.isdir(currentpath_l1) == False:
                    print "error on "+currentpath_l1
                else:
                    #layer 2 : the packagename list 
                    for entry_layer2 in os.listdir(currentpath_l1):
                        currentpath_l2=currentpath_l1+"/"+entry_layer2
                        if os.path.isdir(currentpath_l2) == True:
                            #layer 3: list of versions
                            for entry_layer3 in os.listdir(currentpath_l2):
                                currentpath_l3=currentpath_l2+"/"+entry_layer3
                                if os.path.isdir(currentpath_l3) == True:
                                    #layer 4: list of archs
                                    for entry_layer4 in os.listdir(currentpath_l3):
                                        currentpath_l4=currentpath_l3+"/"+entry_layer4
                                        if os.path.isdir(currentpath_l4) == True:
                                            #layer 5: the md5sums
                                            for entry_layer5 in os.listdir(currentpath_l4):
                                                currentpath_l5=currentpath_l4+"/"+entry_layer5
                                                if os.path.isdir(currentpath_l5) == True:
                                                    #layer 6 : the rpm files
                                                    for entry_layer6 in os.listdir(currentpath_l5):
                                                        currentpath_l6=currentpath_l5+"/"+entry_layer6
                                                        f = open(currentpath_l6,'rb')
                                                        if (len(entry_layer5) == 32  and sumfile(f) != entry_layer5):
                                                            bad_files.append(currentpath_l6)
                                                            bad_count += 1
                                                        elif(len(entry_layer5) > 32 and sum2file(f) != entry_layer5):
                                                            bad_files.append(currentpath_l6)
                                                            bad_count += 1
                                                        else:
                                                            ok_count += 1
                                                    sys.stdout.write("%12d %12d\r" % (ok_count, bad_count))
                                                    sys.stdout.flush()
                         

if bad_files:
    print "\n\nFound %d files with bad checksum:" % bad_count
    print "\n".join(bad_files)
    sys.stdout.flush()
    if not options.force:
        really_delete = yesno("\nReally delete all the files listed above (y/n)?")
        if not really_delete:
            print "ok, exiting"
            sys.exit(0)
    for f in bad_files:
        print "deleting: " + f
        try:
            os.remove(f)
        except OSError, e: 
            print "Error: %d (%s)" % (e.errno, e.strerror)
            proceed = yesno("Continue (y/n)?")
            if not proceed:
                print "ok, exiting"
                break

    print "finished. Please run satellite-sync now if files were deleted."

else:
    print ""
    print "all files ok"
