import numpy as np
import soundfile as sf
import sounddevice as sd
from pydub.utils import mediainfo
from src.core.math_expr import *

def get_file_duration(filename):
    metadata = mediainfo(filename)
    return float(metadata['duration'])

def play_buffer(buffer, sample_rate=None, time_range=None):
	"""
	Plays a numpy buffer using sounddevice, optionally clipped by a TimeRange.
	
	Args:
		buffer (np.ndarray): The audio buffer to play. Can be mono or stereo.
		sample_rate (int or None): The sample rate of the audio. If None,
			defaults to AudioConfig.get_sample_rate().
		time_range (TimeRange or None): The range of time to play. If None, plays the full buffer.
	"""
	# Get the default sample rate if none is provided
	if sample_rate is None:
		sample_rate = AudioConfig.get_sample_rate()

	if not isinstance(buffer, np.ndarray):
		raise TypeError("Buffer must be a numpy array.")

	# Normalize buffer to fit within [-1, 1] range if necessary
	max_val = np.max(np.abs(buffer))
	if max_val > 1.0:
		buffer = buffer / max_val

	# Clip buffer using the TimeRange, if provided
	if time_range:
		start_idx = int(time_range.start * sample_rate)
		end_idx = int(time_range.end * sample_rate)
		buffer = buffer[start_idx:end_idx]

	# Play the audio buffer
	sd.play(buffer, samplerate=sample_rate)
	sd.wait()  # Wait until the buffer finishes playing


class BaseNode:
	def __init__(self, is_constant=False, finite=False, **kwargs):
		self.is_constant = is_constant
		self.finite = finite
		super().__init__(**kwargs)

	def eval(self, t):
		if isinstance(t, TimeRange):
			return np.array([self.eval(time) for time in t])
		elif isinstance(t, (int, float, np.float32, np.float64)):
			raise NotImplementedError("Subclasses must implement eval().")
		else:
			raise TypeError("Unsupported type: {type(t)}")

	def reduce(self):
		"""
		Attempt to reduce the node into a simpler form (e.g., a ConstantNode) if possible.
		"""
		return self

	def __add__(self, other):
		return AddNode(self, other)

	def __mul__(self, other):
		return MulNode(self, other)

	def __mod__(self, other):
		return ModNode(self, other)

	def __neg__(self):
		return MulNode(self, ConstantNode(-1))

	@staticmethod
	def _wrap(value):
		if isinstance(value, BaseNode):
			return value
		elif isinstance(value, (int, float, np.ndarray)):
			return ConstantNode(value)
		raise TypeError(f"Unsupported type for operation: {type(value)}")


class ConstantNode(BaseNode):
	def __init__(self, value):
		super().__init__()
		self.value = value
		self.is_constant = True

	def eval(self, t):
		return self.value  # Scalars or arrays are evaluated as-is

	def reduce(self):
		return self  # Already reduced


class AddNode(BaseNode):
	def __init__(self, *nodes):
		super().__init__()
		# Flatten nested AddNodes and separate constants
		flat_nodes = []
		constant_sum = 0
		for node in nodes:
			wrapped = self._wrap(node)
			if isinstance(wrapped, AddNode):
				flat_nodes.extend(wrapped.nodes)
			elif isinstance(wrapped, ConstantNode):
				constant_sum += wrapped.value
			else:
				flat_nodes.append(wrapped)

		# If there's a constant sum, keep it as a singular constant
		if constant_sum != 0:
			flat_nodes.append(ConstantNode(constant_sum))

		self.nodes = flat_nodes
		self.is_constant = all(node.is_constant for node in self.nodes)
		self.finite = all(node.finite for node in self.nodes)

		# Reduce to ConstantNode if possible
		reduced = self.reduce()
		if isinstance(reduced, ConstantNode):
			self.__class__ = ConstantNode
			self.value = reduced.value

	def eval(self, t):
		return sum(node.eval(t) for node in self.nodes)

	def reduce(self):
		if self.is_constant:
			return ConstantNode(sum(node.eval(0) for node in self.nodes))  # Use any valid t
		return self


class MulNode(BaseNode):
	def __init__(self, *nodes):
		super().__init__()
		# Flatten nested MulNodes and separate constants
		flat_nodes = []
		constant_product = 1
		for node in nodes:
			wrapped = self._wrap(node)
			if isinstance(wrapped, MulNode):
				flat_nodes.extend(wrapped.nodes)
			elif isinstance(wrapped, ConstantNode):
				constant_product *= wrapped.value
			else:
				flat_nodes.append(wrapped)

		# If there's a constant product, keep it as a singular constant
		if constant_product != 1:
			flat_nodes.append(ConstantNode(constant_product))

		self.nodes = flat_nodes
		self.is_constant = all(node.is_constant for node in self.nodes)
		self.finite = all(node.finite for node in self.nodes)

		# Reduce to ConstantNode if possible
		reduced = self.reduce()
		if isinstance(reduced, ConstantNode):
			self.__class__ = ConstantNode
			self.value = reduced.value

	def eval(self, t):
		result = self.nodes[0].eval(t)
		for node in self.nodes[1:]:
			result *= node.eval(t)
		return result

	def reduce(self):
		if self.is_constant:
			product = np.prod([node.eval(0) for node in self.nodes])  # Use any valid t
			return ConstantNode(product)
		return self


