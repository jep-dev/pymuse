from pathlib import Path
import numpy as np
from src.core.audio_source import *


def test_audio_source(root, indent="", verbose=False, *args, **kwargs):
	"""
	Master test suite for AudioSource and related Node systems.
	
	Args:
		root (Path): Root directory where the audio files are stored.
		indent (string): Indentation level for verbose output.
		verbose (bool): If True, print detailed test progress.
		*args, **kwargs: Additional arguments.
	
	Returns:
		bool: True if all tests pass, False otherwise.
	"""
	test_dir = Path(root) / "audio"
	test_file = test_dir / "short.mp3"  # Platform-independent path

	if not test_file.exists():
		raise FileNotFoundError(f"Test file not found: {test_file}")

	sample_rate = AudioConfig.get_sample_rate()
	report("Starting AudioSource and Node tests...", indent, verbose)

	# Run individual tests and collect results
	results = [
		test_audio_source_node(test_file, sample_rate, indent, verbose),
		test_node_tree_evaluation(indent, verbose),
		test_time_range_clipping(test_file, sample_rate, indent, verbose)
	]

	all_passed = all(results)
	report("All tests completed." + (" Success!" if all_passed else " Failure!"), indent, verbose)
	return all_passed


def test_audio_source_node(test_file, sample_rate, indent, verbose):
	"""
	Test AudioSource functionality.
	
	Returns:
		bool: True if the test passes, False otherwise.
	"""
	try:
		report("Testing AudioSource functionality...", indent, verbose)

		# Create an AudioSource
		time_range = TimeRange(0, 2.0)
		source = AudioSource(filename=str(test_file), time_range=time_range)
		report(f"Loaded AudioSource from '{test_file}'.", indent + "\t", verbose)

		# Evaluate the source for a 1-second range
		time_range = TimeRange(0.5, 1.5)
		audio_output = source.eval(time_range)
		report(f"Evaluated AudioSource for TimeRange {time_range}.", indent + "\t", verbose)

		# Play the buffer
		report("Playing evaluated buffer...", indent + "\t", verbose)
		play_buffer(audio_output, sample_rate=sample_rate, time_range=time_range)

		return True
	except Exception as e:
		report(f"AudioSource test failed: {e}", indent, verbose)
		return False


def test_node_tree_evaluation(indent, verbose):
	"""
	Test Node tree functionality and arithmetic equivalence.
	
	Returns:
		bool: True if the test passes, False otherwise.
	"""
	try:
		report("Testing Node tree evaluation and arithmetic equivalence...", indent, verbose)

		# Create sine wave and composite expressions
		sine_wave = sine(440) * sine(880) * 0.5 + sine(220)
		composite = sine_wave * 2 + 1

		# Evaluate the composite node over a TimeRange
		time_range = TimeRange(0.0, 1.0)
		composite_output = composite.eval(time_range)
		report(f"Evaluated composite Node for TimeRange {time_range}.", indent + "\t", verbose)

		# Play the composite buffer
		report("Playing composite buffer...", indent + "\t", verbose)
		play_buffer(composite_output, time_range=time_range)

		return True
	except Exception as e:
		report(f"Node tree evaluation test failed: {e}", indent, verbose)
		return False


def test_time_range_clipping(test_file, sample_rate, indent, verbose):
	"""
	Test audio playback with clipping via TimeRange.
	
	Returns:
		bool: True if the test passes, False otherwise.
	"""
	try:
		report("Testing TimeRange clipping...", indent, verbose)

		# Load AudioSource
		source = AudioSource(filename=str(test_file), time_range=None)
		full_output = source.eval(TimeRange(0, float("inf")))

		# Play the full output
		report("Playing full buffer...", indent + "\t", verbose)
		play_buffer(full_output, sample_rate=sample_rate)

		return True
	except Exception as e:
		report(f"TimeRange clipping test failed: {e}", indent, verbose)
		return False


def report(msg, indent, verbose):
	"""
	Helper function to print verbose test information.
	Args:
		msg (str): Message to report.
		indent (string): Indentation string
		verbose (bool): If True, print the message.
	"""
	if verbose:
		print(indent + msg)

