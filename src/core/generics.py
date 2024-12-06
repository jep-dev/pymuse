#from typing import TypeVar, Generic, Union
#Tag = Union[ZeroTag, ConstTag, VarTag]
#T = TypeVar('T', bound=Tag)
#class EdgeBase:
#	pass
#class Edge(Generic[T], EdgeBase):
#	def __init__(self, tag: T):
#		self.tag = tag
#	def process(self) -> str:
#		return f"Processing {self.tag.describe()}"
