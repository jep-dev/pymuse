from src.core.custom_types import infer_type

def test_type_dims(indent, verbose, *kargs, **kwargs):
	test_cases = [
		None,
		42,
		str(),
		(),
		(1,"a"),
		[],
		[1,2,3],
		[[1,2],[3,4],[5,6]],
		[[[1],[2]],[[3],[4]]],
		{},
		{"k0":1, "k1":0},
	]
	test_results = [
		"NoneType",
		"int",
		"str",
		"tuple",
		"tuple[int,str]",
		"list",
		"list[int]",
		"list[list[int]]",
		"list[list[list[int]]]",
		"dict[NoneType,NoneType]",
		"dict[str,int]",
	]
	for i in range(len(test_cases)):
		case = test_cases[i]
		type_str = infer_type(case)
		test_result = test_results[i]
		if verbose and (type_str != test_result):
			print(f"{indent}Mismatch: {case}:{type_str} != {test_result}")
			return False
	return True

def test_types(root, indent, verbose, *kargs, **kwargs):
	if verbose:
		print(f"{indent}Running test_types...")
	output = test_type_dims(indent+"\t", verbose)
	if verbose:
		print(f"{indent}Running test_types...")
	return output
