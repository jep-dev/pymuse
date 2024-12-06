from typing import Any, List, Tuple, get_origin, get_args
from collections.abc import Mapping

def infer_type(x: Any) -> str:
	def type_name(obj):
		return obj.__name__ if hasattr(obj, "__name__") else str(obj)
	if x is None:
		return "NoneType"
	base = type(x)
	if isinstance(x, Mapping):
		ktype = infer_type(next(iter(x.keys()), None))
		vtype = infer_type(next(iter(x.values()), None))
		return f"dict[{ktype},{vtype}]"
	elif isinstance(x, (list, tuple, set)):
		name = f"{base.__name__}"
		if len(x) == 0:
			return name
		types = {infer_type(elem) for elem in x}
		elem_types = ",".join(sorted(types))
		return f"{name}[{elem_types}]"
	origin = get_origin(base)
	args = get_args(base)
	if origin:
		args_str = ",".join(infer_type(arg for arg in args))
		return f"{type_name(origin)}[{args_str}]"
	return type_name(base)
