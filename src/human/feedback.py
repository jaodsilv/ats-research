"""HumanFeedback for terminal-based PDF review and feedback collection.

This module provides the HumanFeedback class for human-in-the-loop document
review during the pruning workflow. It opens PDFs in the default viewer and
collects user feedback about document length acceptability.
"""

import platform
import subprocess
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging


class HumanFeedback:
    """Handles terminal-based PDF preview and user feedback collection.

    This class provides a human-in-the-loop mechanism for document length
    verification during the pruning workflow. It:
    1. Opens PDFs in the system's default viewer
    2. Prompts for yes/no acceptance feedback
    3. Collects optional comments if document is not acceptable
    4. Returns structured feedback with timestamp

    The PDF viewer is platform-specific:
    - Windows: os.startfile()
    - macOS: subprocess.run(["open", pdf_path])
    - Linux: subprocess.run(["xdg-open", pdf_path])

    Example:
        >>> feedback_collector = HumanFeedback()
        >>> result = await feedback_collector.get_length_feedback(
        ...     Path("./output/resume_v1.pdf")
        ... )
        >>> if result["acceptable"]:
        ...     print("Document length approved!")
        >>> else:
        ...     print(f"Needs revision: {result['comments']}")
    """

    def __init__(self):
        """Initialize the HumanFeedback collector.

        Sets up logging for tracking all user feedback interactions.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("HumanFeedback collector initialized")

    async def get_length_feedback(self, pdf_path: Path) -> Dict[str, Any]:
        """Open PDF in default viewer and prompt user for length feedback.

        This method orchestrates the complete feedback collection workflow:
        1. Validates the PDF file exists
        2. Opens the PDF in the default system viewer
        3. Prompts user with yes/no question about length acceptability
        4. If not acceptable, prompts for optional comments
        5. Returns structured feedback with timestamp

        Args:
            pdf_path: Path to PDF file to review

        Returns:
            Dict with:
                - acceptable: bool - Whether user accepts the document length
                - comments: str - User comments (empty if acceptable)
                - pdf_path: str - Absolute path to reviewed PDF
                - timestamp: str - ISO format timestamp of feedback

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            RuntimeError: If PDF cannot be opened in viewer

        Example:
            >>> feedback = await collector.get_length_feedback(
            ...     Path("./resume_v1.pdf")
            ... )
            >>> print(f"Acceptable: {feedback['acceptable']}")
            >>> print(f"Comments: {feedback['comments']}")
            >>> print(f"Timestamp: {feedback['timestamp']}")
        """
        # Validate PDF exists
        if not pdf_path.exists():
            error_msg = f"PDF file not found: {pdf_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not pdf_path.is_file():
            error_msg = f"Path is not a file: {pdf_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not str(pdf_path).lower().endswith('.pdf'):
            self.logger.warning(f"File does not have .pdf extension: {pdf_path}")

        self.logger.info(f"Requesting feedback for PDF: {pdf_path}")

        # Open PDF in default viewer
        pdf_opened = self._open_pdf(pdf_path)
        if not pdf_opened:
            error_msg = f"Failed to open PDF in viewer: {pdf_path}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        self.logger.info("PDF opened successfully, awaiting user feedback")

        # Prompt for acceptance
        acceptable = self._prompt_yes_no(
            "\nIs the document length acceptable? (yes/no): "
        )

        # Collect comments if not acceptable
        comments = ""
        if not acceptable:
            comments = self._prompt_comments()

        # Build feedback result
        feedback_result = {
            "acceptable": acceptable,
            "comments": comments,
            "pdf_path": str(pdf_path.absolute()),
            "timestamp": datetime.now().isoformat()
        }

        # Log the feedback
        self.logger.info(
            f"Feedback collected - Acceptable: {acceptable}, "
            f"Comments: {'Yes' if comments else 'No'}"
        )

        return feedback_result

    def _open_pdf(self, pdf_path: Path) -> bool:
        """Open PDF in default viewer (cross-platform).

        Uses platform-specific commands to open the PDF:
        - Windows: os.startfile() (Windows-specific API)
        - macOS: subprocess.run(["open", pdf_path])
        - Linux: subprocess.run(["xdg-open", pdf_path])

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF opened successfully, False otherwise

        Example:
            >>> success = feedback._open_pdf(Path("./resume.pdf"))
            >>> if success:
            ...     print("PDF opened in viewer")
        """
        system = platform.system()
        self.logger.debug(f"Opening PDF on {system} platform: {pdf_path}")

        try:
            if system == "Windows":
                # Windows: use os.startfile()
                os.startfile(str(pdf_path))
                self.logger.debug("PDF opened using os.startfile() (Windows)")
                return True

            elif system == "Darwin":
                # macOS: use 'open' command
                result = subprocess.run(
                    ["open", str(pdf_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.logger.debug("PDF opened using 'open' command (macOS)")
                    return True
                else:
                    self.logger.error(f"'open' command failed: {result.stderr}")
                    return False

            elif system == "Linux":
                # Linux: use 'xdg-open' command
                result = subprocess.run(
                    ["xdg-open", str(pdf_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.logger.debug("PDF opened using 'xdg-open' command (Linux)")
                    return True
                else:
                    self.logger.error(f"'xdg-open' command failed: {result.stderr}")
                    return False

            else:
                # Unsupported platform
                self.logger.error(f"Unsupported platform: {system}")
                return False

        except FileNotFoundError as e:
            self.logger.error(f"PDF viewer command not found: {e}")
            return False
        except subprocess.TimeoutExpired:
            # Timeout is not necessarily an error - viewer may have opened
            self.logger.warning("PDF viewer command timed out (viewer may still have opened)")
            return True  # Assume success
        except Exception as e:
            self.logger.error(f"Error opening PDF: {e}", exc_info=True)
            return False

    def _prompt_yes_no(self, question: str) -> bool:
        """Terminal yes/no prompt with validation.

        Prompts the user with a question and accepts yes/y/no/n responses
        (case-insensitive). Repeats until valid input is received.

        Valid responses:
        - yes, y, Yes, YES -> True
        - no, n, No, NO -> False

        Args:
            question: Question to display to user

        Returns:
            True for yes, False for no

        Example:
            >>> result = feedback._prompt_yes_no("Continue? (yes/no): ")
            >>> print(f"User said: {'yes' if result else 'no'}")
        """
        valid_yes = {"yes", "y"}
        valid_no = {"no", "n"}

        while True:
            try:
                response = input(question).strip().lower()

                if response in valid_yes:
                    self.logger.debug("User responded: yes")
                    return True
                elif response in valid_no:
                    self.logger.debug("User responded: no")
                    return False
                else:
                    print("Invalid response. Please enter 'yes' or 'no'.")
                    self.logger.debug(f"Invalid response received: {response}")

            except EOFError:
                # Handle Ctrl+D or pipe input ending
                self.logger.warning("EOF encountered, defaulting to 'no'")
                return False
            except KeyboardInterrupt:
                # Handle Ctrl+C
                self.logger.warning("User interrupted input, defaulting to 'no'")
                print("\nInput interrupted. Defaulting to 'no'.")
                return False

    def _prompt_comments(self) -> str:
        """Optional comments prompt.

        Prompts the user to provide optional comments about why the document
        length is not acceptable. User can press Enter to skip.

        Returns:
            User input string (may be empty)

        Example:
            >>> comments = feedback._prompt_comments()
            >>> if comments:
            ...     print(f"User comments: {comments}")
        """
        try:
            print("\nPlease provide comments on what needs to change (press Enter to skip):")
            comments = input("> ").strip()

            if comments:
                self.logger.debug(f"User provided comments ({len(comments)} chars)")
            else:
                self.logger.debug("User skipped comments")

            return comments

        except EOFError:
            self.logger.warning("EOF encountered during comments prompt")
            return ""
        except KeyboardInterrupt:
            self.logger.warning("User interrupted comments input")
            print("\nComments skipped.")
            return ""
