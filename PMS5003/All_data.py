import time
from pms5003 import PMS5003

print("""pms5003_test.py - Continously print all data values.
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
    print(data)
    time.sleep(1.0)