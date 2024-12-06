from src.core.view import *
from src.core.event_handler import EventHandler
from src.core.json_manager import load_settings

def test_view(root, indent, verbose, *kargs, **kwargs):
	try:
		settings = load_settings(root)
		# Initialize Pygame
		pygame.init()

		# Configure the window
		fullscreen = settings["window"]["fullscreen"]
		info = pygame.display.Info()
		W,H = info.current_w, info.current_h
		width = settings["window"]["width"]
		if width == -1:
			width = W if fullscreen else int(.8*W)
		height = settings["window"]["height"]
		if height == -1:
			height = H if fullscreen else int(.8*H)
		flags = pygame.FULLSCREEN if fullscreen else 0
		screen = pygame.display.set_mode((width, height), flags)
		pygame.display.set_caption("PyMuse")

		# Main loop
		running = True
		clock = pygame.time.Clock()
		event_handler = EventHandler()

		while running:
			for event in pygame.event.get():
				running = event_handler.handle_event(event)

			screen.fill((0, 0, 0))

			pygame.display.flip()
			clock.tick(60)

		pygame.quit()
		return True
	except pygame.error as e:
		print(f"{indent}SDL error: {e}")
		pygame.quit()
		return False
