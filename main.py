import os
import sys

# Add the src directory to sys.path for module imports
root = os.path.abspath(os.path.dirname(__file__))
src_path = os.path.join(root, "src")
if src_path not in sys.path:
	sys.path.append(src_path)

from src.core.pygame_init import *
print("Starting pygame...")
try:
	pygame.mixer.pre_init()
	pygame.init()
except pygame.error as e:
	print(f"SDL error: {e}!")
	pygame.quit()
	exit(1)
print("...done")

#from src.tests.test_shape_tree import test_shape_tree
#from src.tests.test_types import test_types
##from src.tests.test_node import test_nodes
#from src.tests.test_sound_manager import test_sound_manager
from src.tests.test_view import test_view
#from src.tests.test_buffer import test_buffer
from src.tests.test_audio_source import test_audio_source

def main():
	master_verbose = True
	dct = {
		"audio_source": (test_audio_source,True),
		#"shape_tree": (test_shape_tree,False),
		#"types": (test_types,False),
		##"nodes": (test_nodes,True),
		#"sound_manager": (test_sound_manager,True),
		"view": (test_view,True),
		#"buffer": (test_buffer,True),
	}
	for k in dct.keys():
		print(f"Testing {k}...")
		vf,verbose = dct[k]
		if not vf(root, "\t", verbose):
			print(f"Test of {k} failed!")
			return 1
	return 0


if __name__ == "__main__":
	main()

