from SHT31 import SHT31
import time
sht31 = SHT31()

while True:
        sht31.write_command()
        time.sleep(0.3)
        result = sht31.read_data()
        print ("Relative Humidity : %.2f %%"%(result['h']))
        print ("Temperature in Celsius : %.2f C"%(result['c']))
        print ("Temperature in Fahrenheit : %.2f F"%(result['f']))
        print (" ************************************* ")
        time.sleep(1)