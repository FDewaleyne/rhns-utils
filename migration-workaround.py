#!/usr/bin/python
#
#lists systems, builds up a list in a system group, then makes the action on every single of them. or alters just one system.
#

# author : Felix Dewaleyne
# verion 1.5

import xmlrpclib, sys, os, ConfigParser,getpass

###
#parsing config file or creating an empty one ; we will parse the config file for each org name if needed, if it exists the password won't be asked.
# the config file can be in ~/.satellite of the user or in the folder of the script or in /etc/sysconfig/rhn/satellite ; all files are read one after the other.
# sample config :
# [base]
# username=value
# password=value
# url=https://satellite.example.com/rpc/api
# [suborgname]
# username=value
# password=value
###

#global variables
client=None;
SATELLITE_LOGIN=None;
config = ConfigParser.ConfigParser()
config.read(['.satellite', os.path.expanduser('~/.satellite'), '/etc/sysconfig/rhn/satellite'])

# this will initialize a session and return its key.
# for security reason the password is removed from memory before exit, but we want to keep the current username.
def session_init(orgname='baseorg'):
    global client;
    global config;
    global SATELLITE_LOGIN;
    if config.has_section(orgname) and config.has_option(orgname,'username') and config.has_option(orgname,'password') and config.has_option('baseorg','url'):
        SATELLITE_LOGIN = config.get(orgname,'username')
        SATELLITE_PASSWORD = config.get(orgname,'password')
        SATELLITE_URL = config.get('baseorg','url')
    else:
        if not config.has_option('baseorg','url'):
            sys.stderr.write("enter the satellite url, such as https://satellite.example.com/rpc/api")
            sys.stderr.write("\n")
            SATELLITE_URL = raw_input().strip()
        else:
            SATELLITE_URL = config.get('baseorg','url')
        sys.stderr.write("Login details for %s\n\n" % SATELLITE_URL)
        sys.stderr.write("Login: ")
        SATELLITE_LOGIN = raw_input().strip()
        # Get password for the user
        SATELLITE_PASSWORD = getpass.getpass(prompt="Password: ")
        sys.stderr.write("\n")
    #inits the connection
    client = xmlrpclib.Server(SATELLITE_URL, verbose=0)
    key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)
    # removes the password from memory
    del SATELLITE_PASSWORD
    return key
    

#here let's define a couple functions that we are going to use later on
def org_select(key):
    global client;
    # do not call if user is not organization admin#
    # returns an ID that was selected
    print "This is a list of the organizations, enter the ID of the organization we will operate on"
    listorg = sorted(client.org.listOrgs(key))
    for org in listorg:
        print "\t- "+str(org['id'])+"\t- "+org['name']
    orgid = raw_input("Oranization ID:").strip()
    if orgid == "":
        return None
    else:
        return int(orgid)

def getattributes(key,systemid):
    global client;
    #print the attributes as a space or a letter.
    entitlements = []
    systemdetails = client.system.getDetails(key,systemid)
    entitlements.append(systemdetails['base_entitlement'])
    for entitlement in systemdetails['addon_entitlements']:
        entitlements.append(entitlement)
    value = ""
    if entitlements.count("enterprise_entitled") >= 1:
        value += "E "
    else:
        value += "  "
    if entitlements.count("monitoring_entitled") >= 1:
        value += "M "
    else:
        value += "  "
    if entitlements.count("provisioning_entitled") >= 1:
        value += "P "
    else:
        value += "  "
    if entitlements.count("virtualization_host_platform") >= 1:
        value += "VP"
    elif entitlements.count("virtualization_host") >=1:
        value += "VH"
    else:
        value += "  "
    return value

def all_systems(key,groupname=None):
    global client;
    systems = []
    if groupname == None:
        for system in client.system.listSystems(key):
            systems.append(system['id'])
    else:
        for system in client.systemgroup.listSystems(key,groupname):
            systems.append(system['id'])
    return systems


