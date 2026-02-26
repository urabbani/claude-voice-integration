"""Terminal UI for voice client."""

import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


class UI:
    """Terminal UI for displaying recording status and results."""

    def __init__(self, config: dict):
        """Initialize UI with configuration.

        Args:
            config: Configuration dictionary with recording indicators
        """
        self.indicator = config['recording']['indicator']
        self.processing = config['recording']['processing']
        self.success = config['recording']['success']
        self.error = config['recording']['error']

    def print_recording(self, duration: float = None):
        """Print recording status with optional duration.

        Args:
            duration: Recording duration in seconds
        """
        duration_str = f" [{duration:.1f}s]" if duration else ""
        print(f"\r{self.indicator} Recording...{duration_str}", end='', flush=True)

    def print_processing(self):
        """Print processing status."""
        print(f"\r{self.processing} Transcribing...", end='', flush=True)

    def print_success(self, text: str):
        """Print successful transcription.

        Args:
            text: Transcribed text
        """
        print(f"\r{self.success} \"{Fore.GREEN}{text}{Style.RESET_ALL}\"")
        print()  # New line for readability

    def print_error(self, message: str):
        """Print error message.

        Args:
            message: Error message to display
        """
        print(f"\r{self.error} {Fore.RED}Error: {message}{Style.RESET_ALL}")
        print()

    def print_info(self, message: str):
        """Print informational message.

        Args:
            message: Message to display
        """
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

    def print_warning(self, message: str):
        """Print warning message.

        Args:
            message: Warning message to display
        """
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")

    def print_devices(self, devices: list):
        """Print available audio devices.

        Args:
            devices: List of device dictionaries
        """
        print(f"\n{Fore.CYAN}Available audio devices:{Style.RESET_ALL}")
        for device in devices:
            print(f"  [{Fore.WHITE}{device['index']}{Style.RESET_ALL}] {device['name']} ({device['channels']} channels)")
        print()

    def clear_line(self):
        """Clear current terminal line."""
        print("\r" + " " * 80 + "\r", end='', flush=True)
