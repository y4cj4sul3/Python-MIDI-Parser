import sys
import time
import rtmidi
import threading

class EventObject:
	def __init__(self, name, delta_time, code):
		'''
			name: track name
			delta_time: delta time against previous event (tick)
			code: event code
		'''
		self.name = name
		self.delta_time = delta_time
		self.code = code

class TrackObject:
	def __init__(self):
		self.name = ''
		self.instrument = ''
		self.events = []
		
	def push_event(self, event):
		self.events.append(event)
		
	def play(self, midiout, sec_per_tick):
		for event in self.events:
			# delta time
			time.sleep(event.delta_time * sec_per_tick)
			# send event message
			midiout.send_message(event.code)

class MIDIObject:
	def __init__(self, filename):
	
		self.filename = filename
		
		# open file
		self.file = open(self.filename, 'rb')
		print('parsing file: {}'.format(self.filename))
		
		# header chunk
		self._parseHeaderChunk()
		
		# track chunk
		self.tracks = []
		for _ in range(self.num_tracks):
			self.tracks.append(self._parseTrackChunk())
		
		self.file.close
		self.file = ''
	
	def _readFile(self, byte_count):
	
		# check chunk length
		if self.chunk_length < byte_count:
			print('[Error] wrong chunk length')
			exit(1)
		self.chunk_length -= byte_count
		
		# read file
		data = self.file.read(byte_count)
		return data
	
	def _readVariableLength(self):
	
		_byte = ord(self._readFile(1))
		data = '{0:07b}'.format(_byte & 0x7F)
		while _byte > 0x7F:
			# read next byte	
			_byte = ord(self._readFile(1))
			# concate rest 7 bits
			data = data + '{0:07b}'.format(_byte & 0x7F)
		data = int(data, 2)
		return data
		
	def _parseHeaderChunk(self):
		'''
			header chunk
			
			file_format:	MIDI file format (0, 1, 2)
			num_tracks:		number of tracks
			timing_type:	'MIDI clock' or 'MTC'
			PPQN:			pulse per quarter-note
			FPS: 			frame per sec
			TPF: 			tick per frame
		'''
		# chunk type: MThd
		chunk_type = self.file.read(4).decode('ascii')
		if chunk_type != 'MThd':
			# check file type
			print('[Error] This is not MIDI file!')
			exit(1)

		# chunk length: 6 bytes
		chunk_length = int.from_bytes(self.file.read(4), byteorder='big')
		if chunk_length != 6:
			# SMF header chunk always be 6 byte length
			print('[Warning] general MIDI file header chunck length is suppose to be 6 bytes')

		# chunk data
		# format: MIDI file format (0, 1, 2)
		self.file_format = int.from_bytes(self.file.read(2), byteorder='big')
		print('Type-{} MIDI'.format(self.file_format))
		# tracks: number of tracks
		self.num_tracks = int.from_bytes(self.file.read(2), byteorder='big')
		print('{} tracks'.format(self.num_tracks))
		# division: default unit of delta-time
		_byte = self.file.read(1)
		if ord(_byte) < 8:
			self.timing_type = 'MIDI clock'
			self.PPQN = int.from_bytes(_byte + self.file.read(1), byteorder='big')
			print('division: {}, ticks per quarter-note: {}'.format(self.timing_type, self.PPQN))
		else:
			self.timing_type = 'MTC'
			self.FPS = -int.from_bytes(_byte, byteorder='big', signed=True)
			self.TPF = int.from_bytes(self.file.read(1), byteorder='big')
			print('division: {}, ticks per frame: {}, frames per sce: {}'.format(self.timing_type, self.FPS, self.TPF))
	
	def _parseTrackChunk(self):
		trackObj = TrackObject()
		print('===================')
		# chunk type: MTrk
		chunk_type = self.file.read(4).decode('ascii')
		ignoreChunk = False
		if chunk_type != 'MTrk':
			# ignore unknow chunk
			ignoreChunk = True
			print('ignore unknow chunk: {}'.format(chunk_type))

		# chunk length
		self.chunk_length = int.from_bytes(self.file.read(4), byteorder='big')

		# ignore unknown chunk
		if ignoreChunk:
			self.file.read(self.chunk_length)
			return track
			
		# chunk data
		# events
		while self.chunk_length > 0:
			# delta time
			delta_time = self._readVariableLength()
			print('delta time: {} ticks'.format(delta_time))
			
			# check running status
			_next_byte = ord(self.file.peek(1)[:1])
			if _next_byte < 0x80:
				# Running Status
				event_type = running_status
				print('Running Status')
			else:
				# event type
				event_type = ord(self._readFile(1))
				
			if event_type > 0x7F and event_type < 0xF0:
				# MIDI event
				# record running status
				running_status = event_type
				# event status
				event_status = (event_type & 0xF0) >> 4
				print('MIDI event: {:04b}'.format(event_status))
				# event channel
				event_channel = event_type & 0x0F
				#print('channel: {}'.format(event_channel))
				if event_status == 0x8:
					# Note Off
					event_name = 'Note Off'
					# key number
					key_num = ord(self._readFile(1))
					if key_num > 0x7F:
						print('[Error] {} key number should less than 128'.format(event_name))
						exit(1)
					# velocity
					velocity = ord(self._readFile(1))
					if velocity > 0x7F:
						print('[Error] {} velocity should less than 128'.format(event_name))
						exit(1)
					print('{}: channel: {}, key: {}'.format(event_name, event_channel, key_num))
					# add event
					event_code = [event_type, key_num, velocity]
					trackObj.push_event(EventObject(event_name, delta_time, event_code))
				
				elif event_status == 0x9:
					# Note On
					event_name = 'Note On'
					# key number
					key_num = ord(self._readFile(1))
					if key_num > 0x7F:
						print('[Error] {} key number should less than 128'.format(event_name))
						exit(1)
					# velocity
					velocity = ord(self._readFile(1))
					if velocity > 0x7F:
						print('[Error] {} velocity should less than 128'.format(event_name))
						exit(1)
					print('{}: channel: {}, key: {}, velocity: {}'.format(event_name, event_channel, key_num, velocity))
					# add event
					event_code = [event_type, key_num, velocity]
					trackObj.push_event(EventObject(event_name, delta_time, event_code))
				
				elif event_status == 0xA:
					# Note Aftertouch
					event_name = 'Note Aftertouch'
					# key number
					key_num = ord(self._readFile(1))
					if key_num > 0x7F:
						print('[Error] {} key number should less than 128'.format(event_name))
						exit(1)
					# pressure
					pressure = ord(self._readFile(1))
					if pressure > 0x7F:
						print('[Error] {} pressure should less than 128'.format(event_name))
						exit(1)
					print('{}: channel: {}, key: {}, pressure: {}'.format(event_name, event_channel, key_num, pressure))
					# add event
					event_code = [event_type, key_num, velocity]
					trackObj.push_event(EventObject(event_name, delta_time, event_code))
				
				elif event_status == 0xB:
					# Control Change
					# TODO: Channel Mode Messages
					event_name = 'Control Change'
					# controller number
					controller_num = ord(self._readFile(1))
					if controller_num > 0x7F:
						print('[Error] {} controller number should less than 128'.format(event_name))
						exit(1)
					# event value
					event_value = ord(self._readFile(1))
					if event_value > 0x7F:
						print('[Error] {} event value should less than 128'.format(event_name))
						exit(1)
					print('{}: channel: {}, controller: {}, value: {}'.format(event_name, event_channel, controller_num, event_value))
					# add event
					event_code = [event_type, controller_num, event_value]
					trackObj.push_event(EventObject(event_name, delta_time, event_code))
					
				elif event_status == 0xC:
					# Program Change
					event_name = 'Program Change'
					# program number
					program_num = ord(self._readFile(1))
					if program_num > 0x7F:
						print('[Error] {} program_num should less than 128'.format(event_name))
						exit(1)
					print('{}: program: {}'.format(event_name, program_num))
					# add event
					event_code = [event_type, program_num]
					trackObj.push_event(EventObject(event_name, delta_time, event_code))
				
			elif event_type == 0xF0:
				# System Exclusive
				event_name = 'System Exclusive'
				# event length
				event_length = self._readVariableLength()
				# event data
				event_data = self._readFile(event_length)
				
				print(event_data)
				# TODO: check last byte
				
			elif event_type == 0xF7:
				# End of Exclusive
				event_name = 'End of Exclusive'
				# event length
				event_length = self._readVariableLength()
				# event data
				event_data = self._readFile(event_length)
				
				print(event_data)
				# TODO: check last byte
				
			elif event_type == 0xFF:
				# Reset (meta event)
				# meta event type
				meta_event_type = ord(self._readFile(1))
				
				print('meta event: {:02x}'.format(meta_event_type))
				if meta_event_type == 0x00:
					# Sequence Number
					event_name = 'Sequence Number'
					# TODO: should before delta-time
					# event length: 2
					event_length = ord(self._readFile(1))
					
					if event_length != 2:
						print('[Error] {} event should have length of 2 byte'.format(event_name))
						exit(1)
						
				elif meta_event_type == 0x01:
					# Text Event
					event_name = 'Text Event'
					# event length
					event_length = self._readVariableLength()
					# event text
					event_text = self._readFile(event_length).decode('ascii')
					
					print('{}: {}'.format(event_name, event_text))
					
				elif meta_event_type == 0x02:
					# Copyright Notice
					event_name = 'Copyright Notice'
					# event length
					event_length = self._readVariableLength()
					# event text
					self.copyright = self._readFile(event_length).decode('ascii')
					print('{}: {}'.format(event_name, self.copyright))
					
					
				elif meta_event_type == 0x03:
					# Sequence/Track Name
					event_name = 'Sequence/Track Name'
					# event length
					event_length = self._readVariableLength()
					# event text
					trackObj.name = self._readFile(event_length).decode('ascii')
					print('{}: {}'.format(event_name, trackObj.name))
				
				elif meta_event_type == 0x04:
					# Instrument Name
					event_name = 'Instrument Name'
					# event length
					event_length = self._readVariableLength()
					# event text
					trackObj.instrument = self._readFile(event_length).decode('ascii')
					print('{}: {}'.format(event_name, trackObj.instrument))
				
				elif meta_event_type == 0x05:
					# Lyrics
					event_name = 'Lyrics'
					# event length
					event_length = self._readVariableLength()
					# event text
					event_text = self._readFile(event_length).decode('ascii')
					
					print('{}: {}'.format(event_name, event_text))
				
				elif meta_event_type == 0x06:
					# Marker
					event_name = 'Marker'
					# event length
					event_length = self._readVariableLength()
					# event text
					event_text = self._readFile(event_length).decode('ascii')
					print('{}: {}'.format(event_name, event_text))
					
				elif meta_event_type == 0x07:
					# Cue Point
					event_name = 'Cue Point'
					# event length
					event_length = self._readVariableLength()
					# event text
					event_text = self._readFile(event_length).decode('ascii')
					print('{}: {}'.format(event_name, event_text))

				elif meta_event_type == 0x20:
					# MIDI Channel Prefix
					event_name = 'MIDI Channel Prefix'
					# TODO: 
					# event length: 1
					event_length = ord(self._readFile(1))
					if event_length != 1:
						print('[Error] {} event should have length of 1 byte'.format(event_name))
						exit(1)
					# event channel
					event_channel = ord(self._readFile(event_length))
					print('{}: channel-{}'.format(event_name, event_channel))
				
				elif meta_event_type == 0x2F:
					# End Of Track
					event_name = 'End Of Track'
					# event length: 0
					event_length = ord(self._readFile(1))
					if event_length != 0:
						print('[Error] {} event should have length of 0 byte'.format(event_name))
						exit(1)
					if self.chunk_length != 0:
						print('[Error] wrong chunk length')
						exit(1)
					print(event_name)
					
				elif meta_event_type == 0x51:
					# Set Tempo
					event_name = 'Set Tempo'
					# event length: 3
					event_length = ord(self._readFile(1))
					if event_length != 3:
						print('[Error] {} event should have length of 3 byte'.format(event_name))
						exit(1)
					# microsecond per quarter note
					self.MSPQN = int.from_bytes(self._readFile(event_length), byteorder='big')
					# BPM = 60*10^6/(ms/qn)
					self.BPM = 60000000 / self.MSPQN
					# seconds per tick
					if self.timing_type == 'MIDI clock':
						self.sec_per_tick = self.MSPQN / (1000000 * self.PPQN)
						print('{}: {} seconds per tick'.format(event_name, self.sec_per_tick))
					print('{}: {} ms/quarter-note = {} BPM'.format(event_name, self.MSPQN, self.BPM))
					
				elif meta_event_type == 0x54:
					# SMPTE Offset
					event_name = 'SMPTE Offset'
					# event length: 5
					event_length = ord(self._readFile(1))
					if event_length != 5:
						print('[Error] {} event should have length of 5 byte'.format(event_name))
						exit(1)
					# TODO:
					event_data = self._readFile(event_length)
				
				elif meta_event_type == 0x58:
					# Time Signature
					event_name = 'Time Signature'
					# event length: 4
					event_length = ord(self._readFile(1))
					if event_length != 4:
						print('[Error] {} event should have length of 4 byte'.format(event_name))
						exit(1)
					# TODO:
					for _ in range(event_length):
						_byte = ord(self._readFile(1))
						print(_byte)
					
				elif meta_event_type == 0x59:
					# Key Signature
					event_name = 'Key Signature'
					# event length: 2
					event_length = ord(self._readFile(1))
					if event_length != 2:
						print('[Error] {} event should have length of 2 byte'.format(event_name))
						exit(1)
					# key (number of sharps pr flats)
					event_key = int.from_bytes(self._readFile(1), byteorder='big', signed=True)
					print('{}: key: {}'.format(event_name, event_key))
					# scale (major or minor)
					event_scale = ord(self._readFile(1))
					print('{}: scale: {}'.format(event_name, event_scale))
					
				elif meta_event_type == 0x7F:
					# Sequence Specific
					event_name = 'Sequence Specific'
					# event length
					event_length = self._readVariableLength()
					# event data
					event_data = self._readFile(event_length)
					print('{}: {}'.format(event_name, event_data))
		
		return trackObj
	
	def play(self):
		
		midiout = rtmidi.MidiOut()
		available_ports = midiout.get_ports()
		midiout.open_port(0)
		
		# create threads
		threads = []
		for i in range(self.num_tracks):
			threads.append(threading.Thread(target = self.tracks[i].play, args = (midiout, self.sec_per_tick, )))
			threads[i].start()
		
		# wait for all thread
		for i in range(self.num_tracks):
			threads[i].join()
		
		del midiout
		
	
'''
	open file
'''
if len(sys.argv) > 1:
	filename = sys.argv[1]
else:
	filename = 'examples/Craft_-_Windows_Startup_midi.mid'
	
midiobj = MIDIObject(filename)
midiobj.play()
