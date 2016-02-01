#!/usr/bin/env python

# Light each LED in sequence, and repeat.

import opc, time

numLEDs = 64
client = opc.Client('localhost:7890')

pixels = [ (0,0,0) ] * numLEDs
client.put_pixels(pixels)