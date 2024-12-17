import numpy as np
from collections.abc import Iterable

class AudioConfig:
	DEFAULT_SAMPLE_RATE = 44100
	_current_sample_rate = DEFAULT_SAMPLE_RATE
	@staticmethod
	def set_sample_rate(sample_rate: int):
		AudioConfig._current_sample_rate = sample_rate
	@staticmethod
	def get_sample_rate():
		return AudioConfig._current_sample_rate

class TimeRange(Iterable):
	def __init__(self, start, end, step=1/AudioConfig.get_sample_rate()):
		self.start = max(0, start)
		self.end = end
		self.step = max(0, step)

	def duration(self):
		if self.start != self.end and self.end == float("inf"):
			return float("inf")
		return abs(self.end - self.start)
	def __iter__(self):
		"""
		Generate time points within the range [start, end] with the given step size.
		Handles infinite bounds gracefully.
		"""
		t = self.start
		max_iterations = 1_000_000  # Prevent infinite loops in case of bad input
		iterations = 0

		#while ((t <= self.end and self.step > 0) or (t >= self.end and self.step < 0)):
		while (t < self.end and self.step > 0):
			yield t
			t += self.step
			iterations += 1

			# Prevent infinite looping for infinite end
			#if self.end == float("inf") or self.end == -float("inf"):
			if iterations >= max_iterations:
				raise RuntimeError(
					f"Iteration limit reached for TimeRange: start={self.start}, "
					f"end={self.end}, step={self.step}. Check for infinite range."
				)
	def __getitem__(self, num):
		return self.start + self.step * num

class MathExpr:
	def __init__(self, func, args=(), params=()):
		self.func = func
		self.args = args
		self.params = list(params)

	def __call__(self, t):
		"""
		Evaluate the MathExpr. If `t` is a scalar (float/int), return a scalar.
		If `t` is an iterable (like TimeRange), return a numpy array.
		"""
		if isinstance(t, (int, float, np.float32, np.float64)):
			return self._evaluate_single_point(t)
		elif isinstance(t, TimeRange):
			return np.array([self._evaluate_single_point(tp) for tp in t], dtype=np.float32)
		else:
			raise TypeError(f"Unsupported type: {type(t)}")

	def eval(self, t):
		return self(t)

	def _evaluate_single_point(self, t):
		"""
		Evaluate the MathExpr for a single point in time.
		"""
		evaluated_args = [
			arg(t) if isinstance(arg, MathExpr) else arg for arg in self.args
		]
		return self.func(t, *evaluated_args, *self.params)

	def __add__(self, other):
		other = self._wrap(other)  # Ensure compatibility
		return MathExpr(lambda t, a, b: a + b, args=(self, other))

	def __sub__(self, other):
		other = self._wrap(other)  # Ensure compatibility
		return MathExpr(lambda t, a, b: a - b, args=(self, other))

	def __mul__(self, other):
		other = self._wrap(other)  # Ensure compatibility
		return MathExpr(lambda t, a, b: a * b, args=(self, other))

	def __truediv__(self, other):
		other = self._wrap(other)  # Ensure compatibility
		return MathExpr(lambda t, a, b: a / b, args=(self, other))

	def __mod__(self, other):
		other = self._wrap(other)  # Ensure compatibility
		return MathExpr(lambda t, a, b: a % b, args=(self, other))

	def __neg__(self):
		return MathExpr(lambda t, a: -a, args=(self,))

	@staticmethod
	def _wrap(value):
		"""
		Ensure the input is a MathExpr or wrap it into a MathExpr constant.
		"""
		if isinstance(value, MathExpr):
			return value
		elif isinstance(value, (int, float, np.float32, np.float64)):
			return MathExpr._constant(value)
		raise TypeError(f"Unsupported type for MathExpr operation: {type(value)}")

	@staticmethod
	def _constant(value):
		return MathExpr(lambda t, v: v, params=(value,))


# Convenience methods
def constant(value):
	return MathExpr._constant(value)


def sine(frequency=440, phase=0):
	return MathExpr(lambda t, f, p: np.sin(2 * np.pi * f * t + p),
		params=(frequency, phase))


def triangle(frequency=440, phase=0):
	return MathExpr(lambda t, f, p: 2 * np.abs(2 * ((t * f + p / (2 * np.pi)) % 1) - 1) - 1,
		params=(frequency, phase))


def square(frequency=440, phase=0):
	return MathExpr(lambda t, f, p: np.sign(np.sin(2 * np.pi * f * t + p)),
		params=(frequency, phase))


def sawtooth(frequency=440, phase=0):
	return MathExpr(lambda t, f, p: 2 * (t * f + p / (2 * np.pi)) % 1 - 1,
		params=(frequency, phase))

def math_expr_producer(buffer, buffer_id, math_expr, duration=1.0,
		samplerate=44100, chunk_size = 1024):
	time_step = 1 / samplerate
	t = 0  # Start time
	while True:
		# Create a chunk of audio samples
		chunk = np.array([math_expr(t + n * time_step) for n in range(chunk_size)], dtype=np.float32)
		t += chunk_size * time_step  # Increment time
		yield chunk


#wave = sine(440).scale(0.25) + sine(880).scale(.75)
#generator = Generator(expression = wave, rate = 44100)
#producer = Producer(generator, num=4, size=1024)
#audio_source = AudioSource(generator, num=4, size=1024)

