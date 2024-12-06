import os
from src.core.custom_types import infer_type
from src.core.shape_tree import Placeholder, create_shape_tree, are_shapes_compatible, generate_index_tuples, get_value_at_indices

def test_create_shape_tree_types(indent, verbose):
	if verbose:
		print(f"{indent}Testing create_shape_tree with types...")

	obj1 = [[1, 2], [3, 4]]  # Integers
	obj2 = [["a", "b"], ["c", "d"]]  # Strings

	tree1 = create_shape_tree(obj1, dimensional=False)
	tree2 = create_shape_tree(obj2, dimensional=False)
	if verbose:
		print(f"Tree1: {infer_type(tree1)}")
		print(f"Tree2: {infer_type(tree2)}")

	# Check that tree1 has Placeholder[int]
	isP1 = all(
		isinstance(el, Placeholder) and el.type_param is int
		for row in tree1 for el in row
	)
	assert isP1, f"Failed: tree1 elements are not Placeholder[int]"

	# Check that tree2 has Placeholder[str]
	isP2 = all(
		isinstance(el, Placeholder) and el.type_param is str
		for row in tree2 for el in row
	)
	assert isP2, f"Failed: tree2 elements are not Placeholder[str]"

	if verbose:
		print(f"{indent}Passed create_shape_tree with types test.")
	return True

def test_create_shape_tree(indent="", verbose=False):
	if verbose:
		print(f"{indent}Testing create_shape_tree...")

	obj1 = [[1, 2], [3, 4]]
	obj2 = [["a", "b"], ["c", "d"]]

	tree1 = create_shape_tree(obj1)
	tree2 = create_shape_tree(obj2, dimensional=False)

	assert isinstance(tree1, list), f"Failed: tree1 is not a list"
	isP1 = all(isinstance(el, Placeholder) and el.type_param is int for row in tree1 for el in row)
	if not isP1:
		print(f"{indent}Error with tree1: {infer_type(tree1)}")
	assert isP1, f"Failed: tree1 elements are not Placeholders"

	assert isinstance(tree2, list), f"Failed: tree2 is not a list"
	isP2 = all(isinstance(el, Placeholder) and el.type_param is str for row in tree2 for el in row)
	if not isP2:
		print(f"{indent}Error with tree2: {infer_type(tree2)}")
	assert isP2, f"Failed: tree2 elements are not Placeholder[str]s"

	if verbose:
		print(f"{indent}Passed create_shape_tree tests.")
	return True

def test_are_shapes_compatible(indent="", verbose=False):
	if verbose:
		print(f"{indent}Testing are_shapes_compatible...")

	tree1 = create_shape_tree([[1, 2], [3, 4]])
	tree2 = create_shape_tree([["a", "b"], ["c", "d"]])

	compatible = are_shapes_compatible(tree1, tree2, True)
	assert compatible, f"Failed: Shapes should be compatible."

	tree3 = create_shape_tree([[1, 2], [3]])
	incompatible = not are_shapes_compatible(tree1, tree3, True)
	assert incompatible, f"Failed: Shapes should be incompatible."

	if verbose:
		print(f"{indent}Passed are_shapes_compatible tests.")
	return True

def test_generate_index_tuples(indent="", verbose=False):
	if verbose:
		print(f"{indent}Testing generate_index_tuples...")

	tree = create_shape_tree([[1, 2], [3, 4]])
	expected_indices = [(0, 0), (0, 1), (1, 0), (1, 1)]

	generated_indices = list(generate_index_tuples(tree))
	assert generated_indices == expected_indices, (
		f"Failed: Generated indices {generated_indices} do not match expected {expected_indices}."
	)

	if verbose:
		print(f"{indent}Passed generate_index_tuples tests.")
	return True

def test_get_value_at_indices(indent="", verbose=False):
	if verbose:
		print(f"{indent}Testing get_value_at_indices...")

	structure = [[10, 20], [30, 40]]
	indices = (1, 0)
	value = get_value_at_indices(structure, indices)

	assert value == 30, f"Failed: At {indices}, value={value} != 30."

	if verbose:
		print(f"{indent}Passed get_value_at_indices tests.")
	return True

def test_shape_tree(root_path, indent, verbose, *args, **kwargs) -> bool:
	if verbose:
		print(f"{indent}Running all ShapeTree tests...")

	tests = {
		"test_create_shape_tree_types": test_create_shape_tree_types,
		"create_shape_tree": test_create_shape_tree,
		"are_shapes_compatible": test_are_shapes_compatible,
		"generate_index_tuples": test_generate_index_tuples,
		"get_value_at_indices": test_get_value_at_indices,
	}

	all_tests_passed = True

	for test_name in tests.keys():
		test_fn = tests[test_name]
		if verbose:
			print(f"{indent}Running {test_name}...")

		test_passed = test_fn(indent=indent + "\t", verbose=verbose)

		if not test_passed:
			all_tests_passed = False
			if verbose:
				print(f"{indent}Test {test_name} failed.")

	if verbose:
		if all_tests_passed:
			print(f"{indent}All ShapeTree tests passed.")
		else:
			print(f"{indent}Some ShapeTree tests failed.")

	return all_tests_passed

