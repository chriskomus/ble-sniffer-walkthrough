# BLE Sniffer with Raspberry Pi and Reverse Engineering Walkthrough

This guide uses a Raspberry Pi CM4 and a Junctek Bluetooth Battery Monitor as reference. But any BLE device can be reverse engineered to some degree. If it sends a steady stream of data, unencrypted, in a mix of hex code and decimals it will be very similar to this guide. Otherwise, further tinkering will be required.

In order to get battery volts, amps, watts, and charging information off the Junctek Battery Monitor, I had to reverse engineer the data that was transmitted over BlueTooth, using `gatt`, and the `ble_sniffer.py` script included in this repo. Once I had a stream of bytes it had to be parsed, interpreted, and then converted it into readable information.

## Examining the Bytes and Logging - via Python Script

1. Run the script and see a list of devices:
```
python3 ble_sniffer.py
```
2. A bunch of devices should start displaying. Look for one with the name like `BTGXXX`. Copy the mac address for the next step.
3. Copy the ini file
```
cp ble_config.ini.dist ble_config.ini
```
4. Open `ble_config.ini` in a text editor and set `mac_address` to the value found in step 2. Leave `notify_char_uuid` blank for now.
5. Run the script and connect to the device:
```
python3 ble_sniffer.py
```
6. There should be some results that look like this:
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
7. Press `ctrl+c` to stop once all Service and Characteristic uuids have been displayed.
8. Using trial and error, subscribe to each different Characteristic uuids and see what info is returned. An Android/iOS app like nRF Connect can be used as well (see appendix below). Generally, the desired information will all be on one characteristic uuid.
8. Set `notify_char_uuid` in `ble_config.ini` to one of the characteristic UUIDs above. Run `python3 ble_sniffer.py` again to see either:
```
characteristic_enable_notifications_failed
```
or
```
characteristic_enable_notifications_succeeded
```
If it successed there should be a stream of bytes like this:
```
Got packet of len: 18 bb275481d5025674d20249d4230337f389ee
Got packet of len: 18 bb275482d5025675d20251d4230338f300ee
Got packet of len: 18 bb275483d5025676d20252d4230339f304ee
Got packet of len: 18 bb275484d5025677d20253d4230340f314ee
Got packet of len: 18 bb275485d5025678d20254d4230341f318ee
Got packet of len: 10 bb025679d20256d406ee
Got packet of len: 11 bb275486d5230342f304ee
```
9. If bytes start streaming, take notes and write down what is being displayed on the battery monitor device screen. The devices displays this info, write it into a text editor:
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
10. While data is still streaming to the terminal, copy and paste the raw data into a text editor and start searching for values. Since the battery monitor was displaying 12.32v on screen, as shown in the notes in the last step, that data should be somewhere in the bytestreams. Search for 1232 (without the decimal). If the volt changes, search for the new value. Try this with other values like amps, watts, etc. If nothing is found, paste more stream data from the terminal. If still nothing is found, this is probably not the right Characteristic UUID. Press `ctrl+c` and go back to Step 8, using the next Characteristic UUID from the list in Step 6.
11. Repeat this process until values from the notes are found within the byte streams. ie: `Got packet of len: 9 bb1232c00246d850ee` contains `1232` which was recorded in the notes above, representing 12.32volts. It contains `0246` which was also recorded in the notes above, representing 2.46w.
12. This indicates that the script is listening to the correct Characteristic UUID. Continue recording, changing values on the battery monitor device by adding loads, charging, discharging, etc. Record any changes in the notes so that there is a good list of values to search for.
13. Let it run for a few more minutes, then press `ctrl+c`. Copy/paste the stream from the terminal to the text file.

## Making Sense Of It All

1. Here's a sample set of bytes that were captured:

```
Got packet of len: 9 bb1202c08414d867ee
Got packet of len: 9 bb1645d21913d444ee
Got packet of len: 9 bb1204c08548d822ee
Got packet of len: 9 bb0700c18407d842ee
Got packet of len: 9 bb0710c18541d817ee
Got packet of len: 12 bb1204c00500c16020d843ee
Got packet of len: 16 bb1205c00853d6022800d76025d813ee
Got packet of len: 9 bb1206c08562d850ee
Got packet of len: 9 bb1873d22187d416ee
Got packet of len: 9 bb1849d22157d426ee
Got packet of len: 9 bb1205c06025d851ee
```

2. While capturing, the battery monitor showed the following:
- volts: 12.02v, 12.04v, 12.05v, 12.06v
- amps: 7.00a, 7.10a, 5.00a
- watts: 84.14w, 85.62w, 60.25w
- ah remaining: 1.645ah, 1.873ah, 1.849ah

3. Start searching for values throughout the data. Look for the bytes before and after to see if there are any consistencies. Look at the length of bytes, if there are any values that are in every single byte stream. Check if multiple fields are in the samne bytestream (ie: are amps and volts sent at the same time). What is the byte length of each value, of the whole stream? Eventually things should start to make sense.

4. From the info gathering in the previous section, comparing what the battery montior displays and then searching for the values in the byte stream, some patterns begin to emerge:
- BB - every stream starts with
- EE - every stream ends with
- C0 - always comes after voltage
- C1 - always comes after amps
- D2 - always comes after amp hours remaining
- D6 - always comes after time remaining
- D8 - always comes after watts