# function that lists the systems of that organization.
def list_systems(key,groupname=None):
    global client;
    if groupname == None:
        print "Here is the list of systems for the selected organization"
        for system in client.system.listSystems(key):
            print "\t - "+str(system['id'])+" - "+getattributes(key,system["id"])+" - "+system['name']
    else:
        print "List of systems for the selected group"
        for system in client.systemgroup.listSystems(key,groupname):
            print "\t - "+str(system['id'])+" - "+getattributes(key,system["id"])+" - "+system['profile_name']
    return


#selects or creates a group of a given name, making it possible to do 1 operation over a set of systems
def settle_systemgroup(key,groupname,orgid,listsysgroups=dict()):
    global client;
    if len(listsysgroups) == 0:
        for sysgroup in client.systemgroup.listAllGroups(key):
            listsysgroups[sysgroup['name']] = (sysgroup['id'],sysgroup['org_id'])
    if groupname in listsysgroups:
        if listsysgroups[groupname][1] == orgid:
            return groupname
        else:
            print "There is already a systemgroup with that name in the satellite in another organization"
            groupname = raw_input('Enter an alternative to '+groupname+' ['+groupname+'_'+str(orgid)+']:').strip()
            if groupname == "":
                groupname = groupname+'_'+str(orgid)
            return settle_systemgroup(key,groupname,orgid)
    try:
        newgroup = client.systemgroup.create(key,groupname,'a system group created for the workaround of ticket 00349403')
    except xmlrpclib.Fault:
        print "Error; unable to create a system group at all or select a group of "+groupname
        print "enter an existing groupname or nothing to exit on the error"
        groupname=raw_input("Enter the name of an existing group or nothing to exit on error:").strip()
        if  groupname == "":
            raise
        else:
            return settle_systemgroup(key,groupname,orgid)
    return newgroup['name']


#selects a group, creates it if needs be
def select_systemgroup(key,orgid):
    global client;
    print "List of groups visible and in that organization"
    listsysgroups = dict()
    for sysgroup in client.systemgroup.listAllGroups(key):
        listsysgroups[sysgroup['name']] = (sysgroup['id'],sysgroup['org_id'])
        if sysgroup['org_id'] == orgid:
            print "\t - "+sysgroup['name']+" - "+sysgroup['description']
    groupname = raw_input("enter a group name to create or use a group of that name ; enter nothing to use 'workaround': ").strip()
    if groupname == "":
        groupname = 'workaround'
    return settle_systemgroup(key,groupname,orgid,listsysgroups)


#returns a list of channels the machine is entitled to
def get_system_info(key,systemid):
    global client;
    channelinfo={'base':None,'childs':[]}
    for child in client.system.getSubscribedBaseChannel(key,systemid):
        try:
            channelinfo['base'] = child['label']
        except:
            #there is likely no base channel on that system, keeping default of None
            pass
    for child in client.system.listSubscribedChildChannels(key,systemid):
        channelinfo['childs'].append(child['label'])
    return channelinfo


def restore_channels(key,systemid,channeldata):
    global client;
    if channeldata['base'] == None:
        #that means it was not assigned to any channel to start with ; skip.
        return
    client.system.setBaseChannel(key,systemid,channeldata['base'])
    client.system.setChildChannels(key,systemid,channeldata['childs'])

def analyse_consumption(key,systemid):
    global client;
    consumption = dict()
    for vguest in client.system.listVirtualGuests(key,systemid):
        try:
            channel = client.system.getSubscribedBaseChannel(key,vguest['id'])
            childchannels = client.system.getSubscribledChildChannels(key,vguest['id'])
            addons = client.system.getEntitlements(key,vguest['id'])
            if addons == None or addons == []:
                addons = ['enterprise_entitled']
            elif addons.count('enterprise_entitled') == 0:
                addons.append('enterprise_entitled')
            if channel['label'] in consumtion:
                consumption[channel['label']] += 1
            else:
                consumption[channel['label']] = 1
            for child in childchannels:
                if child['label'] in consumption:
                    consumption[child['label']] += 1
                else:
                    consumption[child['label']] = 1
            for addon in addons:
                if addon in consumption:
                    consumption[addon] += 1
                else:
                    consumption[addon] = 1
        except:
            #pass this guest
            print "skipping guest "+vguest['name']
            continue
    return consumption

