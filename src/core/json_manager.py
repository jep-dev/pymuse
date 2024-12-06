import os
import json

# Load settings from settings.json
def load_settings(root):
	settings_path = os.path.join(root, "config", "settings.json")
	try:
		with open(settings_path, "r") as file:
			return json.load(file)
	except FileNotFoundError:
		print(f"Error: {settings_path} not found.")
		exit(1)
