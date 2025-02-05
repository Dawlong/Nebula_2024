from machine import I2C
import time
import struct

class SCD4x:
    def __init__(self, i2c, address=0x62):
        self.i2c = i2c
        self.address = address

    def _write_command(self, command):
        try:
            self.i2c.writeto(self.address, command)
            time.sleep_ms(20)  # Increased delay for sensor processing
        except OSError as e:
            print(f"I2C write error: {e}")

    def _read_data(self, command, length):
        try:
            self.i2c.writeto(self.address, command)
            time.sleep_ms(20)  # Increased delay for sensor processing
            return self.i2c.readfrom(self.address, length)
        except OSError as e:
            print(f"I2C read error: {e}")
            return None

    def start_periodic_measurement(self):
        self._write_command(b'\x21\xb1')

    def stop_periodic_measurement(self):
        self._write_command(b'\x3f\x86')

    def measure_single_shot(self):
        self._write_command(b'\x21\x9D')  # Single shot command for full measurement
        time.sleep(5)  # Wait for measurement to complete

    def measure_single_shot_rht_only(self):
        self._write_command(b'\x21\x96')  # Single shot command for RH and T only
        time.sleep(0.05)  # Wait for measurement to complete

    def read_measurement(self):
        data = self._read_data(b'\xec\x05', 9)
        if data:
            co2 = struct.unpack('>H', data[0:2])[0]
            temperature = -45 + 175 * struct.unpack('>H', data[3:5])[0] / 65536.0
            humidity = 100 * struct.unpack('>H', data[6:8])[0] / 65536.0
            return co2, temperature, humidity
        else:
            return None, None, None

    def get_serial_number(self):
        data = self._read_data(b'\x36\x82', 9)
        if data:
            serial_number = struct.unpack('>HHH', data)
            return serial_number
        else:
            return None

    def soft_reset(self):
        self._write_command(b'\x36\x32')
        time.sleep(0.5)  # Increased delay for reset

    def perform_self_test(self):
        self._write_command(b'\x36\x39')
        time.sleep(10)  # Self-test takes 10 seconds
        data = self._read_data(b'\xE4\xB8', 3)
        if data:
            return struct.unpack('>H', data[:2])[0] == 0
        else:
            return False

    def set_temperature_offset(self, offset):
        value = int(offset * 65536 / 175 + 45 * 65536 / 175)
        self._write_command(b'\x24\x1d' + struct.pack('>H', value))

    def get_temperature_offset(self):
        data = self._read_data(b'\x23\x18', 3)
        if data:
            offset = struct.unpack('>H', data[:2])[0]
            return -45 + 175 * offset / 65536.0
        else:
            return None

    def set_altitude(self, altitude):
        self._write_command(b'\x24\x27' + struct.pack('>H', altitude))

    def get_altitude(self):
        data = self._read_data(b'\x23\x22', 3)
        if data:
            return struct.unpack('>H', data[:2])[0]
        else:
            return None

    def perform_forced_calibration(self, target_co2):
        self._write_command(b'\x36\x2f' + struct.pack('>H', target_co2))
        time.sleep(0.5)
        data = self._read_data(b'\xE4\xB8', 3)
        if data:
            return struct.unpack('>H', data[:2])[0]
        else:
            return None

    def set_automatic_self_calibration(self, enable):
        self._write_command(b'\x24\x16' + struct.pack('>H', int(enable)))

    def get_automatic_self_calibration(self):
        data = self._read_data(b'\x23\x13', 3)
        if data:
            return struct.unpack('>H', data[:2])[0] == 1
        else:
            return None