def is_virtualization_host(key,systemid):
    global client;
    for entitlement in client.system.getEntitlements(key,systemid):
        if entitlement in ['virtualization_host','virtualization_host_platform']:
            return True
    return False


def change_system(key,systemid,adds=[],rms=[]):
    global client;
    validcandidates = []
    channeldata = get_system_info(key,systemid)
    for candidate in client.channel.listRedHatChannels(key):
        validcandidates.append(candidate['id'])
    for candidate in client.system.listSubscribableBaseChannels(key,systemid):
        if validcandidates.count(candidate['id']) >= 1:
            worked = True
            if is_virtualization_host(key,systemid):
                print "Virtual Host detected, converting"
                guestBchanges = dict()
                guestCchanges = dict()
                guestcount = 0
                for guest in client.system.listVirtualGuests(key,systemid):
                    guestcount += 1
                    try:
                        guestdetails=client.system.getDetails(key,guest['id'])
                        channel = client.system.getSubscribedBaseChannel(key,guest['id'])
                        if channel['label'] in guestBchanges.keys():
                            guestBchanges[channel].append(guest['id'])
                        else:
                            guestBchanges[channel] = [guest['id']]
                        for channel in client.system.listSubscribedChildChannels(key,guest['id']):
                            if channel['label'] in guestCchanges.keys():
                                guestCchanges[channel].append(guest['id'])
                            else:
                                guestCchanges[channel] = [guest['id']]
                    except xmlrpclib.Fault:
                        print "guest "+guest['name']+" known as "+guest['guest_name']+" doesn't seem to be registered to the satellite, skipping"
                        pass
                for label in guestBchanges.keys():
                    converted = client.system.convertToFlexEntitlement(key,guestBchanges[label],label)
                    print label+": converted successfully "+str(converted)+" guest systems out of "+str(guestcount)
                for label in guestCchanges.keys():
                    converted = client.system.convertToFlexEntitlement(key,guestCchanges[label],label)
                    print label+": converted successfully "+str(converted)+" guest systems out of "+str(guestcount)
            try:
                client.system.setBaseChannel(key,systemid,candidate['label'])
                client.system.setChildChannels(key,systemid,[])
            except xmlrpclib.Fault, e:
                print "couldn't change the base channel at all for "+str(systemid)+" to "+candidate['label']
                print e
                worked = False 
                pass
            if worked:
                try:
                    if not rms == []:
                        for value in rms:
                            client.system.removeEntitlements(key,systemid,[value])
                    if not adds == []:
                        for value in adds:
                            client.system.addEntitlements(key,systemid,[value])
                except xmlrpclib.Fault, e:
                    print "operation failed on system "+str(systemid)+"while altering the entitlements"
                    print "additions attempted : "+str(adds)
                    print "removals attempted : "+str(rms)
                    print "the error was :"
                    print e
                    if rms.count('virtualization_host') == 1 or rms.count('virtualization_host_platform') == 1:
                        information_host = analyse_consumption(key,systemid)
                        print "the confumtion of the guests of that system approximates to these entitlements"
                        for name in sorted(information_host.keys()):
                            print " - name - "+str(information_host[name])
                    print " this change will not happen and we will restore the channels for that system"
                    worked = False
                    pass
                try:
                    restore_channels(key,systemid,channeldata)
                except xmlrpclib.Fault, e:
                    print "unable to restore the base channel for system "+systemid+" with reason"
                    print e
                    print "the channel data was"
                    print channeldata
            
            return worked
    print "no Red Hat Channel found for system "+str(systemid)+", nothing was done to it"
    return False

