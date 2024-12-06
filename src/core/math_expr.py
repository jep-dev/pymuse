import numpy as np
import time

class MathExpr:
	def __init__(self, func, args=(), params=()):
		self.func = func
		self.args = args
		self.params = list(params)

	def __call__(self, t):
		evaluated_args = [arg(t) if isinstance(arg, MathExpr) else arg for arg in self.args]
		return self.func(t, *evaluated_args, *self.params)

	def __add__(self, other):
		return MathExpr(lambda t, a, b: a + b, args=(self, other))

	def __sub__(self, other):
		return MathExpr(lambda t, a, b: a - b, args=(self, other))

	def __mul__(self, other):
		return MathExpr(lambda t, a, b: a * b, args=(self, other))

	def __truediv__(self, other):
		return MathExpr(lambda t, a, b: a / b, args=(self, other))

	def __neg__(self):
		return MathExpr(lambda t, a: -a, args=(self,))

	def scale(self, factor):
		return MathExpr(lambda t, a, f: a * f, args=(self,), params=(factor,))

	def offset(self, offset):
		return MathExpr(lambda t, a, o: a + o, args=(self,), params=(offset,))


# Convenience methods
def sine(frequency=440, phase=0):
	return MathExpr(lambda t, f, p: np.sin(2 * np.pi * f * t + p), params=(frequency, phase))

def constant(value):
	return MathExpr(lambda t, v: v, params=(value,))

def math_expr_producer(buffer, buffer_id, math_expr, duration=1.0, samplerate=44100):
	"""
	Use a MathExpr generator (e.g., sine wave) to produce audio chunks.
	Args:
		buffer: MultiBuffer instance to write data to.
		buffer_id: ID of the buffer to write to.
		math_expr: MathExpr instance representing the generator.
		duration: Duration of each audio chunk (in seconds).
		samplerate: Number of samples per second.
	"""
	t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
	phase = 0  # Initial phase offset
	while True:
		# Evaluate the math expression
		values = np.array([math_expr.evaluate(time_point) for time_point in t + phase], dtype=np.float32)
		phase += duration  # Update phase to ensure continuity

		# Apply optional modulation (e.g., amplitude modulation)
		mod_freq = 5  # Modulation frequency (5 Hz)
		modulation = 0.5 + 0.5 * np.sin(2 * np.pi * mod_freq * t)
		modulated_values = values * modulation

		buffer.write(buffer_id, {"data": modulated_values, "timestamp": time.time()})
		time.sleep(duration)  # Simulate real-time playback



#wave = sine(440).scale(0.25) + sine(880).scale(.75)
#generator = Generator(expression = wave, rate = 44100)
#producer = Producer(generator, num=4, size=1024)
#audio_source = AudioSource(generator, num=4, size=1024)

