# BLE Sniffer Walkthrough for Junctek BT BAttery Monitor

In order to get data off the Junctek via the BT I had to reverse engineer the data that was being sent over Bluetooth.

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

# Run ble_sniffer.py

1. Scan for bluetooth devices.
```
sudo bluetoothctl
scan on
```
2. A bunch of devices should start displaying. Look for one with the name like `BTGXXX`. Copy the mac address for the next step.
3. Open `ble_sniffer.py` in a text editor and make sure that `NOTIFY_CHAR_UUID = ""` and set `MAC_ADDRESS` to the value found in step 2.
2. Run the script and connect to the device:
```
python3 ble_sniffer.py
```
5. There should be some results that look like this:
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
6. In the previous section it was discovered that all values were written to FFE1, as they all looked something like this:
```
Updated Value of Characteristic FFE1 to 0xBB148815D5115232F369EE.
```
7. From that we can assume that the NOTIFY_SERVICE_UUID is `0000ffe1-0000-1000-8000-00805f9b34fb` based on the data returned in step 5:
```
[38:3b:26:79:df:37]    Characteristic [0000ffe1-0000-1000-8000-00805f9b34fb]
```
8. Set `NOTIFY_SERVICE_UUID` to the UUID in the python script. Run the script again and there should be results like this:
```
Got packet of len: 18 bb275481d5025674d20249d4230337f389ee
Got packet of len: 18 bb275482d5025675d20251d4230338f300ee
Got packet of len: 18 bb275483d5025676d20252d4230339f304ee
Got packet of len: 18 bb275484d5025677d20253d4230340f314ee
Got packet of len: 18 bb275485d5025678d20254d4230341f318ee
Got packet of len: 10 bb025679d20256d406ee
Got packet of len: 11 bb275486d5230342f304ee
```
9. Follow the same process as the last section and take notes of the values on the battery monitor, then CTRL+C to stop the script, and look for those values again.