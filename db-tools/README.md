db-tools
===

Database related scripts

---

_All of these scripts are meant to be used with advise and while understanding their impact on the satellite - backup the db before using any._

---
**package-consistency-checker.py**
This script adds to a channel packages based on criteria - it is meant to help remove packages that should not have been synced. It is meant to be used along with `spacewalk-remove-channel --force -c CHANELLABEL` ; to keep the packages on your `/var/satellite` add `--justdb`. [More information are available through the wiki page for that script](https://github.com/FDewaleyne/rhns-utils/wiki/package-consistency-checker)
