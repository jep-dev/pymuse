import threading
import time
import sounddevice as sd
import numpy as np
from queue import Queue

class MultiBuffer:
	def __init__(self, buffer_count=2, maxsize=10):
		self.buffers = {i: Queue(maxsize=maxsize) for i in range(buffer_count)}
		self.locks = {i: threading.Lock() for i in range(buffer_count)}
		self.consumer_progress = {i: set() for i in range(buffer_count)}

	def write(self, buffer_id, item):
		with self.locks[buffer_id]:
			if not self.buffers[buffer_id].full():
				self.buffers[buffer_id].put(item)

	def read(self, buffer_id):
		with self.locks[buffer_id]:
			if not self.buffers[buffer_id].empty():
				return self.buffers[buffer_id].get()
		return None

	def mark_consumed(self, buffer_id, consumer_id):
		with self.locks[buffer_id]:
			self.consumer_progress[buffer_id].add(consumer_id)

	def is_consumed_by_all(self, buffer_id, consumer_ids):
		with self.locks[buffer_id]:
			return self.consumer_progress[buffer_id].issuperset(consumer_ids)

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

# Example usage
if __name__ == "__main__":
	multi_buffer = MultiBuffer(buffer_count=1)

	# Simulate an audio producer writing chunks to the buffer
	def dummy_producer(buffer, buffer_id):
		for _ in range(100):
			chunk = np.random.rand(44100 * 2) * 0.5  # Simulate 1 second of stereo audio
			buffer.write(buffer_id, {"data": chunk, "timestamp": time.time()})
			time.sleep(0.1)

	producer_thread = threading.Thread(target=dummy_producer, args=(multi_buffer, 0))
	producer_thread.start()

	# Start an audio player consumer
	audio_player = AudioPlayer(consumerId=1, buffer_id=0, multi_buffer=multi_buffer, wrap_point=30, speed=1.0)
	audio_player.start()

	# Run for some time
	try:
		time.sleep(10)
		audio_player.set_scale(0.8)  # Reduce volume
		time.sleep(10)
	finally:
		audio_player.stop()
		audio_player.join()
		producer_thread.join()

	print(f"Total audio played (seconds): {audio_player.get_total_played()}")

