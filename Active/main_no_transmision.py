from machine import SPI, I2C, Pin, ADC
from pms5003 import PMS5003
from bme280 import BME280, BMP280_I2CADDR
from scd4x_micro import SCD4x
import time

# Initialise the PMS5003 for Enviro+
pms5003 = PMS5003(
    uart=machine.UART(0, tx=machine.Pin(12), rx=machine.Pin(13), baudrate=9600),
    pin_enable=machine.Pin(19),
    pin_reset=machine.Pin(18),
    mode="active"
)

# Initialize I2C for both sensors
i2c_bme280 = I2C(0, scl=Pin(9), sda=Pin(8))  # Initialize the I2C bus on GP9 and GP8
i2c_scd41 = I2C(1, scl=Pin(15), sda=Pin(14), freq=100000)  # Adjust pins and I2C ID as needed

# Initialize the BMP280 sensor
bmp = BME280(i2c=i2c_bme280, address=BMP280_I2CADDR)

# Initialize the SCD41 sensor
sensor = SCD4x(i2c_scd41)

# Perform initial setup for SCD41
try:
    # Initialize sensor
    sensor.initialize_sensor()
    
    # Start periodic measurement for SCD41
    sensor.start_periodic_measurement()
    
    # Print header
    print(";iteration_count;time_sec;pressure_hpa;bmp280_temp;PM1.0;PM2.5;PM10;CO2_ppm;SCD41_temp;Humidity")
    
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
        msg = f"{counter};{elapsed_time:.2f};{pressure:.2f};hPa;{bmp_temp:.2f};°C;"
        msg += f"{data.pm_ug_per_m3(1)};ug/m3;{data.pm_ug_per_m3(2.5):.2f};ug/m3;{data.pm_ug_per_m3(10):.2f};ug/m3"
        
        # Append SCD41 data if it is available
        if co2 is not None and scd41_temp is not None and humidity is not None:
            msg += f";{co2};ppm;{scd41_temp:.2f};°C;{humidity:.2f};%"
               
        counter += 1  # Increment counter
        time.sleep(0.5)  # Wait before next reading
        
        print(msg)
finally:
    # Ensure the sensor is set to IDLE mode when done
    sensor.stop_periodic_measurement()