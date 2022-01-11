# MacForger
This is Python 3 software to spoof the MAC address in Windows. Properly it is a graphical interface for the repository "change-mac" of inc0x0.

Original repository:
[inc0x0/change_mac](https://github.com/inc0x0/change-mac)

### Prerequisites

1) Python 3
2) Pip3 (see requirequirements.txt)


### Installing

You can it compile by yourself for the standalone usage or you can simply install requirements and execute it as normal python script.
```
pip3 install -r requirements.txt 
```

## How it works

It requires Administrative privileges to create a key in Windows Register.
When you execute the software, it requires UAC to elevate the privileges.
After you have provide the super user privilages, it's normal if it requires some times to open because it has to check for each interface's physical address (MAC).

The GUI is really simple, on the top you can find the avaible interfaces (MAC spoofing may be not avaible for some interfaces). In the middle there's written the actual MAC address of the adapter currently selected, in the right top corner you can look for the button to reload all available intefaces with either MAC addresses.
Restore Default button provides the possibility to remove the register key and so restore the default MAC address.
Random button is usefull to generate a valid MAC (some adapters requires the first byte equal to 22, if you select "fix 1° byte" it generates MAC following this rule).
Confirm is the execution button, you can confirm the spoof with this.


## Software GUI
![GUI](https://github.com/Marco-Valle/MacForger/blob/main/gui.png)

## Authors

* **Marco Valle** - [Marco-Valle](https://github.com/Marco-Valle)
* **inc0x0** - [inc0x0](https://github.com/inc0x0)

## License

This project is licensed under the GPL v3 License - see the [LICENSE](LICENSE) file for details
