#!/usr/bin/env python3
"""
Centralized subprocess execution utilities
Eliminates code duplication and provides consistent error handling
"""

import os
import sys
import subprocess
import asyncio
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path


class SubprocessRunner:
    """
    Centralized subprocess execution with proper encoding and error handling

    Replaces 5+ duplicate implementations across CCOM modules
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _configure_windows_encoding(kwargs):
        """Configure proper encoding for Windows"""
        if sys.platform == "win32":
            kwargs.setdefault('encoding', 'utf-8')
            kwargs.setdefault('errors', 'replace')
        return kwargs

    def run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        timeout: int = 60,
        shell: bool = False,
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run command synchronously with proper error handling

        Args:
            cmd: Command to execute
            cwd: Working directory
            timeout: Timeout in seconds
            shell: Whether to use shell
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess with results
        """
        kwargs = {
            'timeout': timeout,
            'shell': shell,
            'cwd': str(cwd) if cwd else None
        }

        if capture_output:
            kwargs.update({
                'capture_output': True,
                'text': True
            })

        kwargs = self._configure_windows_encoding(kwargs)

        try:
            if isinstance(cmd, str) and not shell:
                # Split string command if shell=False
                import shlex
                cmd = shlex.split(cmd)

            self.logger.debug(f"Running command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
            result = subprocess.run(cmd, **kwargs)

            self.logger.debug(f"Command completed with return code: {result.returncode}")
            return result

        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Command timed out after {timeout}s: {cmd}")
            raise
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            raise

    async def run_command_async(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """
        Run command asynchronously

        Args:
            cmd: Command to execute
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            CompletedProcess with results
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return subprocess.CompletedProcess(
                cmd,
                process.returncode,
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace')
            )

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")

    def run_npm_command(
        self,
        script: str,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
        timeout: int = 120
    ) -> subprocess.CompletedProcess:
        """
        Run npm command with proper error handling

        Args:
            script: npm script name (e.g., 'lint', 'build')
            args: Additional arguments
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            CompletedProcess with results
        """
        cmd = ['npm', 'run', script]
        if args:
            cmd.extend(['--'] + args)

        return self.run_command(cmd, cwd=cwd, timeout=timeout, shell=True)

    def run_python_command(
        self,
        script_args: List[str],
        cwd: Optional[Path] = None,
        timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """
        Run Python command with proper error handling

        Args:
            script_args: Python script and arguments
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            CompletedProcess with results
        """
        cmd = [sys.executable] + script_args
        return self.run_command(cmd, cwd=cwd, timeout=timeout)

    def check_command_exists(self, command: str) -> bool:
        """
        Check if a command exists in PATH

        Args:
            command: Command to check

        Returns:
            True if command exists, False otherwise
        """
        try:
            result = self.run_command(
                ['which', command] if sys.platform != 'win32' else ['where', command],
                capture_output=True,
                shell=True
            )
            return result.returncode == 0
        except:
            return False

    def get_git_info(self, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """
        Get git repository information

        Args:
            cwd: Working directory

        Returns:
            Dictionary with git information
        """
        info = {
            'is_git_repo': False,
            'branch': None,
            'commit': None,
            'status': None
        }

        try:
            # Check if it's a git repo
            result = self.run_command(['git', 'rev-parse', '--git-dir'], cwd=cwd)
            if result.returncode == 0:
                info['is_git_repo'] = True

                # Get branch
                result = self.run_command(['git', 'branch', '--show-current'], cwd=cwd)
                if result.returncode == 0:
                    info['branch'] = result.stdout.strip()

                # Get commit
                result = self.run_command(['git', 'rev-parse', 'HEAD'], cwd=cwd)
                if result.returncode == 0:
                    info['commit'] = result.stdout.strip()[:8]

                # Get status
                result = self.run_command(['git', 'status', '--porcelain'], cwd=cwd)
                if result.returncode == 0:
                    info['status'] = 'clean' if not result.stdout.strip() else 'dirty'

        except Exception as e:
            self.logger.debug(f"Git info collection failed: {e}")

        return info