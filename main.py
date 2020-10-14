from tkinter import Tk, W, E, N, CENTER, OptionMenu, StringVar, BooleanVar, messagebox
from tkinter.ttk import Frame, Button, Checkbutton, Entry, Style, Label
from getmac import get_mac_address
from psutil import net_if_addrs
from ifaddr import get_adapters
from random import randint
from elevate import elevate
import changeMac
import ctypes
import re


class MacForger(Frame):

    def __init__(self):
        super().__init__()

        self.interfaces = []                            # List of all network interfaces
        self.adapters = {}                              # Dict with all network interfaces info { name : (MAC, GUID) }
        self.mac = StringVar()                          # Written MAC
        self.actual_mac = StringVar()                   # Actual MAC of selected interface
        self.interface_selected = StringVar()           # Actual interface selected
        self.reload_interface = BooleanVar(value=True)  # Reload after MAC change
        self.fix_first_byte = BooleanVar(value=True)    # Some adapters accept MAC spoof only if the first byte's equal than 22

        self.update_interfaces()        # Update adapters info
        self.init_ui()                  # Initialize user interface
        self.set_default_interface()    # We set Wifi adapter as default one
        self.reload_mac()               # Reload MAC shown

    def init_ui(self):
        self.master.title("MAC forger")
        self.master.resizable(False, False)

        Style().configure("TButton", padding=(0, 5, 0, 5), font='serif 10', foreground='Blue')
        Style().configure("TLabel", font='serif 10')
        Style().configure("TCheckbutton", foreground='Blue')
        Style().configure("mac.TLabel", font='serif 12', foreground='Red')

        title = Label(self, text="MAC forger")
        title.grid(row=0)

        interfaces_label = Label(self.master, text="Interface:")
        interfaces_label.grid(row=1, column=0, sticky=E, pady=10, padx=20)
        self.interface_selected.set(self.interfaces[0])
        interfaces = OptionMenu(self.master, self.interface_selected, *self.interfaces)
        interfaces.grid(row=1, column=1, sticky=(E, W), pady=10, padx=20)
        self.interface_selected.trace_add('write', self.reload_mac)
        reload_button = Button(self.master, text="Reload", command=self.update_interface)
        reload_button.grid(row=1, column=2, pady=10, padx=10)
        reload_button = Button(self.master, text="Reload All", command=self.update_interfaces)
        reload_button.grid(row=1, column=3, pady=10, padx=10)

        actual_mac_label = Label(self.master, text="Actual MAC Address:")
        actual_mac_label.grid(row=2, column=0, sticky=E, pady=10, padx=20, rowspan=2)
        actual_mac = Label(self.master, style='mac.TLabel', justify=CENTER, textvariable=self.actual_mac)
        actual_mac.grid(row=2, column=1, pady=10, padx=20, rowspan=2)
        self.actual_mac.set("FF : FF : FF : FF : FF : FF")
        reload_interface = Checkbutton(self.master, text=" Reload interface\n after changes", variable=self.reload_interface)
        reload_interface.grid(row=2, column=2, padx=5, rowspan=2, sticky=(N, W))
        fix_button = Checkbutton(self.master, text="  Fix 1° byte", variable=self.fix_first_byte)
        fix_button.grid(row=3, column=2, padx=5, rowspan=2, sticky=(N, W))
        reset_button = Button(self.master, text="Restore\n Default", command=self.reset_mac)
        reset_button.grid(row=2, column=3, pady=10, padx=5, rowspan=2)

        mac_label = Label(self.master, text="MAC Address: ")
        mac_label.grid(row=4, column=0, sticky=E, pady=10, padx=20)
        mac_entry = Entry(width=25, justify=CENTER, font='serif 12', textvariable=self.mac)
        mac_entry.grid(row=4, column=1, pady=10, padx=20)
        self.mac.set("FF:FF:FF:FF:FF:FF")
        self.mac.trace_add('write', self.mac_entry_rules)
        random_button = Button(self.master, text="Generate\nRandom", command=self.random_mac)
        random_button.grid(row=4, column=2, pady=10, padx=5)
        change_button = Button(self.master, text="Confirm\n  MAC", command=self.change_mac)
        change_button.grid(row=4, column=3, pady=10, padx=5)

    def set_default_interface(self):
        # Set Wifi adapter as default one if exists
        try:
            self.adapters["Wi-Fi"]
            self.interface_selected.set("Wi-Fi")
        except KeyError:
            self.interface_selected.set(self.interfaces[0])

    def mac_entry_rules(self, *args):
        # This function provides a real time validation for the MAC address
        pattern = re.compile('(?:[0-9a-fA-F:]:?)')
        if len(self.mac.get()) > 17:
            self.mac.set(self.mac.get()[0:17])
        for i in self.mac.get():
            if not bool(pattern.match(i)):
                self.mac.set(self.mac.get().replace(i, ''))
        self.mac.set(self.mac.get().upper())

    def validate_mac(self):
        # This function validates the MAC given before trying to change the old one
        tmp = self.mac.get()
        # If starts with : we add two zero
        if tmp[0] == ":":
            tmp = "00"+tmp
        # Check the correct length
        if len(tmp) == 12:
            # Add the two points where are missing
            tmp = tmp[:2] + ':' + tmp[2:4] + ':' + tmp[4:6] + ':' + tmp[6:8] + ':' + tmp[8:10] + ':' + tmp[10:12]
        if len(tmp) < 17:
            tmp = tmp + "0" * (17 - len(tmp))
        # Add : where are needed
        hot_idx = [2, 5, 8, 11, 14]
        for i in hot_idx:
            if tmp[i] != ":":
                tmp = tmp[:i] + ":" + tmp[i+1:]
        self.mac.set(tmp)
        # Check again the length
        if len(self.mac.get()) > 17:
            self.mac.set(self.mac.get()[0:17])
        # Check the pattern
        pattern = re.compile('(?:[0-9a-fA-F]:?){12}')
        return bool(pattern.match(self.mac.get()))

    def reload_mac(self, *args):
        # Reload the MAC label with the actual MAC of the selected interface
        try:
            self.actual_mac.set(self.adapters[self.interface_selected.get()][0].replace(":", " : ").upper())
        except AttributeError:
            # This occurs when the interface is virtual and doesn't have a physical address
            self.actual_mac.set("00 : 00 : 00 : 00 : 00 : 00")

    def reload(self, guid):
        # If required reload the network interface
        if self.reload_interface.get():
            if changeMac.restart_network_interface(guid=guid):
                messagebox.showinfo("Info", "Interface reloaded")
            else:
                messagebox.showinfo("Info", "Cannot reload interface.\nProbably the interface is off.")

    def change_mac(self):
        # Set the MAC of the selected interfaces with the given value
        guid = self.adapters[self.interface_selected.get()][1]
        if self.validate_mac():
            print("Trying to change the MAC of {} to {}".format(guid, self.mac.get()))
            if messagebox.askokcancel("Spoof", "Trying to change the MAC of {} to {}".format(guid, self.mac.get()), default="cancel", icon="warning"):
                changeMac.set_mac_value(self.mac.get(), guid=guid)
                self.reload(guid)
                self.update_interface()
                self.reload_mac()
            else:
                print("MAC changes cancelled")
        else:
            print("Not valid MAC inserted")
            messagebox.showwarning("Warning", "Not valid MAC inserted")

    def reset_mac(self):
        # Restore the original MAC
        guid = self.get_guid()
        print("Trying to restore the MAC of {}".format(guid))
        if messagebox.askokcancel("Restore", "Trying to restore the MAC of {}".format(guid), default="cancel", icon="warning"):
            changeMac.remove_mac_value(guid=guid)
            self.reload(guid)
            self.update_interface()
            self.reload_mac()
        else:
            print("MAC restore cancelled")

    def random_mac(self):
        # Define a Random MAC
        mac = ''
        # Manufacturer's bytes
        r = randint(0, 13)
        if r == 0:
            mac += "CC:46:D6"
        elif r == 1:
            mac += "3C:5A:B4"
        elif r == 2:
            mac += "3C:D9:2B"
        elif r == 3:
            mac += "00:9A:CD"
        elif r == 4:
            mac += "D0:D0:03"
        elif r == 5:
            mac += "B0:65:F1"
        elif r == 6:
            mac += "AC:B1:EE"
        elif r == 7:
            mac += "AC:81:F3"
        elif r == 8:
            mac += "E8:CC:32"
        elif r == 9:
            mac += "00:30:48"
        elif r == 10:
            mac += "40:D3:AE"
        elif r == 11:
            mac += "10:72:23"
        elif r == 12:
            mac += "00:21:2F"
        elif r == 13:
            mac += "00:14:5A"
        if self.fix_first_byte.get():
            # Some adapters allow to spoof MAC but with the first byte must be equal then 22
            mac = "22" + ':' + mac[3:]
        mac += ":"
        # Random bytes
        for i in range(6):
            r = randint(0, 15)
            if r >= 10:
                if r == 10:
                    r = "A"
                elif r == 11:
                    r = "B"
                elif r == 12:
                    r = "C"
                elif r == 13:
                    r = "D"
                elif r == 14:
                    r = "E"
                elif r == 15:
                    r = "F"
            else:
                r = str(r)
            mac += r
            if i != 5 and (i % 2) != 0:
                mac += ":"
        self.mac.set(mac)

    def get_guid(self, interface=None):
        # GUID is properly name of network interfaces in Windows
        guid = None
        adapters = get_adapters()
        if interface is None:
            interface = self.interface_selected.get()
        for a in adapters:
            if a.ips[0].nice_name == interface:
                guid = a.name
        return str(guid)

    def update_interface(self):
        # Update the selected interface info ( MAC, GUID)
        self.adapters[self.interface_selected.get()] = \
            (get_mac_address(self.interface_selected.get()), self.get_guid())
        # Reload MAC label
        self.reload_mac()

    def update_interfaces(self):
        # Get the available interfaces and the relative info
        self.interfaces = []
        self.adapters = {}
        interfaces = list(net_if_addrs().keys())
        for i in interfaces:
            # Get MAC
            mac = get_mac_address(i)
            if mac is not None:
                # Get GUID
                guid = self.get_guid(interface=i)
                self.interfaces.append(i)
                self.adapters[i] = (mac, guid)
        # Set the default
        self.set_default_interface()
        # Reload MAC label
        self.reload_mac()


if __name__ == '__main__':
    if ctypes.windll.shell32.IsUserAnAdmin():
        # Run application as Administrator
        root = Tk()
        root.iconbitmap("icon.ico")
        root.title("loading")
        app = MacForger()
        root.mainloop()
    else:
        # Require UAC
        elevate(show_console=False)
