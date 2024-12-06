from typing import Generator, Any
from scipy.io.wavfile import read, write
import soundfile as sf
import numpy as np
import asyncio
import sounddevice as sd
from src.core.custom_types import infer_type

def dtype_info(dtype_str=None, np_dtype=None, max_value=None):
	intmax16 = 2**15-1
	intmax32 = 2**31-1
	floatmax32 = intmax16/(2**15)
	floatmax64 = intmax32/(2**31)
	dtype_map = {
		"int16": (np.int16, intmax16),
		"int32": (np.int32, intmax32),
		"float32": (np.float32, floatmax32),
		"float64": (np.float64, floatmax64),
	}
	np_map = {v[0]: (k, v[1]) for k, v in dtype_map.items()}
	max_map = {v[1]: (k, v[0]) for k, v in dtype_map.items()}
	nones = sum(x is None for x in (dtype_str, np_dtype, max_value))
	if nones != 2:
		return None
	if dtype_str is not None:
		#if not dtype_map[dtype_str]:
		#	return None
		n,v = dtype_map[dtype_str]
		return dtype_str, n, v
	if np_dtype is not None:
		#if not np_map[np_dtype]:
		#	return None
		s,v = np_map[np_dtype]
		return s, np_dtype, v
	if max_value is not None:
		#if not max_map[max_value]:
		#	return None
		s,n = max_map[max_value]
		return s, n, max_value
	return None

def scale_dtype(power, s=None, n=None, v=None):
	intmax16 = 2**15-1
	intmax32 = 2**31-1
	floatmax32 = intmax16/(2**15)
	floatmax64 = intmax32/(2**31)
	dtype_info_res = dtype_info(s, n, v)
	if not dtype_info_res:
		return None

	print(f"scale_dtype[0]: {s}, {n}, {v}")
	dtype_str, np_dtype, max_value = dtype_info_res
	print(f"scale_dtype[1]: {dtype_str}, {np_dtype}, {max_value}\n")

	# Calculate new bit depth
	current_bits = {
		'int16': 16, 'int32': 32, 'float32': 32, 'float64': 64
	}.get(dtype_str, None)
	if current_bits is None:
		return None

	new_bits = int(current_bits * (2**power))

	float_map = {
		'int16': False, 'int32': False, 'float32': True, 'float64': True
	}
	floating = float_map.get(s, None)
	if floating is None:
		return None
	if floating == False:
		bit_to_dtype = {
			16: ('int16', np.int16, intmax16),
			32: ('int32', np.int32, intmax32),
		}
		return bit_to_dtype.get(max(16,min(32,new_bits)), None)
	elif floating == True:
		bit_to_dtype = {
			32: ('float32', np.float32, floatmax32),
			64: ('float64', np.float64, floatmax64),
		}
		return bit_to_dtype.get(max(32,min(64,new_bits)), None)
	else:
		return None


def load_audio(filepath, dtype='float32'):
	data, rate = sf.read(filepath, dtype=dtype)
	buf = ensure_stereo(data)
	return rate, buf

def save_audio(filepath, rate, data):
	buf = ensure_stereo(data)
	sf.write(filepath, buf, samplerate=rate)

def ensure_stereo(buffer):
	if len(buffer.shape) == 1:
		buffer = np.stack((buffer, buffer), axis=-1)
	return buffer

def gain(data, db=None):
	if db is None:
		return data
	return data * (10 ** (db/20))

def low_pass(data, cutoff=1000, rate=44100, order=5):
	nyquist = 0.5 * rate
	normal = cutoff/nyquist
	b,a = butter(order, cutoff, btype="low", analog=False)
	return lfilter(b, a, data)
	#fft_data = np.fft.rfft(data)
	#freqs = np.fft.rfftfreq(len(data), d=1/rate)
	#fft_data[freqs>cutoff] = 0
	#return np.fft.irfft(fft_data)

def reverb(data, impulse_response):
	return np.convolve(data, impulse_response, mode='full')[:len(data)]

async def audio_buffer_manager(bufsize, src, sink):
	buffer = np.zeros(bufsize)
	while True:
		chunk = await src()
		buffer = np.concatenate((buffer[len(chunk):], chunk))
		processed_chunk = process_audio(buffer)
		await sink(processed_chunk)

def play_audio_from_file(filepath, start=0, stop=-1, dtype='float32'):
	#rate,data = read(filepath)
	rate,data = load_audio(filepath, dtype=dtype)
	data = ensure_stereo(data)
	data = data.astype(np.float32) / 32768
	sample0 = int(start*rate)
	sample1 = int(stop*rate) if stop>0 else len(data)
	sd.play(data[sample0:sample1], samplerate=rate)
	sd.wait()

def play_audio_from_stream(g: Generator[np.ndarray, Any, None], rate=44100):
	for buffer in g:
		try:
			def audio_callback(outdata, frames, time, status):
				if status:
					print("Stream status:", status)
				try:
					chunk = next(g)
					if len(chunk.shape) == 1:
						#chunk = np.column_stack((chunk, chunk))
						#chunk = chunk.reshape(-1,1)
						chunk = ensure_stereo(chunk)
					chunk_frames = chunk.shape[0]
					if chunk_frames < frames:
						outdata[:chunk_frames] = chunk
						outdata[chunk_frames:] = 0
					else:
						before = chunk[:frames]
						if len(before.shape) == 1:
							#before = np.column_stack((before, before))
							before = ensure_stereo(before)
						outdata[:] = before
				except StopIteration:
					raise sd.CallbackStop
			with sd.OutputStream(
				samplerate=rate,
				#channels=1 if len(first_chunk.shape) == 1 else 2,
				channels=2,
				dtype='float32',
				blocksize=1024,
				callback=audio_callback,
			):
				sd.sleep(1000)
		except Exception as e:
			print(f"Error while playing audio: {e}!")

