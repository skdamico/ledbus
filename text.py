#!/usr/bin/env python

# Light each  LED in sequence, and repeat.

import opc

from PIL import Image, ImageDraw, ImageFont
import math
import os
import time
from lib.predict import predict

### Config

stops = [
 # ( 'actransit', 'J', '0600260', 'To San Francisco' )
    ( 'sf-muni', '30', '3136', 'Outbound to the Marina District' )
]

max_predictions = 1   # NextBus shows up to 5; limit to 3 for simpler display
min_time        = 0   # Drop predictions below this threshold (minutes)
short_time      = 5   # Times less than this are displayed in red
mid_time        = 10  # Times less than this are displayed yellow

width          = 8  # Matrix size (pixels) -- change for different matrix
height         = 8  # types (incl. tiling).  Other code may need tweaks.
fps            = 20  # Scrolling speed (ish)

long_time_color  = (  0, 160,   0) # Ample arrival time = green
mid_time_color   = (160, 160,   0) # Medium arrival time = yellow
short_time_color = (160,   0,   0) # Short arrival time = red
mins_color      = (110, 110, 110) # Commans and 'minutes' labels
no_times_color   = (  0,   0, 255) # No predictions = blue

# TrueType fonts are a bit too much for the Pi to handle -- slow updates and
# it's hard to get them looking good at small sizes.  A small bitmap version
# of Helvetica Regular taken from X11R6 standard distribution works well:
font           = ImageFont.load(os.path.dirname(os.path.realpath(__file__))
                   + '/resources/helvR08.pil')

# Drawing takes place in offscreen buffer to prevent flicker
image       = Image.new('RGB', (width, height))
draw        = ImageDraw.Draw(image)
current_time = 0.0
prev_time    = 0.0

class Tile(object):

	x = 0
	y = 0
	label = ''
	label_size = (0, 0)
	color = (110, 0, 120) # soft white
	velocity = 6
	bounds = width * 2

	def __init__(self, label):
		self.set_label(label)

	def _get_label_size(self):
		return font.getsize(self.label)

	def set_label(self, text):
		self.label = text
		self.label_size = self._get_label_size()

	def tick(self, time_delta):
		#self.x -= (self.velocity * time_delta)

		#if math.fabs(self.x) > self.bounds:
		#	self.x = self.bounds

		self.x = math.floor((width - self.label_size[0]) * 0.5)
		self.y = math.floor((height - self.label_size[1]) * 0.5)

	def draw(self):
		draw.text((math.floor(self.x), math.floor(self.y)), 
				  self.label, 
				  font=font, 
				  fill=self.color)


class BusPredictionTile(Tile):
	predict_obj = None

	def __init__(self, label):
		super(self.__class__, self).__init__(label)
		self.predict_obj = predict(stops[0])

	def draw(self):
		if self.predict_obj.predictions == []:
			self.set_label("--")
		else:
			p_count = 0
			print ""

			predictions = sorted(self.predict_obj.predictions)
			for p in predictions:
				t = p - (current_time - self.predict_obj.lastQueryTime)
				m = int(t / 60)
				print m

			print ""
			for p in predictions:
				if p_count >= max_predictions:
					break
			
				# convert time to minutes
				t = p - (current_time - self.predict_obj.lastQueryTime)
				m = int(t / 60)
				print m

				if m <= min_time:
					continue

				# what kind of label do we need?
				label = self.get_label_for_prediction(m)
				color = self.get_color_for_prediction(m)

				self.set_label(label)
				self.color = color

				p_count += 1
		super(self.__class__, self).draw()

	def get_label_for_prediction(self, p_time):
		if p_time < 1:
			return "0"
		else:
			return str(p_time)

	def get_color_for_prediction(self, p_time):
		if p_time <= short_time: 
			return short_time_color
		elif p_time <= mid_time:
			return mid_time_color
		else:
			return long_time_color

def clear_pixels():
	return [ (0,0,0) ] * (width * height)


client = opc.Client('localhost:7890')
pixels = clear_pixels()

tiles = []
for i in range(1):
	tile = BusPredictionTile('Jam!!!!')
	tiles.append(tile)

# Initialization done; loop forever ------------------------------------------
try:
	time_delta = 0
	while True:
		# Clear background
		draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

		for t in tiles:
			t.tick(time_delta)
			t.draw()

		# Try to keep timing uniform-ish; rather than sleeping a fixed time,
		# interval since last frame is calculated, the gap time between this
		# and desired frames/sec determines sleep time...occasionally if busy
		# (e.g. polling server) there'll be no sleep at all.
		current_time = time.time()
		time_delta   = (1.0 / fps) - (current_time - prev_time)
		if(time_delta > 0.0):
			time.sleep(time_delta)
		prev_time = current_time

		# Offscreen buffer is copied to screen
		pixels = list(image.getdata())
		client.put_pixels(pixels)
		
finally:
	pixels = clear_pixels()
	client.put_pixels(pixels)
