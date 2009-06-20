class NetInterface:

    def __init__(self, type, mode, switchname=None, switchport=None, hostport=None, ipaddress=None, mtu=9000, vlans=[]):

        self.type = type
        self.mode = mode
        self.switchname = switchname
        self.switchport = switchport
        self.hostport = hostport
        self.ipaddress = ipaddress
        self.mtu = mtu
        self.vlans = vlans

        log.debug("Created interface with vlans: %s", self.vlans)

    def __repr__(self):
        return '<Interface %s:%s %s:%s (%s)>' % (self.type, self.mode, self.switchname, self.switchport, self.ipaddress)

def create_netinterface_from_node(node, defaults, parent):
    """
    Create a network interface from an XML node
    """
    try:
        switchname = node.find('switchname').text
        switchport = node.find('switchport').text
    except AttributeError, e:
        if not is_virtual:
            log.warn("Host switch configuration not present for %s: %s", hostname, e)
        switchname = None
        switchport = None

    try:
        hostport = node.find('hostport').text
    except AttributeError, e:
        log.warn("No host port defined for host: %s", hostname)
        hostport = None

    try:
        ipaddr = node.find('ipaddr').text
    except AttributeError:
        ipaddr = None


    type = node.attrib['type']
    try:
        mode = node.attrib['mode']
    except KeyError:
        mode = 'passive'

    try:
        mtu = int(node.attrib['mtu'])
    except KeyError:
        # If the MTU isn't set on the interface, use the project VLAN MTU
        vlan = self.get_project_vlan(site.type)
        mtu = vlan.mtu

    # Figure out the VLANs this interface should be in.
    # If one isn't defined, but it in the first 'project' VLAN
    vlan_nums = node.findall('vlan_number')
    if len(vlan_nums) == 0:
        vlans = [ vlan for vlan in self.vlans if vlan.site == site.type and vlan.type == 'project' ]

    else:
        # Find all the vlans this interface can talk to (ie: it's a trunk)
        vlans = []
        for vlan_num in vlan_nums:
            vlans.extend([ vlan for vlan in self.vlans if vlan.site == site.type and vlan.number == vlan_num.text ])
            pass
        pass

    # Add the required switch to the project switches list
    if switchname is not None:
        try:
            switch = self.known_switches[switchname]
        except KeyError:
            raise KeyError("Switch '%s' is not defined. Is it in switches.conf?" % switchname)

        log.debug("Adding switch '%s' to project switch list at site '%s'", switch, site)
        switch.site = site
        self.project_switches[switchname] = switch

        # If this is an edge, make sure its connected cores are added to the
        # list of project switches.
        if switch.type == 'edge':
            for coreswitch in switch.connected_switches:
                if coreswitch not in self.project_switches:
                    self.project_switches[coreswitch] = self.known_switches[coreswitch]
                    self.project_switches[coreswitch].site = site
                    pass
                pass
            pass

    # Sanity check the interface parameters. The combination of switchname+switchport should
    # only occur once, unless either is None, in which case it doesn't matter.
    for iface in self.interfaces:
        #log.debug("checking interface: %s", iface)

        if iface.switchname is not None and iface.switchname == switchname and iface.switchport == switchport:
            log.warn("switch:port combination '%s:%s' is used more than once in project config." % (switchname, switchport) )

    iface = network.Interface(type, mode, switchname, switchport, hostport, ipaddr, mtu, vlans)
    return iface

