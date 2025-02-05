import time
from pms5003 import PMS5003
import machine

print("""pms5003_test.py - Continuously print PM1.0, PM2.5, and PM10 values.
""")

# Configure the PMS5003 for Enviro+
pms5003 = PMS5003(
    uart=machine.UART(0, tx=machine.Pin(12), rx=machine.Pin(13), baudrate=9600),
    pin_enable=machine.Pin(3),
    pin_reset=machine.Pin(2),
    mode="active"
)

while True:
    data = pms5003.read()
    print(f"PM1.0: {data.pm_ug_per_m3(1)}, PM2.5: {data.pm_ug_per_m3(2.5)}, PM10: {data.pm_ug_per_m3(10)}")
    time.sleep(1.0)
