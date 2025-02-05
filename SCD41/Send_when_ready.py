from machine import I2C, Pin
from scd4x_micro import SCD4x
import time

# Initialize I2C
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)  # Adjust pins and I2C ID as needed

# Initialize the SCD4x sensor
sensor = SCD4x(i2c)

# Perform initial setup
try:
    # Initialize sensor
    sensor.initialize_sensor()
    
    # Start periodic measurement
    sensor.start_periodic_measurement()
    
    # Record the start time using time.time()
    ctime = time.time()

    while True:
        # Get the current time and calculate elapsed time
        elapsed_time = time.time() - ctime
        
        # Read measurement data only when ready
        co2, temperature, humidity = sensor.read_measurement()
        if co2 is not None and temperature is not None and humidity is not None:
            # Print the time in seconds (float format) with other measurements
            print(f"time: {elapsed_time:.2f}s, CO2: {co2} ppm, Temp: {temperature:.2f} °C, Hum: {humidity:.2f} %")
        
        # Small sleep to avoid busy-waiting
        time.sleep(1)

finally:
    # Ensure the sensor is set to IDLE mode when done
    sensor.stop_periodic_measurement()
