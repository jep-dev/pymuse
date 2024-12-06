from src.core.function import *

class AudioSource:
    def __init__(self, func:Function, rate:int=44100, duration:float=0.1):
        self.func=func
        self.rate=rate
        self.duration=duration
        slef.time=0.0
    def generate_chunk(self) -> np.ndarray:
        size = int(self.rate*self.duration)
        times = np.linspace(self.time, self.time+self.duration, size, endpoint=False)
        chunk = self.func.evaluate(times)
        self.time += self.duration
        return chunk

# src1 = SineWaveSource(440)
# src2 = SineWaveSource(880)
# src12 = src1 + src2
# play_audio_from_stream(src12())
