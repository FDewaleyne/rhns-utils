#!/usr/bin/python

# quick script used to clean a pickle from rhns-remove*.py from the content that is provided by no channels.


IN="backup_content"
OUT=IN+".new"

import pickle
bkpfile = open(IN, 'r')
newbkpfile = open(OUT, 'w+')

packages = pickle.load(bkpfile)
remove = []

for package in packages:
    if len(packages[package]['channels']) > 0 and packages[package]['channels'][0] is None:
        remove.append(package)

for package in remove:
    del packages[package]

pickle.dump(packages, newbkpfile)

bkpfile.close()
newbkpfile.close()

print "done. the data was written to %s" % (OUT)
