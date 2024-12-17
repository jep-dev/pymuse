from src.core.view import View
from src.core.json_manager import load_settings


def test_view(root, indent="", verbose=False, *kargs, **kwargs):
	try:
		settings = load_settings(root)
		view = View(settings)
		view.start()
		return True
	except pygame.error as e:
		print(f"{indent}SDL error: {e}")
		pygame.quit()
		return False