class ConvNode(BaseNode):
	def __init__(self, *nodes):
		super().__init__()
		# Flatten nested ConvNodes
		flat_nodes = []
		for node in nodes:
			wrapped = self._wrap(node)
			if isinstance(wrapped, ConvNode):
				flat_nodes.extend(wrapped.nodes)
			else:
				flat_nodes.append(wrapped)

		self.nodes = flat_nodes
		self.is_constant = all(node.is_constant for node in self.nodes)
		self.finite = all(node.finite for node in self.nodes)

		# Reduce to ConstantNode if possible
		reduced = self.reduce()
		if isinstance(reduced, ConstantNode):
			self.__class__ = ConstantNode
			self.value = reduced.value

	def eval(self, t):
		result = self.nodes[0].eval(t)
		for node in self.nodes[1:]:
			result = np.convolve(result, node.eval(t), mode='same')
		return result

	def reduce(self):
		if self.is_constant:
			arrays = [node.eval(0) for node in self.nodes]
			result = arrays[0]
			for array in arrays[1:]:
				result = np.convolve(result, array, mode='same')
			return ConstantNode(result)
		return self


class ModNode(BaseNode):
	def __init__(self, left, right):
		super().__init__()
		self.left = self._wrap(left)
		self.right = self._wrap(right)
		self.is_constant = self.left.is_constant and self.right.is_constant

		# Reduce to ConstantNode if possible
		reduced = self.reduce()
		if isinstance(reduced, ConstantNode):
			self.__class__ = ConstantNode
			self.value = reduced.value

	def eval(self, t):
		return self.left.eval(t) % self.right.eval(t)

	def reduce(self):
		if self.is_constant:
			mod_value = self.left.eval(0) % self.right.eval(0)  # Use any valid t
			return ConstantNode(mod_value)
		return self

class AudioSource(BaseNode):
	def __init__(self, filename: str, time_range: TimeRange = None, **kwargs):
		"""
		Initialize the AudioSource node.

		Args:
			filename (str): Path to the audio file.
			time_range (TimeRange): Optional time range to clip the audio.
									If time_range.start > time_range.end, audio is reversed.
		"""
		self.finite = True
		self.filename = filename
		self.time_range = self._adjust_time_range(time_range)

		# Load audio file metadata
		self.data, self.sample_rate = self._load_audio_metadata()

		# Validate sample rate against AudioConfig
		audio_config_rate = AudioConfig.get_sample_rate()
		if self.sample_rate != audio_config_rate:
			raise ValueError(
				f"Sample rate mismatch: file {self.sample_rate}Hz, "
				f"expected {audio_config_rate}Hz. "
				f"Resampling not implemented."
			)

		# Clip audio data to match time_range
		self.data = self._process_time_range(self.data, self.time_range)

		# Check if this node is constant (it never is, as it depends on external input)
		self.finite = True
		super().__init__(is_constant=False, finite=True, **kwargs)
	def _adjust_time_range(self, time_range: TimeRange):
		time_range = time_range or TimeRange(0, float('inf'))
		true_end = get_file_duration(self.filename)
		if time_range.end == float('inf') or time_range.end > true_end:
			time_range.end = true_end
		if time_range.start == -float('inf') or time_range.start < 0:
			time_range.start = 0
		return time_range

	def _load_audio_metadata(self):
		"""
		Load audio data and metadata from the file.

		Returns:
			Tuple[np.ndarray, int]: Audio data and its sample rate.
		"""
		data, sample_rate = sf.read(self.filename, always_2d=True)  # Ensure multi-channel
		return data, sample_rate

	def _process_time_range(self, data, time_range: TimeRange):
		"""
		Apply the time range (including reversing if necessary) to the audio data.

		Args:
			data (np.ndarray): Audio data.
			time_range (TimeRange): Time range to clip the audio.

		Returns:
			np.ndarray: Processed audio data.
		"""
		sample_rate = AudioConfig.get_sample_rate()
		num_samples = data.shape[0] if data is not None else 0
		end_time = num_samples/sample_rate if num_samples > 0 else 0
		start, end = time_range.start, time_range.end
		def clamp_positive_time(value):
			if value == float("inf"):
				return end_time
			return max(0, min(value, end_time))
		start_sample = int(clamp_positive_time(start)*sample_rate)
		end_sample = int(clamp_positive_time(end)*sample_rate)
		assert(start_sample != float("inf") and end_sample != float("inf"))
		if start_sample == 0 and end_sample == len(data):
			return data
		return data[start_sample:end_sample]

	def eval(self, t):
		if isinstance(t, TimeRange):
			t = self._adjust_time_range(t)
			return np.array([self.eval(time) for time in t])
		elif isinstance(t, (int, float, np.float32, np.float64)):
			sample_idx = int(t*self.sample_rate)
			return self.data[min(sample_idx, len(self.data)-1)]
		else:
			return super().eval(t)



class MathExprNode(BaseNode):
	def __init__(self, func, args=(), params=(), dtype=np.float32):
		self.func = func
		self.args = args
		self.params = list(params)
		self.dtype = np.result_type(dtype, *(arg.dtype
				if isinstance(arg, AudioSource) else arg for arg in args),
			*(param for param in params))
		super().__init__(is_constant=False, finite=False)
	def __call__(self, t):
		evaluated_args = [
			arg(t) if isinstance(arg, MathExpr) else arg for arg in self.args
		]
		return self.func(t, *evaluated_args, *self.params)
	def render(self, time_range: TimeRange):
		sample_rate = AudioConfig.get_sample_rate()
		duration = int(time_range.duration()*sample_rate)
		t = np.linspace(time_range.start, time_range.end, duration)
		return self(t).astype(self.dtype)
	def __add__(self, other):
		return AddNode(self, self._wrap(other))
	def __mul__(self, other):
		return MulNode(self, self._wrap(other))
	def conv(self, other):
		return ConvolveNode(self, self._wrap(other))
	@staticmethod
	def _wrap(value):
		if isinstance(value, AudioSource):
			return value
		return ConstantSource(value)


