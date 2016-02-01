#!/usr/bin/env python

# Light each LED in sequence, and repeat.

import opc, time

numLEDs = 64
client = opc.Client('localhost:7890')

pixels = [ (0,0,0) ] * numLEDs
loop_count = 0

while True:
	loop_count += 1
	
	for i in range(numLEDs):
		pixels[i] = (220, 0, 0) if ((i + loop_count) % 2 == 0) else (0, 220, 0)
		client.put_pixels(pixels)
		time.sleep(0.005)
