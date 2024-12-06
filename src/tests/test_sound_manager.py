import os
import numpy as np
import src.core.sound_manager as sound_manager
from src.core.sound_manager import dtype_info, scale_dtype
from src.core.sound_manager import load_audio, save_audio
import sounddevice as sd
from src.core.custom_types import infer_type

def test_dtype_info(indent, verbose):
	if verbose:
		print(f"{indent}Testing dtype_info...")
	intmax16 = 2**15-1
	intmax32 = 2**31-1
	floatmax32 = intmax16/(2**15)
	floatmax64 = intmax32/(2**31)
	valids = [
		dtype_info('int16', None, None),
		dtype_info('int32', None, None),
		dtype_info('float32', None, None),
		dtype_info('float64', None, None),
		dtype_info(None, np.int16, None),
		dtype_info(None, np.int32, None),
		dtype_info(None, np.float32, None),
		dtype_info(None, np.float64, None),
		dtype_info(None, None, intmax16),
		dtype_info(None, None, intmax32),
		dtype_info(None, None, floatmax32),
		dtype_info(None, None, floatmax64),
	]
	nones = [
		dtype_info(None, None, None),
		dtype_info(None, np.int16, intmax32),
		dtype_info(None, np.int32, intmax16),
		dtype_info(None, np.float32, floatmax32),
		dtype_info(None, np.float64, floatmax64),
		dtype_info('int16', None, intmax32),
		dtype_info('int32', None, intmax16),
		dtype_info('float32', None, floatmax32),
		dtype_info('float64', None, floatmax64),
		dtype_info('int16', np.int32, None),
		dtype_info('int32', np.int16, None),
		dtype_info('float32', np.float64, None),
		dtype_info('float64', np.float32, None),
		dtype_info('int16', np.int16, intmax16),
		dtype_info('int32', np.int32, intmax32),
		dtype_info('float32', np.float32, floatmax32),
		dtype_info('float64', np.float64, floatmax64),
	]
	expects = [
		('int16', np.int16, intmax16),
		('int32', np.int32, intmax32),
		('float32', np.float32, floatmax32),
		('float64', np.float64, floatmax64),
		('int16', np.int16, intmax16),
		('int32', np.int32, intmax32),
		('float32', np.float32, floatmax32),
		('float64', np.float64, floatmax64),
		('int16', np.int16, intmax16),
		('int32', np.int32, intmax32),
		('float32', np.float32, floatmax32),
		('float64', np.float64, floatmax64),
	]
	passing = True
	for k in range(len(valids)):
		if valids[k] != expects[k]:
			if verbose:
				print(f"{indent}{k}: {valids[k]} != {expects[k]}")
			passing = False
	for k in range(len(nones)):
		if nones[k] is not None:
			if verbose:
				print(f"{indent}{k}: {nones[k]} != None")
			passing = False
	if not passing:
		if verbose:
			print(f"{indent}Failed test_dtype_info")
	if verbose:
		if not passing:
			print(f"{indent}...failed!")
		else:
			print(f"{indent}...done")

	return passing

def test_scale_dtype(indent, verbose):
	if verbose:
		print(f"{indent}Testing scale_dtype...")
	intmax16 = 2**15-1
	intmax32 = 2**31-1
	floatmax32 = intmax16/(2**15)
	floatmax64 = intmax32/(2**31)
	passing = True
	if scale_dtype(0, "int16") != ("int16", np.int16, intmax16):
		passing = False
	if scale_dtype(0, "float32") != ("float32", np.float32, floatmax32):
		passing = False
	if scale_dtype(1, "int16") != ("int32", np.int32, intmax32):
		passing = False
	if scale_dtype(1, "float32") != ("float64", np.float64, floatmax64):
		passing = False
	if scale_dtype(-1, "int32") != ("int16", np.int16, intmax16):
		passing = False
	if scale_dtype(-1, "float64") != ("float32", np.float32, floatmax32):
		passing = False
	if verbose:
		if passing:
			print(f"{indent}...done")
			return True
		else:
			print(f"{indent}...failed")
			return False
	return passing

def test_audio_load_and_save(origfile, newfile):
	rate,data = load_audio(origfile)
	assert data.dtype == np.float32, f"Data type {data.dtype} != np.float32"
	assert len(data.shape) == 2, f"Shape length {len(data.shape)}!=2"
	save_audio(newfile, rate, data)
	rate2,data2 = load_audio(newfile)
	assert rate == rate2, f"Rate {rate} != {rate2}"
	np.allclose(data, data2)
	return True

def test_sound_manager(root, indent, verbose, *kargs, **kwargs):
	# Test data type specification and supplementation
	if not test_dtype_info(indent+"\t", verbose):
		return False
	# Test data type and max value handling
	if not test_scale_dtype(indent+"\t", verbose):
		return False
	# File paths for testing
	buffer_file = os.path.join(root, "audio", "buffer.wav")
	original = os.path.join(root, "audio", "original.wav")
	original_name = os.path.splitext(original)[0]
	original_0 = f"{original_name}_0.wav"
	original_gain = f"{original_name}_gain.wav"
	# Test loading and saving
	if not test_audio_load_and_save(original, original_0):
		return False

	# Load a file, save as a new file, and compare
	if(verbose):
		print(f"{indent}Testing file load and save...")
	rate,data = sound_manager.load_audio(original)
	sound_manager.save_audio(original_0, rate, data)
	#mm = "Files do not match!"
	rate2,data2 = sound_manager.load_audio(original_0)
	assert rate == rate2, "Rates do not match!"
	print(f"data={infer_type(data)}, rate={infer_type(rate)}")
	print(f"data2={infer_type(data2)}, rate2={infer_type(rate2)}")
	diff = np.abs(data.astype(np.float64) - data2.astype(np.float64))
	dmax = np.max(diff)
	davg = np.mean(diff)
	davg2 = np.sum(diff)/(data.shape[0]*data.shape[1])
	print(f"Difference max: {dmax}")
	print(f"Difference avg: {davg}")
	print(f"Experimental avg: {davg2}")
	if dmax >= 5e-5:
		if verbose:
			print(f"Max error {dmax} exceeds limit 5e-5")
		return False
	if davg >= 2.5e-5:
		if verbose:
			print(f"Avg error {davg} exceeds limit 2.5e-5")
		return False
	if davg > dmax:
		if verbose:
			print(f"Max error {dmax} < average error {davg}")
		return False

	# Load a file, apply a transform, and save
	if(verbose):
		print(f"{indent}Testing transform and save...")
	transformed_data = sound_manager.gain(data)
	sound_manager.save_audio(original_gain, rate, transformed_data)

	# Open input stream, apply transform, play back through output stream
	if(verbose):
		print(f"{indent}Testing stream transformation...")
	def stream_generator(freq,phase,rate,duration):
		for i in range(5):  # Simulate 5 chunks
			#yield np.random.randn(44100).astype(np.float32) * 0.1
			t = np.linspace(0, duration, int(rate*duration), endpoint=False)
			factor = 2*np.pi*freq
			t = 0.5*np.sin(factor*t+phase)
			phase += factor*duration
			yield t
	sound_manager.play_audio_from_stream(stream_generator(440,0,44100,0.1))

	# Open input stream, save output to file
	if(verbose):
		print(f"{indent}Testing stream to file saving...")
	buffer = []
	for chunk in stream_generator(880,0,44100,0.1):
		buffer.append(chunk)
	combined_audio = np.concatenate(buffer)
	sound_manager.save_audio(buffer_file, rate, combined_audio)

	return True
