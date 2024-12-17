from src.core.pygame_init import *
import pygame


class View:
	def __init__(self, settings):
		"""
		Initialize the View object with settings for the GUI.

		Args:
			settings (dict): A dictionary of configuration settings.
		"""
		self.settings = settings
		self.running = False
		self.screen = None
		self.clock = None
		self.width, self.height, self.flags = self._configure_window()
		self.toolbar_height = 30
		self.context_menu_items = ["Dummy Item"]
		self.context_menu_active = False
		self.context_menu_rect = pygame.Rect(0, 0, 150, 25 * len(self.context_menu_items))
		self.context_menu_position = (0, 0)

	def _configure_window(self):
		"""
		Configures the window size and flags based on settings.

		Returns:
			Tuple[int, int, int]: width, height, and flags for the window.
		"""
		fullscreen = self.settings["window"]["fullscreen"]
		info = pygame.display.Info()
		W, H = info.current_w, info.current_h
		width = self.settings["window"]["width"]
		if width == -1:
			width = W if fullscreen else int(0.8 * W)
		height = self.settings["window"]["height"]
		if height == -1:
			height = H if fullscreen else int(0.8 * H)
		flags = pygame.FULLSCREEN if fullscreen else 0
		return width, height, flags

	def start(self):
		"""Initialize and start the main GUI loop."""
		pygame.display.set_mode((self.width, self.height), self.flags)
		pygame.display.set_caption("PyMuse - Night Mode")
		self.screen = pygame.display.get_surface()
		self.clock = pygame.time.Clock()
		self.running = True
		self.main_loop()

	def stop(self):
		"""Stop the main GUI loop."""
		self.running = False

	def main_loop(self):
		"""Main GUI loop."""
		while self.running:
			self._handle_events()
			self._render()
			pygame.display.flip()
			self.clock.tick(60)
		pygame.quit()

	def _handle_events(self):
		"""Handle incoming events."""
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.stop()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 3:  # Right-click
					self.context_menu_position = event.pos
					self.context_menu_active = True
			elif event.type == pygame.MOUSEBUTTONUP:
				if event.button == 1 and self.context_menu_active:  # Left-click to dismiss context menu
					self.context_menu_active = False

	def _render(self):
		"""Render the GUI elements."""
		self.screen.fill((20, 20, 20))  # Night mode background
		self._render_toolbar()
		if self.context_menu_active:
			self._render_context_menu()

	def _render_toolbar(self):
		"""Render the toolbar."""
		pygame.draw.rect(self.screen, (40, 40, 40), (0, 0, self.width, self.toolbar_height))
		font = pygame.font.Font(None, 24)
		file_label = font.render("File", True, (200, 200, 200))
		edit_label = font.render("Edit", True, (200, 200, 200))
		self.screen.blit(file_label, (10, 5))
		self.screen.blit(edit_label, (60, 5))

	def _render_context_menu(self):
		"""Render the right-click context menu."""
		x, y = self.context_menu_position
		pygame.draw.rect(self.screen, (30, 30, 30), self.context_menu_rect.move(x, y))
		font = pygame.font.Font(None, 24)
		for i, item in enumerate(self.context_menu_items):
			item_label = font.render(item, True, (200, 200, 200))
			self.screen.blit(item_label, (x + 10, y + 5 + i * 25))