I went through other hex values from A0 through FF, but couldn't find anything usable. There were a number of incremental values, but couldn't figure out if that was a clock, counter, or anything of use. In this case, getting volts, amps, watts, and ah remaining will be good enough. SoC (battery percentage) can be calculated by the aH remaining as a percentage of the aH of the battery. I couldn't find out whether it transmits charging state (charging vs discharging), and amps always display as a positive number regardless of the direction the amps are flowing.

5. Every device is different, but in the case of the Junctek battery monitor, it's returning bytestreams of varying lengths (anywhere between 9 to 18 bytes). The values for each parameter are often in varying lengths as well (1 to 3 bytes). This means that the best way to parse the data is to break eat byte strem up into segments beginning with `BB`, then a value of a parameter, then the hex key that represents that parameter. Then another value, then another hex key, and so on until a checksum, then ending with `EE`.

## Examples:

`bb1202c08414d867ee`:
- C0 - volt - 1202 = 12.02 volts
- D8 - watts - 8414 = 84.14 watts

`bb1204c00500c16020d843ee`:
- C0 - volt - 1204 = 12.04 volts
- C1 - amps - 0500 = 05.00 amps
- D8 - watts - 6020 = 60.20 watts

`bb1873d22187d416ee`:
- D2 - ah remaining - 1873 = 1.873 ah
- D4 - ???

`bb1205c00853d6022800d76025d813ee`:
- C0 - volt - 1205 = 12.05 volts
- D6 - time remaining - 0853 = 853 min or 15h:13m
- D7 - ???
- D8 - watts - 6025 = 60.25 watts

## Parsing and Returning Useful Information

This can be done a million different ways, but to break up the bytestream into usable information this is what I did:

```python
params = {
    "voltage": "C0",
    "current": "C1",
    "dir_of_current": "D1",
    "ah_remaining": "D2",
    "mins_remaining": "D6",
    "power": "D8",
    "temp": "D9"
}
battery_capacity_ah = 100

params_keys = list(params.keys())
params_values = list(params.values())

# split bs into a list of all values and hex keys
bs_list = [bs[i:i+2] for i in range(0, len(bs), 2)]

# reverse the list so that values come after hex params
bs_list_rev = list(reversed(bs_list))

values = {}
# iterate through the list and if a param is found,
# add it as a key to the dict. The value for that key is a
# concatenation of all following elements in the list
# until a non-numeric element appears. This would either
# be the next param or the beginning hex value.
for i in range(len(bs_list_rev)-1):
    if bs_list_rev[i] in params_values:
        value_str = ''
        j = i + 1
        while j < len(bs_list_rev) and bs_list_rev[j].isdigit():
            value_str = bs_list_rev[j] + value_str
            j += 1

        position = params_values.index(bs_list_rev[i])

        key = params_keys[position]
        values[key] = value_str

# now format to the correct decimal place, or perform other formatting
for key,value in list(values.items()):
    if not value.isdigit():
        del values[key]

    val_int = int(value)
    if key == "voltage":
        values[key] = val_int / 100
    elif key == "current":
        values[key] = val_int / 100
    elif key == "dir_of_current":
        if value == "01":
            self.charging = True
        else:
            self.charging = False
    elif key == "ah_remaining":
        values[key] = val_int / 1000
    elif key == "mins_remaining":
        values[key] = val_int
    elif key == "power":
        values[key] = val_int / 100
    elif key == "temp":
        values[key] = val_int - 100

# Display current as negative numbers if discharging
if self.charging == False:
    if "current" in values:
        values["current"] *= -1
    if "power" in values:
        values["power"] *= -1

# Calculate percentage
if isinstance(battery_capacity_ah, int) and "ah_remaining" in values:
    values["soc"] = values["ah_remaining"] / battery_capacity_ah * 100

# Append max capacity
values["max_capacity"] = battery_capacity_ah

# Now it should be formatted corrected, in a dictionary
print(values)
```

## Logging and Visualization

For this particular project, I wanted to visualize and log the data using grafana and prometheus:
[Check out my solar-bt-battery-monitor project here](https://github.com/chriskomus/solar-battery-bt-monitor).

I also wrote a plugin for [Olen's solar-monitor](https://github.com/Olen/solar-monitor).

## Appendix A -Examining the Bytes and Logging - via nRF Connect

An alternative to using trial and error to find which Characterist UUID contains the useful information:

1. Install nRF Connect on iOS or Android. Open it up and connect to the Junctek device. It should be something like `BTG004`.
2. Under the Client tab scroll through the Attribute Table section and hit the down arrow button on everything to start pulling values from the device. Subscribe to values with the down arrow with the line under it. This will start pulling a continuous stream of information.
3. Open up a blank txt file and take notes of the values that appear on the Junctek device screen. Write down the time along with the volts, amps, Ah, SoC (state of charge), power, and time left:
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
4. Let it run for a minute or two and note any changes. Getting a few different values per parameter would be ideal. Add loads, turn things off, that sort of thing. Note it all.
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
11. Make a note of the `Updated Value of Characteristic xxxx to 0xBBxxxxxxx` block. In this case it always updates `FFE1`. This will be used in the next section.

# Credits

Uses [gatt-python](https://github.com/getsenic/gatt-python)

Shout-outs to [Olen's solar-monitor project](https://github.com/Olen/solar-monitor) for some of the code in `ble_sniffer.py` that helps with discovery and reconnecting devices.