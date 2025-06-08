## lets you completely edit, append new code, and replace existing code with new blocks of c i
import tempfile
import shutil
import re
from typing import Literal


from pathlib import Path
from .encoding import with_encoding, EncodingManager
from .exceptions import ToolError

Command = Literal[
    'view',
    'create',
    'str_replace',
    'insert',
    'undo_edit',
]

SNIPPET_CONTEXT_WINDOW = 4

class Editor:
    def __init__(self):
        self._encoding_manager = EncodingManager()
    def __call__(
        self,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        enable_linting: bool = False,
        **kwargs,

    ):
        # let's only implement view, create and insert for now
        _path = Path(path) 
        if command == 'view':
            start_line, end_line = view_range
            self.read_file(_path, start_line, end_line)
        elif command ==  'insert':
            self.insert(_path, insert_line, new_str)
        elif command == 'str_replace':
            self.str_replace(_path, new_str=new_str, old_str=old_str, enable_linting=False)

    @with_encoding
    def _count_lines(self, path: Path, encoding: str = 'utf-8') -> int:
        """
        Count the number of lines in a file safely.

        Args:
            path: Path to the file
            encoding: The encoding to use when reading the file (auto-detected by decorator)

        Returns:
            The number of lines in the file
        """
        with open(path, encoding=encoding) as f:
            return sum(1 for _ in f)
        
    @with_encoding
    def read_file(self, path: Path, start_line: int | None=None, end_line: int | None=None, encoding='utf-8'):
        """ Read within the view_range"""
        try:
            if start_line is not None and end_line is not None:

                with open(path, 'r', encoding=encoding) as f:
                    text = []
                    for i,line in enumerate(f,1):
                        if i >= start_line:
                            text.append(line)
                        if i > end_line:
                            break
                            
                print(''.join(text))
                return ''.join(text) 
            else:
                with open(path, 'r', encoding=encoding) as f:
                    return ''.join(f)
                    

        except Exception as e:
            raise ToolError(f'Error {e} ')

    @with_encoding
    def insert(self, path: Path, insert_line: int, new_str: str, encoding='utf-8'):
        # tot_len =  self._count_lines(path)
        try:

            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding=encoding,
                delete=False
                ) as temp_file:
                with open(path, 'r', encoding=encoding) as f:
                    for i, line in enumerate(f, 1):
                        if i < insert_line:
                            temp_file.write(line)
                        if i > insert_line:
                            break
                    
                new_str_ls = new_str.split('\n')
                for line in new_str_ls:
                    temp_file.write(line + '\n')
                
                with open(path, 'r', encoding=encoding) as f:
                    for i, line in enumerate(f, 1):
                        if i >= insert_line:
                            temp_file.write(line)

                shutil.move(temp_file.name, path)

        except Exception as e:
            raise ToolError(f'Error {e}')
        

    @with_encoding
    def str_replace(
        self,
        path: Path,
        old_str: str,
        new_str: str | None,
        enable_linting: bool,
        encoding: str = 'utf-8',
    ):
        """
        Implement the str_replace command, which replaces old_str with new_str in the file content.

        Args:
            path: Path to the file
            old_str: String to replace
            new_str: Replacement string
            enable_linting: Whether to run linting on the changes
            encoding: The encoding to use (auto-detected by decorator)
        """
        # self.validate_file(path)
        new_str = new_str or ''

        # Read the entire file first to handle both single-line and multi-line replacements
        file_content = self.read_file(path)

        # Find all occurrences using regex
        # Escape special regex characters in old_str to match it literally
        pattern = re.escape(old_str)
        occurrences = [
            (
                file_content.count('\n', 0, match.start()) + 1,  # line number
                match.group(),  # matched text
                match.start(),  # start position
            )
            for match in re.finditer(pattern, file_content)
        ]

        if not occurrences:
            raise ToolError(
                f'No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}.'
            )
        if len(occurrences) > 1:
            line_numbers = sorted(set(line for line, _, _ in occurrences))
            raise ToolError(
                f'No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {line_numbers}. Please ensure it is unique.'
            )

        # We found exactly one occurrence
        replacement_line, matched_text, idx = occurrences[0]

        # Create new content by replacing just the matched text
        new_file_content = (
            file_content[:idx] + new_str + file_content[idx + len(matched_text) :]
        )

        # Write the new content to the file
        self.write_file(path, new_file_content)

    @with_encoding
    def write_file(self, path: Path, file_text: str, encoding: str = 'utf-8') -> None:
        """
        Write the content of a file to a given path; raise a ToolError if an error occurs.

        Args:
            path: Path to the file to write
            file_text: Content to write to the file
            encoding: The encoding to use when writing the file (auto-detected by decorator)
        """
        # self.validate_file(path)
        try:
            # Use open with encoding instead of path.write_text
            with open(path, 'w', encoding=encoding) as f:
                f.write(file_text)
        except Exception as e:
            raise ToolError(f'Ran into {e} while trying to write to {path}') from None

