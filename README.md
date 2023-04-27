# Reverse Engineer Junctek BT Guide

In order to get data off the Junctek via the BT I had to reverse engineer the data that was being sent over Bluetooth. This is more of a guide to remind myself how to do it if I have to go through it again.

# Examine and Log The Data

1. Install nRF Connect on iOS or Android. Open it up and connect to the Junctek device. It should be something like `BTG004`.
2. Under the Client tab scroll through the Attribute Table section and hit the down arrow button to start pulling values from the device. Subscribe to values with the down arrow with the line under it. This will start pulling a continuous stream of information.
3. Take note of the values that appear on the Junctek device screen. Write down the time along with the volts, amps, Ah, SoC (state of charge), power, and time left:
```
--11:53pm
12.32v
0.2a
0.1a
0.2a
38.895Ah
2.46w
1.23w
86% charge
311h:09m
```
4. Let it run for a minute or two and note any changes. Getting a few different values per parameter would be ideal. Add loads, turn things off, that sort of thing.
5. Go to the Log tab and export the data as text, open up in a text editor and start looking at all the results. It should look like this:
```
Scanner On.
Device Scanned.

...

[Callback] peripheral(peripheral, didUpdateValueForCharacteristic: FFE1, error: nil)
Updated Value of Characteristic FFE1 to 0xBB148815D5115232F369EE.
"0xBB148815D5115232F369EE" value received.
[Callback] peripheral(peripheral, didUpdateValueForCharacteristic: FFE1, error: nil)
Updated Value of Characteristic FFE1 to 0xBB40C10491D809EE.
"0xBB40C10491D809EE" value received.
[Callback] peripheral(peripheral, didUpdateValueForCharacteristic: FFE1, error: nil)
Updated Value of Characteristic FFE1 to 0xBB148816D5115233F371EE.
"0xBB148816D5115233F371EE" value received.
[Callback] peripheral(peripheral, didUpdateValueForCharacteristic: FFE1, error: nil)
Updated Value of Characteristic FFE1 to 0xBB148817D5115234F373EE.
"0xBB148817D5115234F373EE" value received.
```
6. Go back and repeat the process a couple times to get more data, but keeping things in separate files will make it easier to search for values.
7. Look through the notes and start searching for values. ie: Ah readings of 38.895Ah, search for `38895`:
```
[Callback] peripheral(peripheral, didUpdateValueForCharacteristic: FFE1, error: nil)
Updated Value of Characteristic FFE1 to 0xBB148623D5038895D2114920F352EE.
```
8. Add that to the notes:
```
...
38.895Ah - Updated Value of Characteristic FFE1 to 0xBB148623D5038895D2114920F352EE
...
```
9. Repeat this process until all values in the notes have an associated Characteristic update. To find 'time left', convert hours to minutes.
10. Start looking at the different characterists for a field, ie: volts or aH. Look for similarities in the bytes.
11. Set aside for now and proceed to next section.

# Set up a test script to confirm results

1. Scan for bluetooth devices.
```
sudo bluetoothctl
scan on
```
2. A bunch of devices should start displaying. Look for one with the name like `BTGXXX`. Copy the mac address for the next step.
3. Create a new py test file with the following code, change the mac address to the device:
```python
import gatt
import time

NOTIFY_CHAR_UUID = ""

class AnyDeviceManager(gatt.DeviceManager):
    def device_discovered(self, device):
        print("Discovered [%s] %s" % (device.mac_address, device.alias()))

class AnyDevice(gatt.Device):
    def connect_succeeded(self):
        super().connect_succeeded()
        print("[%s] Connected" % (self.mac_address))

    def connect_failed(self, error):
        super().connect_failed(error)
        print("[%s] Connection failed: %s" % (self.mac_address, str(error)))

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        print("[%s] Disconnected" % (self.mac_address))
        print("[%s] Reconnecting in 10 seconds" % (self.mac_address))
        time.sleep(10)
        self.connect()

    def services_resolved(self):
        super().services_resolved()

        print("[%s] Resolved services" % (self.mac_address))
        for service in self.services:
            print("[%s]  Service [%s]" % (self.mac_address, service.uuid))
            for characteristic in service.characteristics:
                if not NOTIFY_CHAR_UUID:
                    print("[%s]    Characteristic [%s]" % (self.mac_address, characteristic.uuid))
                elif characteristic.uuid == NOTIFY_CHAR_UUID:
                    print("[%s]    Enabling Notifications for Characteristic [%s]" % (self.mac_address, characteristic.uuid))
                    characteristic.enable_notifications()

    def characteristic_enable_notifications_succeeded(self, characteristic):
        print('characteristic_enable_notifications_succeeded')

    def characteristic_enable_notifications_failed(self, characteristic, error):
        print('characteristic_enable_notifications_failed')

    def characteristic_value_updated(self, characteristic, value):
        super().characteristic_value_updated(characteristic, value)
        print(f"characteristic={characteristic.uuid} value={value}")

manager = gatt.DeviceManager(adapter_name='hci0')

# Run discovery
manager.update_devices()
print("Starting discovery...")
# scan all the advertisements from the services list
manager.start_discovery()
discovering = True
wait = 15
found = []
# delay / sleep for 10 ~ 15 sec to complete the scanning
while discovering:
    time.sleep(1)
    f = len(manager.devices())
    print("Found {} BLE-devices so far".format(f))
    found.append(f)
    if len(found) > 5:
        if found[len(found) - 5] == f:
            # We did not find any new devices the last 5 seconds
            discovering = False
    wait = wait - 1
    if wait == 0:
        discovering = False

manager.stop_discovery()
print("Found {} BLE-devices".format(len(manager.devices())))

for dev in manager.devices():
    print("Processing device {} {}".format(dev.mac_address, dev.alias()))
    mac = '38:3b:26:79:df:37'.lower()
    if dev.mac_address.lower() == mac:
        print("Trying to connect to {}...".format(dev.mac_address))
        try:
            device = AnyDevice(mac_address='38:3b:26:79:df:37', manager=manager)
        except Exception as e:
            print(e)
            continue

        device.connect()

print("Terminate with Ctrl+C")

try:
    manager.run()
except KeyboardInterrupt:
    pass

for dev in manager.devices():
    device.disconnect()
```
2. Run the script and connect to the device:
```
python3 test.py
```
3. There should be some results that look like this:
```
[38:3b:26:79:df:37] Connected
[38:3b:26:79:df:37] Resolved services
[38:3b:26:79:df:37]  Service [0000ffe0-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [0000ffe2-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [0000ffe1-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]  Service [0000fff0-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [0000fff3-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [0000fff2-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [0000fff1-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]  Service [0000180a-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a50-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a29-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a28-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a27-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a26-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a25-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a24-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a23-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]  Service [00001801-0000-1000-8000-00805f9b34fb]
[38:3b:26:79:df:37]    Characteristic [00002a05-0000-1000-8000-00805f9b34fb]
```
4. In the previous section it was discovered that all values were written to FFE1, as they all looked like this:
```
Updated Value of Characteristic FFE1 to 0xBB148815D5115232F369EE.
```
5. From that we can assume that the NOTIFY_SERVICE_UUID is `0000ffe1-0000-1000-8000-00805f9b34fb` based on the data returned in step 2:
```
[38:3b:26:79:df:37]    Characteristic [0000ffe1-0000-1000-8000-00805f9b34fb]
```
6. Set `NOTIFY_SERVICE_UUID` to the UUID in the python script. Run the script again.
```
```
