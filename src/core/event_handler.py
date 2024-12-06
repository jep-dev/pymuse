import pygame
import sys

class EventHandler:
	def __init__(self):
		self.is_fullscreen = False

	def handle_event(self, event):
		if event.type == pygame.QUIT:
			return False  # Exit the program
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				return False  # Exit on ESC key
			elif event.key == pygame.K_F11:
				self.toggle_fullscreen()
			elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
				# Start tracking for combinations like Ctrl+S
				self.ctrl_pressed = True
			if self.ctrl_pressed:
				if event.key == pygame.K_s:
					self.save_layout()
				elif event.key == pygame.K_o:
					self.open_layout()

		if event.type == pygame.KEYUP:
			if event.key in [pygame.K_LCTRL, pygame.K_RCTRL]:
				self.ctrl_pressed = False

		return True

	def toggle_fullscreen(self):
		self.is_fullscreen = not self.is_fullscreen
		flags = pygame.FULLSCREEN if self.is_fullscreen else 0
		pygame.display.set_mode((0, 0), flags)

	def save_layout(self):
		print("Save layout triggered (not yet implemented)")

	def open_layout(self):
		print("Open layout triggered (not yet implemented)")

