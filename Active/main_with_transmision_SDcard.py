from machine import SPI, I2C, Pin, ADC
from pms5003 import PMS5003
from rfm69 import RFM69
from bme280 import BME280, BMP280_I2CADDR
from scd4x_micro import SCD4x
import time
import sdcard
import os
import uos

#RFM69
#initialise data transmision
NAME           = "Python"
FREQ           = 435.1

ENCRYPTION_KEY = b"\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08"
NODE_ID        = 120 # ID of this node
BASESTATION_ID = 100 # ID of the node (base station) to be contacted

# Buses & Pins
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=50000, polarity=0, phase=0, firstbit=SPI.MSB)
nss = Pin(5, Pin.OUT, value=True)
rst = Pin(3, Pin.OUT, value=False)
i2c = I2C(0, scl=Pin(9), sda=Pin(8)) # initialize the i2c bus on GP9 and GP8

# RFM Module
rfm = RFM69(spi=spi, nss=nss, reset=rst)
rfm.tx_power = 15 # 13 dBm = 20mW (default value, safer for all modules) ; 20 # 20 dBm = 100mW
rfm.frequency_mhz  = FREQ
rfm.encryption_key = (ENCRYPTION_KEY)
rfm.node           = NODE_ID # This instance is the node 120
rfm.destination    = BASESTATION_ID # Send to specific node 100

led = Pin(25, Pin.OUT) # Onboard LED

# Initialize SPI1 for SD Card
spi_sd = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
cs_sd = Pin(13, Pin.OUT, value=True)

# Mount SD Card
try:
    sd = sdcard.SDCard(spi_sd, cs_sd)  # Initialize SD card
    vfs = uos.VfsFat(sd)  # Mount filesystem
    uos.mount(vfs, "/sd")  # Mount at /sd
    print("SD Card mounted successfully!")
except Exception as e:
    print("Failed to mount SD Card:", e)
    sd = None
    
# Generate a unique filename based on time
timestamp = int(time.time()) if time.time() > 0 else "000000"
filename = f"/sd/log_{timestamp}.csv"

# Write CSV header if file is new
def file_exists(filepath):
    try:
        with open(filepath, "r"):
            return True
    except OSError:
        return False

if sd and not file_exists(filename):
    with open(filename, "w") as f:
        f.write("count;time_sec;pressure_hpa;bmp280_temp;PM1.0_ug/m3;PM2.5_ug/m3;PM10_ug/m3;CO2_ppm;SCD41_temp;Humidity_%\n")


# Initialise the PMS5003 for Enviro+
pms5003 = PMS5003(
    uart=machine.UART(0, tx=machine.Pin(16), rx=machine.Pin(17), baudrate=9600),
    pin_enable=machine.Pin(19),
    pin_reset=machine.Pin(18),
    mode="active"
)

# Initialize I2C0 for BME280
i2c_bme280 = I2C(0, scl=Pin(9), sda=Pin(8))  # Initialize the I2C bus on GP9 and GP8
bmp = BME280(i2c=i2c_bme280, address=BMP280_I2CADDR)

#Initialize I2C1 for SCD41
i2c_scd41 = I2C(1, scl=Pin(15), sda=Pin(14), freq=100000)  # Adjust pins and I2C ID as needed
sensor = SCD4x(i2c_scd41)


# Perform initial setup
try:
    # Initialize sensor SCD41
    sensor.initialize_sensor()
    
    # Start periodic measurement for SCD41
    sensor.start_periodic_measurement()
    
    #print relevant transmition data
    print( 'Frequency     :', rfm.frequency_mhz )
    print( 'encryption    :', rfm.encryption_key )
    print( 'NODE_ID       :', NODE_ID )
    print( 'BASESTATION_ID:', BASESTATION_ID )

    
    # Print header
    print("count;time_sec;pressure_hpa;bmp280_temp;PM1.0_ug/m3;PM2.5_ug/m3;PM10_ug/m3;CO2_ppm;SCD41_temp;Humidity_%")
    
    # Record the start time
    ctime = time.time()
    counter = 1

    while True:
        # Get the current time and calculate elapsed time
        elapsed_time = time.time() - ctime
                
        # Read measurement data from BMP280 every 0.5 seconds
        bmp_temp, pressure, _ = bmp.raw_values
        
        # Read measurement data from SCD41 whenever it is ready
        co2, scd41_temp, humidity = sensor.read_measurement()
        
        # Read measurement data from the PMS5003
        data = pms5003.read()
                
        # Prepare the output message
        msg = f"{counter};{elapsed_time:.2f};{pressure:.2f};{bmp_temp:.2f};"
        msg += f"{data.pm_ug_per_m3(1)};{data.pm_ug_per_m3(2.5)};{data.pm_ug_per_m3(10)}"
        
        # Append SCD41 data if it is available
        if co2 is not None and scd41_temp is not None and humidity is not None:
            msg += f";{co2};{scd41_temp:.2f};{humidity:.2f}"
        else:
            msg += f"; ; ; "
        
        counter += 1  # Increment counter
        time.sleep(0.25)  # Wait before next reading
        
        print(msg)
        
        # Write to SD Card
        if sd:
            with open(filename, "a") as f:
                f.write(msg + "\n")
        
        #send message RFM
        led.on() # Led ON while sending data
        rfm.send(bytes(msg , "utf-8"))
        led.off()
        
finally:
    # Ensure the sensor is set to IDLE mode when done
    sensor.stop_periodic_measurement()
