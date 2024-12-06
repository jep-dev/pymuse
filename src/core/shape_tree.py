from typing import Generic, TypeVar, Union, List, Any, Generator, Tuple
import numpy as np

T = TypeVar('T')

class Placeholder(Generic[T]):
	def __init__(self, type_param: T = None):
		self.type_param = type_param
	def __repr__(self):
		return f"Placeholder[{self.type_param}]"
	def __str__(self):
		return f"${self.type_param.__name__ if self.type_param else '?'}"
		#if self.type_param is None:
		#	return "$"
		#elif self.type_param is Any:
		#	return "$?"
		#else:
		#	return f"${self.type_param.__name__}"

ShapeTree = Union[Placeholder, list['ShapeTree']]

def create_shape_tree(obj, dimensional=True) -> ShapeTree:
	if isinstance(obj, (list,tuple,np.ndarray)):
		return [create_shape_tree(x, dimensional) for x in obj]
	return Placeholder[type(obj)](type(obj))

def are_shapes_compatible(shape1: ShapeTree, shape2: ShapeTree, dimensional) -> bool:
	if isinstance(shape1, Placeholder) and isinstance(shape2, Placeholder):
		if not dimensional:
			return shape1.type_param is shape2.type_param
		return True
	if isinstance(shape1, list) and isinstance(shape2, list):
		return len(shape1) == len(shape2) and all(
			are_shapes_compatible(sub1,sub2,dimensional)
			for sub1,sub2 in zip(shape1,shape2)
		)
	return False


def generate_index_tuples(shape_tree: Any, prefix: Tuple[int,...] = ()) -> (Generator[tuple[int,...], None, None]):
	if isinstance(shape_tree, list):
		for i,subtree in enumerate(shape_tree):
			yield from generate_index_tuples(subtree, prefix + (i,))
	else:
		yield prefix


def get_value_at_indices(structure:Any, indices:Tuple[int,...]) -> Any:
	value = structure
	for i in indices:
		value = value[i]
	return value