#returns true if that's a system, false and shows an error if not"
def is_a_system(key,systemid):
    global client;
    try:
        client.system.getRegistrationDate(key,systemid)
        return True
    except xmlrpclib.Fault:
        return False
        pass

def systems_by_name(key,systemname,groupname=None):
    global client;
    systems = []
    try:
        if groupname == None:
            for system in client.system.getId(key,systemname):
                systems.append(system['id'])
        else:
            for system in client.system.getId(key,systemname):
                for group in client.system.listGroups(key,system):
                    if group['subscribed'] == 1 and group['system_group_name'] == groupname:
                        systems.append(system)
    except xmlrpclib.Fault, e:
        print e
        pass
    return systems

#asks what systems to add or which systems to remove if given  a group name.
def ask_systems(key,groupname=None):
    list_systems(key,groupname)
    if not groupname == None:
        action = "remove from "+groupname
    else:
        action = "add"
    systems=[]
    while True:
        answer = raw_input("ID or name of the system to "+action+"  (press enter to finish, A for all):").strip()
        if answer == "":
            break
        elif answer == 'a' or answer == 'A':
            #will assign all sytems in the list or all systems of the group if groupname has been defined
            systems = all_systems(key,groupname)
            break
        elif answer.isdigit() and is_a_system(key,int(answer)):
            systems.append(int(answer))
        else:
            for systemid in systems_by_name(key,answer,groupname):
                systems.append(systemid)
            continue
    return systems
   

def alter_systemgroup(key, groupname, systems=[],adding=True):
    global client;
    try:
        client.systemgroup.addOrRemoveSystems(key,groupname, systems, adding)
    except xmlrpclib.Fault, e:
        print "unable to alter the group"
        print e
        pass
    return

#here is done the operations that will be done to the systems listed
def ask_operation(key,systems=[]):
    questions={'enterprise_entitled':"do you want to Assign or Skip enterprise entitlements (also known as Management entitlements)(a/s)?",
            'provisioning_entitled':"do you want to Assign, Remove or Skip provisioning entitlements (a/r/s)?",
            'monitoring_entitled':"do you want to Assign, Remove or Skip monitoring entitlements (a/r/s)?",
            'virtualization_host_platform':"do you want to Assign, Remove or Skip virtual host platform (a/r/s)?",
            'virtualization_host':"do you want to Assign, Remove or Skip virtual host (a/r/s)?"}
    adds=[]
    rms=[]
    for entitlement, question in questions.iteritems():
        if entitlement == 'virtualization_host' or entitlement == 'virtualization_host_platform':
            print "note that adding virtualization_host_platform will remove virtualization_host and vice versa"
        while True:
            answer = raw_input(question).strip()
            if answer == 'a' or answer == 'A':
                if entitlement == 'virtualization_host_platform':
                    rms.append('virtualization_host')
                    if adds.count('virtualization_host'):
                        print "replacing choice of virtualization host with virtualization host platform"
                        adds.remove('virtualization_host')
                        rms.remove('virtualization_host_plaform')
                elif entitlement == 'virtualization_host':
                    rms.append('virtualization_host_plaform')
                    if adds.count('virtualization_host_platform') > 0:
                        print "replacing choice of virtualization host platform with virtualization host"
                        adds.remove('virtualization_host_platform')
                        rms.remove('virtualization_host')
                adds.append(entitlement)
                break
            elif answer == 'r' or answer == 'R':
                if  entitlement == 'enterprise_entitled':
                    print "this script will not remove management entitlements"
                else:
                    rms.append(entitlement)
                    print 
                break
            elif answer == 's' or answer =='S' :
                break
            continue
    if len(rms) > 0 or len(adds) > 0:
        passes = 0
        fails = 0
        for system in systems:
            print "working on "+str(system)
            if change_system(key,system,adds,rms):
                passes+=1
            else:
                fails+=1
        print str(passes + fails)+" systems touched, "+str(passes)+" passed and "+str(fails)+" failed"
    else:
        print "nothing to do, skip"
    return

