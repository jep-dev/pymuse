import numpy as np
from scipy.signal import savgol_filter  # For smoothing

class TimeMapper:
	def __init__(self, input_range, output_range=(0.0, 1.0), smoothing_window=5, polyorder=2):
		"""
		Map dynamic input values to time.
		:param input_range: Tuple (min_input, max_input), e.g., (-128, 127).
		:param output_range: Tuple (min_time, max_time), e.g., (0.0, 1.0).
		:param smoothing_window: Window size for smoothing (must be odd).
		:param polyorder: Polynomial order for smoothing.
		"""
		self.input_range = input_range
		self.output_range = output_range
		self.history = []  # Store recent input values
		self.smoothing_window = smoothing_window
		self.polyorder = polyorder

	def add_input(self, value):
		"""Add a new control input value."""
		self.history.append(value)
		# Keep history size manageable
		if len(self.history) > self.smoothing_window * 2:
			self.history.pop(0)

	def get_mapped_time(self, t):
		"""
		Return the mapped time at the current logical time `t`.
		:param t: Logical time (continuous input).
		:return: Mapped time (e.g., for playback).
		"""
		if not self.history:
			return t  # Default to linear time if no inputs
		# Normalize and smooth the input history
		smoothed = savgol_filter(self.history, self.smoothing_window, self.polyorder)
		normalized = np.interp(smoothed, self.input_range, self.output_range)
		return normalized[-1]  # Use the most recent value for time mapping

	def __call__(self, t):
		"""Make the class callable as a time mapping."""
		return self.get_mapped_time(t)

	def inverse(self, mapped_time):
		"""Optional: Define inverse mapping if needed."""
		raise NotImplementedError("Dynamic mappings typically lack invertibility.")

