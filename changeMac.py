import winreg
import itertools
import re
import subprocess

REG_KEY_PATH_INTERFACES = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"


def get_reg_value(name, reg_key_path):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path) as registry_key:
            value, regtype = winreg.QueryValueEx(registry_key, name)
            return value
    except OSError:
        return None


def set_reg_value(name, value, reg_key_path):
    try:
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path):
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path, 0, winreg.KEY_WRITE) as current_key:
                winreg.SetValueEx(current_key, name, 0, winreg.REG_SZ, value)
        return True
    except OSError:
        return False


def del_reg_value(name, reg_key_path):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key_path, 0, winreg.KEY_WRITE) as registry_key:
            winreg.DeleteValue(registry_key, name)
            return True
    except OSError:
        return False


def san_mac(mac):
    mac1 = re.sub('[^a-fA-F\d]', '', mac)
    if len(mac1) != 12:
        print("Invalid MAC supplied")
        return False
    return mac1


def san_guid(net_cfg_instance_id):
    m = re.search('[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', net_cfg_instance_id)
    if m:
        return m.group(0)
    else:
        print("Invalid GUID supplied")
        return False


def set_mac_value(mac, guid):
    guid = san_guid(guid)
    guid = "{" + guid + "}"
    mac = san_mac(mac)
    try:
        subkeys = []
        # get the path names of all subkeys which are interfaces
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY_PATH_INTERFACES) as registry_key:
            for i in itertools.count(start=0, step=1):
                try:
                    subkey_name = winreg.EnumKey(registry_key, i)
                    if len(subkey_name) == 4:
                        subkeys.append(subkey_name)
                except OSError:
                    break
        # loop through all interfaces and check which is the correct to edit
        for interface in subkeys:
            tmp_path = REG_KEY_PATH_INTERFACES + "\\" + interface
            net_cfg_instance_id = get_reg_value("NetCfgInstanceId", tmp_path)
            if net_cfg_instance_id == guid:
                if set_reg_value("NetworkAddress", mac, tmp_path):
                    print("MAC of " + str(guid) + " changed to " + str(mac))
                    return True
                else:
                    return False
        return False
    except OSError:
        return None


def restart_network_interface(guid):
    guid = san_guid(guid)
    # parse interface name out of guid
    r = subprocess.run(["getmac", "/fo", "csv", "/V"], capture_output=True).stdout.decode('utf-8')
    r = r.split(",")
    interface_name = ""
    for i, j in enumerate(r):
        if guid in j:
            interface_name = r[i - 3].split("\r\n")[1]
    if len(interface_name) == 0:
        print("Could not find interface name, you need to restart the network interface on your own."
              "\r\nUse this command:")
        print('netsh interface set interface name="<insert interface name>" admin="enabled"')
        return False

    # trigger restart of networks interface
    cmd1 = 'netsh interface set interface name=' + interface_name + ' admin="disabled"'
    subprocess.run(cmd1)
    cmd2 = 'netsh interface set interface name=' + interface_name + ' admin="enabled"'
    subprocess.run(cmd2)
    return True


def remove_mac_value(guid):
    guid = san_guid(guid)
    guid = "{" + guid + "}"
    try:
        subkeys = []
        # get the path names of all subkeys which are interfaces
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY_PATH_INTERFACES) as registry_key:
            for i in itertools.count(start=0, step=1):
                try:
                    subkey_name = winreg.EnumKey(registry_key, i)
                    if len(subkey_name) == 4:
                        subkeys.append(subkey_name)
                except OSError:
                    break
        # loop through all interfaces and check which is the correct to remove
        for interface in subkeys:
            tmp_path = REG_KEY_PATH_INTERFACES + "\\" + interface
            net_cfg_instance_id = get_reg_value("NetCfgInstanceId", tmp_path)
            if net_cfg_instance_id == guid:
                if del_reg_value("NetworkAddress", tmp_path):
                    print("Resetted MAC of " + str(guid) + " to default.")
                    return True
                else:
                    return False
        return False
    except OSError:
        return None
