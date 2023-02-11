# puleunAIR

## 1. Set I2C
```
$ sudo nano /boot/config.txt

# Add i2c port & bus at last line
dtoverlay=i2c-gpio,i2c_gpio_sda=17,i2c_gpio_scl=19,bus=2 #SX1509 Port
```

## 2. Install requirements

### MQTT-broker
```
$ wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key
$ sudo apt-key add mosquitto-repo.gpg.key
$ cd /etc/apt/sources.list.d/
$ sudo wget http://repo.mosquitto.org/debian/mosquitto-buster.list 
$ sudo apt-get update
$ sudo apt-get install mosquitto
```
### Python Library
#### mqtt
```shell
$ pip3 install paho-mqtt
```
#### DHT11
```shell
$ pip3 install adafruit-blinka
$ pip3 install adafruit-circuitypython-dht
```
- edit DHT library file in dist-package
```shell
$ sudo nano /usr/local/lib/python3.7/dist-packages/Adafruit_DHT/platform_detect.py
```
- Add code in line 111
```shell
elif match.group(1) == 'BCM2711':
    return 3
```
  
## 3. Install dependencies
```shell
$ curl -sL https://deb.nodesource.com/setup_16.x | sudo -E bash -

$ sudo apt-get install -y nodejs

$ node -v

$ sudo npm install -g pm2

$ git clone https://github.com/IoTKETI/puleunAIR.git

$ cd /home/pi/puleunAIR

$ npm install
```