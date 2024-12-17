#import threading
from threading import *
import time
import sounddevice as sd
import numpy as np
from queue import Queue
from src.core.math_expr import *
from src.core.buffer import *

def test_buffer(indent, verbose, *kargs, **kwargs):
	# Define MultiBuffer
	multi_buffer = MultiBuffer(num_buffers=10, buffer_size=1024)  # Larger buffer pool for smooth playback

	# Register consumers
	consumer_ids = ["audio_player"]
	for cid in consumer_ids:
		multi_buffer.register_consumer(cid)

	# Define a combined signal
	signal = sine(440).scale(0.5) + sine(880).scale(0.5)

	# Create and start the producer
	producer = MathExprProducer(signal, multi_buffer)
	producer.start()

	# Define the audio playback consumer task
	def buffered_audio_player_task(multi_buffer, consumer_id, samplerate=44100, lead_chunks=3):
		"""
		Consumer task that buffers multiple chunks before starting playback and ensures smooth playback.
		"""
		try:
			underrun_count = 0
			audio_buffer = []  # Local buffer to hold chunks before playback
			while True:
				# Read data from the MultiBuffer
				chunk = multi_buffer.read(consumer_id)
				if chunk is not None:
					audio_buffer.append(chunk)
					# Start playback once we have enough chunks buffered
					if len(audio_buffer) >= lead_chunks:
						# Concatenate buffered chunks into a single array for playback
						play_chunk = np.concatenate(audio_buffer, axis=0)
						sd.play(audio_buffer, samplerate=samplerate, blocking=False)
						audio_buffer = []  # Clear the buffer after playback starts
				else:
					# Sleep briefly to wait for new data
					underrun_count += 1
					print(f"Underrun #{underrun_count} occurred")
					time.sleep(0.05)
		except KeyboardInterrupt:
			print(f"{indent}{consumer_id} stopped.")
		finally:
			sd.stop()  # Stop audio playback when task ends

	# Start the audio player consumer
	audio_player_thread = threading.Thread(target=buffered_audio_player_task, args=(multi_buffer, "audio_player"), daemon=True)
	audio_player_thread.start()

	# Run the system for a short time to test
	try:
		time.sleep(5)  # Allow playback for 10 seconds
	finally:
		producer.stop()
		print("Stopped playback.")
