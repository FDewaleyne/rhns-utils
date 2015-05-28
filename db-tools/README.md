db-tools
===

Database related scripts

---

_All of these scripts are meant to be used with advise and while understanding their impact on the satellite - backup the db before using any._

---
**package-consistency-checker.py**
This script adds to a channel packages based on criteria - it is meant to help remove packages that should not have been synced. It is meant to be used along with `spacewalk-remove-channel --force -c CHANELLABEL` ; to keep the packages on your `/var/satellite` add `--justdb`. [More information are available through the wiki page for that script](https://github.com/FDewaleyne/rhns-utils/wiki/package-consistency-checker)

---
**rhns-remove-unknown-provider.py**
This script is dangerous - it exports the channel relations of a set of packages that have no signature and are in red hat channels (and other channels) then can be ran to remove the content. This should replace the `package-consistancy-checker.py` in this aspect only. Part of its queries may make their way to `spacewalk-fsck` but I am not so sure it would be such a good idea (it would burn beta channels!). [More information on this script is available on the wiki](https://github.com/FDewaleyne/rhns-utils/wiki/rhns-remove-unknown-provider)

---
**rhns-remove-package.py**
This script is dangerous - it exports the channel relations of a package then can remove the content requested. This should replace the `package-consistancy-checker.py` in this aspect only. [More information on this script is available on the wiki](https://github.com/FDewaleyne/rhns-utils/wiki/rhns-remove-package) - for usage on one single package.

---
**rhns-package-infos.py**
This script outputs information related to a package given in argument through `--packageid`.
