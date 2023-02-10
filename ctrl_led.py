import SX1509
import Control
import time

TPR_pin = 10
Heater_pin = 11
Stirrer_pin = 12
Lift_pin = 13
Lift2_pin = 14

addr = 0x3e
sx = SX1509.SX1509(addr)
ctl = Control.Control(sx)

count = 0

while True:
	
	count += 1
	count %= 2
	ctl.DOUT(TPR_pin, count)
	ctl.DOUT(Heater_pin, count)
	ctl.DOUT(Stirrer_pin, count)
	ctl.DOUT(Lift_pin, count)
	ctl.DOUT(Lift2_pin, count)
	print(count)
	time.sleep(1)
