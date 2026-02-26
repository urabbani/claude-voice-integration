"""Global hotkey management using pynput."""

from pynput import keyboard
import threading
from typing import Callable, Optional, Tuple


class HotkeyManager:
    """Manage global hotkey for recording toggle."""

    def __init__(self, hotkey_str: str):
        """Initialize the hotkey manager.

        Args:
            hotkey_str: Hotkey string like 'ctrl+shift+v'
        """
        self.hotkey_str = hotkey_str
        self.listener: Optional[keyboard.Listener] = None
        self.callback: Optional[Callable] = None
        self.running = False
        self.parsed_hotkey = self._parse_hotkey(hotkey_str)
        self.pressed_keys = set()

    def _parse_hotkey(self, hotkey_str: str) -> Tuple:
        """Parse hotkey string into pynput format.

        Args:
            hotkey_str: String like 'ctrl+shift+v'

        Returns:
            Tuple of (modifier_keys, final_key)
        """
        parts = hotkey_str.lower().split('+')
        key = parts[-1]
        modifiers = parts[:-1]

        key_map = {
            'ctrl': keyboard.Key.ctrl,
            'shift': keyboard.Key.shift,
            'alt': keyboard.Key.alt,
            'cmd': keyboard.Key.cmd,
            'win': keyboard.Key.cmd,
        }

        modifiers_parsed = []
        for mod in modifiers:
            mod_key = key_map.get(mod)
            if mod_key:
                modifiers_parsed.append(mod_key)

        # Handle the final key
        if len(key) == 1:
            final_key = keyboard.KeyCode.from_char(key)
        elif hasattr(keyboard.Key, key):
            final_key = getattr(keyboard.Key, key)
        else:
            final_key = keyboard.KeyCode.from_char(key)

        return (tuple(modifiers_parsed), final_key)

    def _on_press(self, key):
        """Handle key press events.

        Args:
            key: The key that was pressed
        """
        self.pressed_keys.add(key)

        # Check if all modifiers and final key are pressed
        modifiers, final_key = self.parsed_hotkey

        if final_key in self.pressed_keys:
            # Check if all modifiers are pressed
            modifiers_pressed = all(m in self.pressed_keys for m in modifiers)

            # Also check no extra modifiers (e.g., ctrl+shift+v but not ctrl+alt+shift+v)
            extra_modifiers = any(
                k in self.pressed_keys and k not in modifiers and k != final_key
                for k in [keyboard.Key.ctrl, keyboard.Key.shift, keyboard.Key.alt]
            )

            if modifiers_pressed and not extra_modifiers:
                if self.callback:
                    self.callback()

    def _on_release(self, key):
        """Handle key release events.

        Args:
            key: The key that was released
        """
        self.pressed_keys.discard(key)

    def start(self, callback: Callable):
        """Start listening for the hotkey.

        Args:
            callback: Function to call when hotkey is pressed
        """
        self.callback = callback
        self.running = True

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        """Stop listening for hotkey."""
        self.running = False
        if self.listener:
            self.listener.stop()
            try:
                self.listener.join(timeout=1)
            except:
                pass
