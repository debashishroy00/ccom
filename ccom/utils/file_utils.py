#!/usr/bin/env python3
"""
Centralized file and path utilities
Eliminates code duplication for file operations
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import logging


class FileUtils:
    """
    Centralized file operations

    Replaces 8+ duplicate file handling implementations across CCOM modules
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if necessary

        Args:
            path: Directory path

        Returns:
            Path object
        """
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    @staticmethod
    def safe_read_json(file_path: Union[str, Path], default: Any = None) -> Any:
        """
        Safely read JSON file with default fallback

        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist or is invalid

        Returns:
            Parsed JSON data or default value
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default

    @staticmethod
    def safe_write_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
        """
        Safely write JSON file with error handling

        Args:
            file_path: Path to JSON file
            data: Data to write
            indent: JSON indentation

        Returns:
            True if successful, False otherwise
        """
        try:
            path_obj = Path(file_path)
            FileUtils.ensure_directory(path_obj.parent)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except (OSError, TypeError):
            return False

    @staticmethod
    def safe_read_text(file_path: Union[str, Path], default: str = "") -> str:
        """
        Safely read text file with default fallback

        Args:
            file_path: Path to text file
            default: Default value if file doesn't exist

        Returns:
            File content or default value
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except (FileNotFoundError, OSError):
            return default

    @staticmethod
    def safe_write_text(file_path: Union[str, Path], content: str) -> bool:
        """
        Safely write text file with error handling

        Args:
            file_path: Path to text file
            content: Content to write

        Returns:
            True if successful, False otherwise
        """
        try:
            path_obj = Path(file_path)
            FileUtils.ensure_directory(path_obj.parent)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except OSError:
            return False

    @staticmethod
    def find_project_root(start_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
        """
        Find project root by looking for common project files

        Args:
            start_path: Starting directory (defaults to current)

        Returns:
            Project root path or None if not found
        """
        current = Path(start_path) if start_path else Path.cwd()

        # Look for common project indicators
        indicators = [
            'package.json',
            'pyproject.toml',
            'setup.py',
            '.git',
            'Cargo.toml',
            'go.mod'
        ]

        while current != current.parent:
            for indicator in indicators:
                if (current / indicator).exists():
                    return current
            current = current.parent

        return None

    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get comprehensive file information

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            return {
                'exists': False,
                'size': 0,
                'lines': 0,
                'extension': path_obj.suffix,
                'name': path_obj.name
            }

        try:
            stat = path_obj.stat()
            lines = 0

            if path_obj.is_file() and path_obj.suffix in ['.py', '.js', '.ts', '.md', '.txt']:
                try:
                    with open(path_obj, 'r', encoding='utf-8', errors='replace') as f:
                        lines = sum(1 for _ in f)
                except:
                    lines = 0

            return {
                'exists': True,
                'size': stat.st_size,
                'lines': lines,
                'extension': path_obj.suffix,
                'name': path_obj.name,
                'modified': stat.st_mtime,
                'is_file': path_obj.is_file(),
                'is_dir': path_obj.is_dir()
            }
        except OSError:
            return {
                'exists': True,
                'size': 0,
                'lines': 0,
                'extension': path_obj.suffix,
                'name': path_obj.name,
                'error': 'Cannot access file stats'
            }

    @staticmethod
    def list_python_files(directory: Union[str, Path], exclude_patterns: Optional[List[str]] = None) -> List[Path]:
        """
        List all Python files in directory recursively

        Args:
            directory: Directory to search
            exclude_patterns: Patterns to exclude (e.g., ['__pycache__', '.git'])

        Returns:
            List of Python file paths
        """
        exclude_patterns = exclude_patterns or ['__pycache__', '.git', 'node_modules', '.venv', 'venv']
        directory = Path(directory)
        python_files = []

        for py_file in directory.rglob('*.py'):
            # Check if file should be excluded
            excluded = any(pattern in str(py_file) for pattern in exclude_patterns)
            if not excluded:
                python_files.append(py_file)

        return sorted(python_files)

    @staticmethod
    def cleanup_temp_files(directory: Union[str, Path], patterns: List[str] = None) -> int:
        """
        Clean up temporary files in directory

        Args:
            directory: Directory to clean
            patterns: File patterns to remove

        Returns:
            Number of files removed
        """
        patterns = patterns or ['*.tmp', '*.temp', '*~', '*.bak']
        directory = Path(directory)
        removed = 0

        for pattern in patterns:
            for temp_file in directory.rglob(pattern):
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                        removed += 1
                except OSError:
                    continue

        return removed

    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_suffix: str = '.backup') -> Optional[Path]:
        """
        Create backup of file

        Args:
            file_path: File to backup
            backup_suffix: Suffix for backup file

        Returns:
            Path to backup file or None if failed
        """
        try:
            source = Path(file_path)
            if not source.exists():
                return None

            backup_path = source.with_suffix(source.suffix + backup_suffix)

            import shutil
            shutil.copy2(source, backup_path)
            return backup_path
        except OSError:
            return None

    @staticmethod
    def get_relative_path(file_path: Union[str, Path], base_path: Union[str, Path]) -> str:
        """
        Get relative path from base

        Args:
            file_path: Target file path
            base_path: Base directory path

        Returns:
            Relative path string
        """
        try:
            return str(Path(file_path).relative_to(Path(base_path)))
        except ValueError:
            return str(file_path)