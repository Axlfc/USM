import os


class BaseService:
    def print_colored(self, text: str, color: str):
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "gray": "\033[90m",
            "cyan": "\033[96m",
        }
        reset = "\033[0m"
        print(f"{colors.get(color, '')}{text}{reset}")