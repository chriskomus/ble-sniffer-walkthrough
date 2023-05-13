import gatt
import time
import configparser

# Read configuration file
config = configparser.ConfigParser()
config.read('ble_config.ini')

NOTIFY_CHAR_UUID = config.get('monitor', 'notify_char_uuid', fallback=None)
MAC_ADDRESS = config.get('monitor', 'mac_address', fallback=None)

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
        self.on_data_received(value)

    def on_data_received(self, value):
        print(f"Got packet of len(value)={len(value)}: {value.hex()}")

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
    if MAC_ADDRESS:
        mac = MAC_ADDRESS.lower()
        if dev.mac_address.lower() == mac:
            print("Trying to connect to {}...".format(dev.mac_address))
            try:
                device = AnyDevice(mac_address=mac, manager=manager)
            except Exception as e:
                print(e)
                continue

            device.connect()

if MAC_ADDRESS:
    print("Terminate with Ctrl+C")

    try:
        manager.run()
    except KeyboardInterrupt:
        pass

    for dev in manager.devices():
        device.disconnect()
else:
    print("Choose a mac address from the list and enter it into ble_config.ini")