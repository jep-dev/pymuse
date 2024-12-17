from collections import deque
import threading
import time
import sounddevice as sd
import numpy as np
from queue import Queue
from threading import Event

import threading

class MultiBuffer:
	def __init__(self, num_buffers, buffer_size, num_consumers):
		self.buffer_size = buffer_size
		self.num_consumers = num_consumers
		self.buffers = deque(maxlen=num_buffers)  # Ring of buffers
		self.consumer_progress = [0] * num_buffers  # Tracks how many consumers have processed each buffer
		self.consumer_positions = [0] * num_consumers  # Each consumer's read position
		self.lock = threading.Lock()  # Protect shared state
		self.not_empty = threading.Condition(self.lock)  # Notify consumers when data is available
		self.write_index = 0  # Tracks where to write next

		# Initialize with empty buffers
		for _ in range(num_buffers):
			self.buffers.append([None] * buffer_size)

	def write(self, chunk):
		with self.lock:
			# Check if the next write position is available for overwriting
			if self.consumer_progress[self.write_index] < self.num_consumers:
				raise RuntimeError("Cannot overwrite; some consumers haven't finished with this buffer.")

			# Write data to the next buffer
			self.buffers[self.write_index] = chunk
			self.consumer_progress[self.write_index] = 0  # Reset progress for this buffer

			# Advance write index
			self.write_index = (self.write_index + 1) % len(self.buffers)
			self.not_empty.notify_all()  # Notify consumers that data is available

	def read(self, consumer_id):
		with self.lock:
			consumer_pos = self.consumer_positions[consumer_id]
			while self.consumer_progress[consumer_pos] == 0:  # Wait for data to be written
				self.not_empty.wait()

			# Get the chunk for this consumer
			chunk = self.buffers[consumer_pos]

			# Mark this consumer as having processed this buffer
			self.consumer_progress[consumer_pos] += 1

			# Advance the consumer's position
			self.consumer_positions[consumer_id] = (consumer_pos + 1) % len(self.buffers)

			return chunk


class Consumer(threading.Thread):
	def __init__(self, consumerId, buffer_id, multi_buffer):
		super().__init__()
		self.consumerId = consumerId
		self.buffer_id = buffer_id
		self.multi_buffer = multi_buffer
		self.running = True

	def run(self):
		while self.running:
			self.consume()

	def consume(self):
		item = self.multi_buffer.read(self.buffer_id)
		if item:
			self.process(item)
			self.multi_buffer.mark_consumed(self.buffer_id, self.consumerId)
		else:
			time.sleep(0.01)  # Avoid busy waiting

	def process(self, item):
		raise NotImplementedError("Subclasses must implement `process`.")

	def stop(self):
		self.running = False

class AudioPlayer(Consumer):
	def __init__(self, consumerId, buffer_id, multi_buffer, wrap_point=None, speed=1.0, scale_factor=1.0):
		super().__init__(consumerId, buffer_id, multi_buffer)
		self.wrap_point = wrap_point
		self.speed = speed
		self.scale_factor = scale_factor
		self.position = 0.0
		self.total_played = 0.0

	def process(self, item):
		audio_chunk = item["data"]

		# Apply scaling
		scaled_chunk = audio_chunk * self.scale_factor

		# Play audio with sounddevice
		playback_duration = len(scaled_chunk) / 44100 / self.speed
		sd.play(scaled_chunk, samplerate=int(44100 * self.speed))

		# Update position and handle wrapping
		self.position += playback_duration
		if self.wrap_point and self.position >= self.wrap_point:
			wrapped_position = self.position - self.wrap_point
			self.total_played += self.wrap_point + wrapped_position
			self.position = wrapped_position
		else:
			self.total_played += playback_duration

		# Wait until playback is complete
		sd.wait()

	def set_scale(self, scale_factor):
		"""Set the scale factor for audio playback."""
		self.scale_factor = scale_factor

	def get_total_played(self):
		"""Get the total duration of audio played, including wraps."""
		return self.total_played

class ThreadedProducer:
	def __init__(self, buffer, buffer_id, generator):
		self.buffer = buffer
		self.buffer_id = buffer_id
		self.generator = generator
		self.thread = threading.Thread(target=self.run)
		self.running = False

	def start(self):
		self.running = True
		self.thread.start()

	def stop(self):
		self.running = False
		self.thread.join()

	def run(self):
		for chunk in self.generator:
			if not self.running:
				break
			self.buffer.write(self.buffer_id, {"data": chunk, "timestamp": time.time()})

class MathExprProducer:
	def __init__(self, math_expr, multi_buffer, samplerate=44100):
		"""
		Initialize a producer for MathExpr.
		"""
		self.math_expr = math_expr
		self.multi_buffer = multi_buffer
		self.samplerate = samplerate
		self.time_step = 1 / samplerate
		self.t = 0  # Start time
		self.running_event = Event()
		self.thread = None

	def produce(self):
		"""
		Generator function for producing chunks.
		"""
		while self.running_event.is_set():
			# Generate a buffer chunk using MathExpr's __call__
			chunk = np.array(
				[self.math_expr(self.t + n * self.time_step) for n in range(self.multi_buffer.buffer_size)],
				dtype=np.float32,
			)
			self.t += self.multi_buffer.buffer_size * self.time_step  # Increment time

			# Yield the chunk for external processing
			yield chunk

	def threaded_produce(self):
		"""
		Run the producer in a thread, writing to MultiBuffer.
		"""
		for chunk in self.produce():
			try:
				self.multi_buffer.write(chunk)
			except RuntimeError as e:
				print(f"Producer blocked: {e}")

	def start(self):
		"""
		Start the producer in a new thread.
		"""
		if self.thread and self.thread.is_alive():
			return  # Already running
		self.running_event.set()
		self.thread = threading.Thread(target=self.threaded_produce, daemon=True)
		self.thread.start()

	def stop(self):
		"""
		Stop the producer thread.
		"""
		self.running_event.clear()
		if self.thread:
			self.thread.join()
