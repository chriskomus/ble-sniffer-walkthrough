import gatt
import time

NOTIFY_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
MAC_ADDRESS = "38:3b:26:79:df:37"

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

    def bytes_to_int(self, bs, offset, length):
        # Reads data from a list of bytes, and converts to an int
        # Bytes2Int(bs, 3, 2)
        ret = 0
        if len(bs) < (offset + length):
            return ret
        if length > 0:
            # offset = 11, length = 2 => 11 - 12
            byteorder='big'
            start = offset
            end = offset + length
        else:
            # offset = 11, length = -2 => 10 - 11
            byteorder='little'
            start = offset + length + 1
            end = offset + 1
        # Easier to read than the bitshifting below
        return int.from_bytes(bs[start:end], byteorder=byteorder)

    def on_data_received(self, value):
        print(f"Got packet of len: {len(value)} {value.hex()}")
        # data = self.parse_bytes(value)
        # for key in data:
        #     # self.data[key] = data[key]
        #     print(f"key={key} value={data[key]}")

    def parse_bytes(self, bs):
        data = {}
        data['test'] = self.bytes_to_int(bs, 2, 4)
        # data['battery_percentage'] = self.bytes_to_int(bs, 3, 2)
        data['battery_voltage'] = self.bytes_to_int(bs, 2, 4)
        # data['battery_current'] = self.bytes_to_int(bs, 7, 2)
        return data

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
    mac = MAC_ADDRESS.lower()
    if dev.mac_address.lower() == mac:
        print("Trying to connect to {}...".format(dev.mac_address))
        try:
            device = AnyDevice(mac_address=mac, manager=manager)
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