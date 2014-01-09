db-tools
===

Database related scripts

---

_All of these scripts are meant to be used with advise and while understanding their impact on the satellite - backup the db before using any._

---
**package-consistency-checker.py**
This script adds to a channel packages based on criteria - it is meant to help remove packages that should not have been synced. It is meant to be used along with `spacewalk-remove-channel --force -c CHANELLABEL` ; to keep the packages on your `/var/satellite` add `--justdb`

Usage info :
~~~
Usage: package-consistency-checker.py [options]

Usage: package-consistency-checker.py [options] This program will clone all
erratas and packages from the source to the destination as long as they are
not already present in the destiation, depending on which settings are used
REMEMBER TO BACKUP YOUR DATABASE

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -H SATHOST, --host=SATHOST
                        hostname of the satellite to use, preferably a fqdn
                        e.g. satellite.example.com
  -l SATUSER, --login=SATUSER
                        User to connect to satellite
  -p SATPWD, --password=SATPWD
                        Password to connect to satellite
  -c DESTCHANNEL, --destChannel=DESTCHANNEL
                        Channel to populate with the packages that don't have
                        a path
  -A ARCH, --arch=ARCH  Architecture to use when creating the channel and
                        filtering packages. Defaults to x86_64 which accepts
                        64 and 32 bits packages
  -v, --verbose         Enables debug output
  --keyid=KEYID         Focuses on all the packages signed by the keyid
                        provided. Only use if you know already what keyid to
                        remove - value to use changes from database to
                        database.
  --nullkeyid           Focuses on all packages with no key id
  --packageid=PACKAGEID
                        Focuses on the packages with the same signature as
                        this package
  --packagefile=PACKAGEFILE
                        Focuses on the packages with a path identical to the
                        entries in a file
~~~
