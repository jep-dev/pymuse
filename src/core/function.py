import numpy as np
from typing import Callable, List, Union

class Function:
	# TODO NOTE must change float to union of np.float32 and np.float64
	def __init__(self, func:Callable[[np.ndarray, List[float]], np.ndarray], params: List[float]):
		self.func = func
		self.params = np.array(params, dtype=np.float64)
	def evaluate(self, t:Union[np.ndarray,float]) -> np.ndarray:
		if isinstance(t,(int,float)):
			t = np.array([t],dtype=np.float64)
			return self.func(t, self.params)
	def copy(self, factor:float=1.0) -> 'Function':
		return Function(lambda t,p:self.func(t,p) * factor, self.params)
	def offset(self,value:float=0.0) -> 'Function':
		return Function(lambda t,p: self.func(t,p) + value, self.params)
	def __add__(self, other:'Function') -> 'Function':
		if isinstance(other, Function):
			return Function(lambda t,p:self.func(t,p) + other.evaluate(t), self.params)
		else:
			return self.offset(other)
	def __mul__(self, other:'Funcion') -> 'Function':
		if isinstance(other, Function):
			return Function(lambda t,p: self.func(t,p) * other.evaluate(t), self.params)
		else:
			return self.scale(other)

def frame_to_chunk(func:Callable[[float],float], rate:int, duration:float) -> Callable[[np.ndarray],np.ndarray]
	def wrapped_chunk(times:np.ndarray) -> np.ndarray:
		return np.array([func(t) for t in times])
	return wrapped_chunk
def chunk_to_frame(func:Callable[[np.ndarray],np.ndarray], rate:int) -> Callable[[float],float]:
	def wrapped_frame(time:float) -> float:
		return func(np.array([time]))[0]
	return wrapped_frame

class CompositeFunction(Function):
	def __init__(self,*functions:Function):
		self.functions=functions
	def evaluate(self, t:Union[np.ndarray,float]) -> np.ndarray:
		return sum(f.evaluate(f) for f in self.functions)

# sine = Function(lambda t,p:np.sin(2*np.pi*p[0]*t+p[1]), [440,0])
# triangle = Function(lambda t,p:((t*p[0]+p[1])%(2*np.pi))*2-1, [2*np.pi*880,0])
# composite = CompositeFunction(sine.scale(0.5), triangle.scale(0.5))

