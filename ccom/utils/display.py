#!/usr/bin/env python3
"""
Centralized display and output formatting utilities
Eliminates code duplication for consistent user interface
"""

import sys
from typing import Optional, List, Dict, Any
from datetime import datetime


class Display:
    """
    Centralized output formatting

    Replaces 20+ similar print formatting patterns across CCOM modules
    """

    # ANSI color codes for terminal output
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m'
    }

    @classmethod
    def _colorize(cls, text: str, color: str) -> str:
        """Add color to text if terminal supports it"""
        if sys.stdout.isatty():
            return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['RESET']}"
        return text

    @classmethod
    def success(cls, message: str, prefix: str = "✅"):
        """Display success message"""
        print(f"{prefix} {cls._colorize(message, 'GREEN')}")

    @classmethod
    def error(cls, message: str, prefix: str = "❌"):
        """Display error message"""
        print(f"{prefix} {cls._colorize(message, 'RED')}")

    @classmethod
    def warning(cls, message: str, prefix: str = "⚠️"):
        """Display warning message"""
        print(f"{prefix} {cls._colorize(message, 'YELLOW')}")

    @classmethod
    def info(cls, message: str, prefix: str = "ℹ️"):
        """Display info message"""
        print(f"{prefix} {cls._colorize(message, 'BLUE')}")

    @classmethod
    def progress(cls, message: str, prefix: str = "🔄"):
        """Display progress message"""
        print(f"{prefix} {cls._colorize(message, 'CYAN')}")

    @classmethod
    def header(cls, title: str, width: int = 60, char: str = "="):
        """Display section header"""
        print()
        print(cls._colorize(char * width, 'BOLD'))
        print(cls._colorize(f" {title} ".center(width), 'BOLD'))
        print(cls._colorize(char * width, 'BOLD'))

    @classmethod
    def section(cls, title: str, width: int = 50, char: str = "-"):
        """Display subsection header"""
        print()
        print(cls._colorize(f"{title}", 'BOLD'))
        print(cls._colorize(char * len(title), 'BLUE'))

    @classmethod
    def bullet_list(cls, items: List[str], bullet: str = "  •"):
        """Display bulleted list"""
        for item in items:
            print(f"{bullet} {item}")

    @classmethod
    def numbered_list(cls, items: List[str]):
        """Display numbered list"""
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")

    @classmethod
    def key_value_table(cls, data: Dict[str, Any], indent: str = "  "):
        """Display key-value pairs in table format"""
        max_key_length = max(len(str(key)) for key in data.keys()) if data else 0

        for key, value in data.items():
            key_str = str(key).ljust(max_key_length)
            print(f"{indent}{cls._colorize(key_str, 'CYAN')}: {value}")

    @classmethod
    def status_line(cls, status: str, message: str, width: int = 50):
        """Display status line with alignment"""
        status_colored = cls._colorize(status, 'GREEN' if 'SUCCESS' in status.upper() else 'RED')
        dots = '.' * (width - len(status) - len(message))
        print(f"{message} {dots} {status_colored}")

    @classmethod
    def progress_bar(cls, current: int, total: int, width: int = 50, prefix: str = "Progress"):
        """Display simple progress bar"""
        if total == 0:
            percent = 0
        else:
            percent = (current / total) * 100

        filled_width = int(width * current // total) if total > 0 else 0
        bar = '█' * filled_width + '░' * (width - filled_width)

        print(f"\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})", end='', flush=True)

        if current >= total:
            print()  # New line when complete

    @classmethod
    def timestamp(cls, message: str, format_str: str = "%H:%M:%S"):
        """Display message with timestamp"""
        time_str = datetime.now().strftime(format_str)
        print(f"[{cls._colorize(time_str, 'PURPLE')}] {message}")

    @classmethod
    def ccom_banner(cls, version: str = "5.0"):
        """Display CCOM banner"""
        banner = f"""
🚀 CCOM v{version} - Claude Code Orchestrator and Memory

🎯 Enterprise automation and quality enforcement
"""
        print(cls._colorize(banner, 'CYAN'))

    @classmethod
    def workflow_start(cls, workflow_name: str):
        """Display workflow start message"""
        cls.header(f"🤖 CCOM {workflow_name.upper()}")
        cls.timestamp(f"Starting {workflow_name} workflow")

    @classmethod
    def workflow_complete(cls, workflow_name: str, success: bool = True):
        """Display workflow completion message"""
        if success:
            cls.success(f"✅ **{workflow_name.upper()} COMPLETE**")
        else:
            cls.error(f"❌ **{workflow_name.upper()} FAILED**")

    @classmethod
    def agent_execution(cls, agent_name: str, mode: str = "SDK"):
        """Display agent execution message"""
        mode_icon = "🤖" if mode == "SDK" else "📄"
        print(f"{mode_icon} **CCOM {agent_name.upper()}** ({mode} mode)")

    @classmethod
    def metrics_table(cls, metrics: Dict[str, Any], title: str = "Metrics"):
        """Display metrics in formatted table"""
        cls.section(f"📊 {title}")

        for category, values in metrics.items():
            if isinstance(values, dict):
                print(f"\n{cls._colorize(category, 'BOLD')}:")
                cls.key_value_table(values, indent="  ")
            else:
                print(f"  {category}: {values}")

    @classmethod
    def file_list(cls, files: List[str], title: str = "Files", max_display: int = 10):
        """Display list of files with optional truncation"""
        cls.section(f"📁 {title}")

        display_files = files[:max_display]
        for file_path in display_files:
            print(f"  📄 {file_path}")

        if len(files) > max_display:
            remaining = len(files) - max_display
            print(f"  ... and {remaining} more files")

    @classmethod
    def command_help(cls, commands: Dict[str, str], title: str = "Available Commands"):
        """Display command help in formatted way"""
        cls.section(title)

        max_cmd_length = max(len(cmd) for cmd in commands.keys()) if commands else 0

        for command, description in commands.items():
            cmd_str = cls._colorize(command.ljust(max_cmd_length), 'CYAN')
            print(f"  {cmd_str} → {description}")

    @classmethod
    def clear_line(cls):
        """Clear current line (useful for progress updates)"""
        print('\r' + ' ' * 80 + '\r', end='', flush=True)