def ask_batchchange(key,orgid,groupname,adding=True):
    list_systems(key,groupname)
    if adding:
        question = "Would you like to add systems to that list [y/n]?"
    else:
        question = "Would you like to remove systems from the group[y/n]?"
    while True:
        answer = raw_input(question).strip()
        if answer == 'y' or answer == 'Y' :
            alter_systemgroup(key,groupname,ask_systems(key),adding)
            break
        elif answer == 'n' or answer == 'N':
            break
    pass

def is_group_empty(key,groupname):
    global client;
    if len(client.systemgroup.listSystems(key,groupname)) > 0:
        return False
    else:
        return True


#batch mode process
def ask_batchmode(key,orgid):
    global client;
    groupname = select_systemgroup(key,orgid)
    while True:
        ask_batchchange(key,orgid,groupname)
        ask_batchchange(key,orgid,groupname,False)
        answer = raw_input( "stop altering the group?[Y/n]").strip()
        if answer == 'n' or answer == 'N':
            continue
        else:
            break
    if is_group_empty(key,groupname):
        print "the group is empty - no operation will be done"
        return
    ask_operation(key,all_systems(key,groupname))
    list_systems(key,groupname)
    while True:
        answer =  raw_input("Do you wish to clear, delete or leave the group as is(c/d/L)?").strip()
        if answer == 'c' or answer == 'C':
            alter_systemgroup(key,groupname,all_systems(key,groupname),False)
            break
        elif answer == 'd' or answer == 'D':
            try:
                client.systemgroup.delete(key,groupname)
                print "group deleted"
            except xmlrpclib.Fault, e:
                print "group not deleted : "
                print e
                pass
            break
        else:
            break
    return


#asks if we edit 1 system or a batch, then starts the appropriate function for that mode
def ask_mode(key,orgid):
    print "enter a systemid to edit one system, B for batch mode or A for all"
    action = raw_input("sytemID/Batch/All?").strip()
    if action == "":
        return
    elif action == 'A' or action == 'a':
        ask_operation(key,all_systems(key))
    elif action == 'B' or action == 'b':
        ask_batchmode(key,orgid)
    elif is_a_system(key,int(action)):
        ask_operation(key,[int(action)])
    else:
        ask_mode(key)
    return


#################################
### the main code starts here ###
#################################
# initializing the first connection to the satellite
while True:
    key = session_init()
    #then let's try to see if we are in a sub organization ; this also sets orgid to the id of the organization.
    userdetails = client.user.getDetails(key,SATELLITE_LOGIN)
    orgid = userdetails['org_id']
    orgdetails = client.org.getDetails(key,orgid)
    if orgid != 1:
        #we are in a sub org
        orgdetails = client.org.getDetails(key,orgid)
        print "you are not from the base organizaion but from "+orgdetails['name']
        sub_org = True
    else:
        #base org
        print "you are org admin"
        sub_org = False
        orgid = org_select(key)
        if orgid == None:
            print "No selection, leaving"
            client.auth.logout(key)
            break
        elif orgid == 1:
            print "staying in the base organization"
        else:
            orgdetails = client.org.getDetails(key,orgid)
            print "switching to an admin for sub-organization "+orgdetails['name']
            client.auth.logout(key)
            key = session_init(orgdetails['name'])
    # displays the list of systems and starts going through the assistant
    while True:
        list_systems(key)
        ask_mode(key,orgid)
        answer= raw_input("Continue working in organziation "+orgdetails['name']+"(y/N)?")
        if answer == 'y' or answer == 'Y':
            continue
        else:
            break
    client.auth.logout(key)
    if sub_org:
        break
    else:
        print "re-logging as base org admin"

#end

