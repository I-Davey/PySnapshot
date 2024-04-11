import asyncio
from bleak import BleakScanner, BleakClient
import enum
from uuid import UUID
import struct
import time
import colorspacious

import tkinter as tk

import threading


class Command(enum.Enum):
    CMD_POWER_OFF = (0, 0)
    CMD_RESET = (1, 0)
    CMD_PING = (2, 0)
    CMD_SET_CALIBRATION = (3, 5)
    CMD_GET_CALIBRATION = (4, 5)
    CMD_GET_CALIBRATION_TEMPERATURE = (5, 5)
    CMD_DO_CALIBRATION = (7, 1)
    CMD_GET_STORAGE_CAPACITY = (32, 1)
    CMD_GET_NUMBER_STORED_SAMPLES = (33, 1)
    CMD_GET_STORED_SAMPLE_N = (34, 13)
    CMD_CLEAR_ALL_STORED_SAMPLES = (35, 0)
    CMD_GET_DATA_COLOUR = (64, 12)
    CMD_GET_DATA_TEMPERATURE = (65, 4)
    CMD_GET_DATA_LIGHT_C = (66, 2)
    CMD_GET_DATA_LIGHT_R = (67, 2)
    CMD_GET_DATA_LIGHT_G = (68, 2)
    CMD_GET_DATA_LIGHT_B = (69, 2)
    CMD_GET_DATA_BRIGHTNESS = (70, 4)
    CMD_GET_DATA_LIGHT_CRGB = (71, 8)
    CMD_GET_DATA_RED = (72, 8)
    CMD_GET_DATA_GREEN = (73, 8)
    CMD_GET_DATA_BLUE = (74, 8)
    CMD_SET_IDLE_TIMER = (80, 2)
    CMD_GET_IDLE_TIMER = (81, 2)
    CMD_SET_CALIBRATION_STATUS = (88, 1)
    CMD_GET_CALIBRATION_STATUS = (89, 1)

    def __init__(self, command_id, response_size):
        self.command_id = command_id
        self.response_size = response_size
    
    @classmethod
    def from_id(cls, command_id):
        for command in cls:
            if command.value[0] == command_id:
                return command
        return None

class InvalidHeaderException(Exception):
    pass

class DeviceResponseParser:
    def parse(self, byte_array):
        if byte_array[0] != 126:  # Validate header byte
            raise InvalidHeaderException(f"Invalid header byte: {byte_array[0]}")

        command_id = byte_array[2]
        command = Command.from_id(command_id)
        if command is None:
            raise ValueError("Unknown command ID")

        error_code = byte_array[3]
        is_response_packet = bool(byte_array[1] & 32)
        payload = byte_array[4:]

        if error_code != 0:
            print(f"Response error: 0x{error_code:X}")
            return None

        if is_response_packet:
            print(f"Received response for command ID: {command_id}")
            # Parse payload based on command
            return self.parse_payload(command, payload), byte_array
        else:
            print(f"Received notification for command ID: {command_id}")
            return None
        
        

    def parse_payload(self, command, payload):
        # Simplify payload parsing logic by focusing on one command as an example
        if command == Command.CMD_GET_DATA_COLOUR:
            #multiply the colors by 10
            color1, color2, color3 = struct.unpack('!fff', payload)

            #convert the color to #hex so it can be displayed
            rgb_color = colorspacious.cspace_convert([color1, color2, color3], "CIELab", "sRGB1")
            print(f"Color: {rgb_color}")
            rgb_color = [int(x * 255) for x in rgb_color]
            rgb_color_hex = f"#{rgb_color[0]:02X}{rgb_color[1]:02X}{rgb_color[2]:02X}"

            #raw bytes as in 01010101etc
            #unpack requires a buffer, so calculate the buffer size
            #unpack returns a tuple of the unpacked values

            buffer_size = len(payload)
            return rgb_color_hex
        
        return None

async def discover_snapshot_device() -> str:
    for _ in range(10):
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name and "Snapshot" in device.name:
                print(f"Found Snapshot device: {device.name}, {device.address}")
                return device.address
        await asyncio.sleep(1)
    return None

class SnapshotConnection:
    def __init__(self, client: BleakClient):
        self.client = client
        self.parser = DeviceResponseParser()
        self.popup = None
        self.parsed_data = []
        self.is_connected = False

    @classmethod
    async def create(cls):
        address = await discover_snapshot_device()
        if address is None:
            print("Snapshot device not found.")
            return None
        client = BleakClient(address)
        await client.connect()
        print(f"Connected to {address}")
        return cls(client)

    async def disconnect(self):
        await self.client.disconnect()
        print("Disconnected.")

    async def read_battery_level(self) -> str:
        battery_level_uuid = "00002a19-0000-1000-8000-00805f9b34fb"
        battery_level = await self.client.read_gatt_char(battery_level_uuid)
        return f"{int(battery_level[0])}%"

    async def subscribe_to_notifications(self):
        a = "9B2B0001-FDDE-11E2-B778-0800200C9A66"
        b = "9B2B0002-FDDE-11E2-B778-0800200C9A66"
        char_uuid = "9B2B0003-FDDE-11E2-B778-0800200C9A66"

        await self.client.start_notify(char_uuid, self.notification_handler)
        print(f"Subscribed to {char_uuid}. Waiting for notifications...")

    async def notification_handler(self, sender, data):
        data = self.parser.parse(data)
        print(f"Received data: {data}")
        self.parsed_data.append(data)






async def mainBluetoothCode(dev=False):
    snapshot = await SnapshotConnection.create()
    if snapshot:
        snapshot.is_connected = True
        print("Battery level:", await snapshot.read_battery_level())

        if dev:
            await testfunc(snapshot)    

        await snapshot.subscribe_to_notifications()

        

        await asyncio.sleep(60)  # Keep listening for 60 seconds or adjust as necessary
        await snapshot.disconnect()





def start_asyncio_loop(asyncio_loop):
    asyncio.set_event_loop(asyncio_loop)
    asyncio_loop.run_forever()




