import libtmux
import time
import re
import json
import traceback
from pydantic import BaseModel
from typing import Tuple

HARD_TIMEOUT=300
CMD_OUTPUT_PS1_BEGIN = '\n###PS1JSON###\n'
CMD_OUTPUT_PS1_END = '\n###PS1END###'
CMD_OUTPUT_METADATA_PS1_REGEX = re.compile(
    f'^{CMD_OUTPUT_PS1_BEGIN.strip()}(.*?){CMD_OUTPUT_PS1_END.strip()}',
    re.DOTALL | re.MULTILINE,
)





class CmdOutputMetadata(BaseModel):
    """Additional metadata captured from PS1"""

    exit_code: int = -1
    pid: int = -1
    username: str | None = None
    hostname: str | None = None
    working_dir: str | None = None
    py_interpreter_path: str | None = None
    prefix: str = ''  # Prefix to add to command output
    suffix: str = ''  # Suffix to add to command output

    @classmethod
    def to_ps1_prompt(cls) -> str:
        """Convert the required metadata into a PS1 prompt."""
        prompt = CMD_OUTPUT_PS1_BEGIN
        json_str = json.dumps(
            {
                'pid': '$!',
                'exit_code': '$?',
                'username': r'\u',
                'hostname': r'\h',
                'working_dir': r'$(pwd)',
                'py_interpreter_path': r'$(which python 2>/dev/null || echo "")',
            },
            indent=2,
        )
        # Make sure we escape double quotes in the JSON string
        # So that PS1 will keep them as part of the output
        prompt += json_str.replace('"', r'\"')
        prompt += CMD_OUTPUT_PS1_END + '\n'  # Ensure there's a newline at the end
        return prompt
    @classmethod
    def matches_ps1_metadata(cls, string: str) -> list[re.Match[str]]:
        matches = []
        matched_json = []
        for match in CMD_OUTPUT_METADATA_PS1_REGEX.finditer(string):
            try:
                matched = json.loads(match.group(1).strip())  # Try to parse as JSON
                # print('matchedddd ', matched)
                matches.append(match)
                matched_json.append(matched)
            except json.JSONDecodeError:
                print(
                    f'Failed to parse PS1 metadata: {match.group(1)}. Skipping.'
                    + traceback.format_exc()
                )
                continue  # Skip if not valid JSON
        return matches, matched_json


class CmdOutputObservation(BaseModel):
    metadata: CmdOutputMetadata
    content: str

    def to_agent_observation(self) -> str:
        ret =  f'<RESULT>{self.content}</RESULT>'
        if self.metadata.working_dir:
            ret += f'\n[Current working directory {self.metadata.working_dir}]'
        if self.metadata.py_interpreter_path:
            ret += f'\n[Current python interpreter path {self.metadata.py_interpreter_path}]'
        if self.metadata.exit_code:
            ret += f'\n[Command finished with exit code {self.metadata.exit_code}]'

        return ret
        

class BashSession:
    PS1 = CmdOutputMetadata.to_ps1_prompt()
    HISTORY_LIMIT = 10_000
    def __init__(self, work_dir: str, username: str):
        self.work_dir = work_dir
        self.username = username
        self.server = libtmux.Server()
        
    def initialize(self ):
        session_name = 'tinyoh'
        self.session = self.server.new_session(
            session_name=session_name,
            start_directory=self.work_dir,  # This parameter is supported by libtmux
            kill_session=True,
            x=1000,
            y=1000,
        )

        # _shell_command = f'su {self.username} -'
        _shell_command = '/bin/bash'
        window_command = _shell_command
        self.session.set_option('history-limit', str(self.HISTORY_LIMIT))
        self.session.history_limit = self.HISTORY_LIMIT
        # We need to create a new pane because the initial pane's history limit is (default) 2000
        _initial_window = self.session.active_window
        self.window = self.session.new_window(
            window_name='bash',
            window_shell=window_command,
            start_directory=self.work_dir,  # This parameter is supported by libtmux
        )
        self.pane = self.window.active_pane
        # logger.debug(f'pane: {self.pane}; history_limit: {self.session.history_limit}')
        _initial_window.kill_window()
                     
   
        # Configure bash to use simple PS1 and disable PS2
        self.pane.send_keys(
            f'export PROMPT_COMMAND=\'export PS1="{self.PS1}"\'; export PS2=""'
        )
        time.sleep(0.1)  # Wait for command to take effect
        self._clear_screen()

    def _clear_screen(self) -> None:
        """Clear the tmux pane screen and history."""
        self.pane.send_keys('C-l', enter=False)
        time.sleep(0.1)
        self.pane.cmd('clear-history')

    def _get_pane_content(self) -> str:
        """Capture the current pane content and update the buffer."""
        content = '\n'.join(
            map(
                # avoid double newlines
                lambda line: line.rstrip(),
                self.pane.cmd('capture-pane', '-J', '-pS', '-').stdout,
            )
        )
        return content

    def execute(
            self,
            command: str
    ):
        init_content = self._get_pane_content()
        init_output,_ = CmdOutputMetadata.matches_ps1_metadata(init_content)
        init_match_count = len(init_output)

        start_time = time.time()
        end_time = start_time


        self.pane.send_keys(command)
        time.sleep(0.5)

        # out = self._get_pane_content()
        # ps1_matches = CmdOutputMetadata.matches_ps1_metadata(out)
        # combined_output, combined_output_segment = (self._combine_outputs_between_matches(pane_content=out, ps1_matches=ps1_matches))
        # print(combined_output_segment[-1:])

        # Check if the command is still executing, 
        while end_time - start_time < HARD_TIMEOUT:
            out = self._get_pane_content()
            ps1_matches,ps1_matches_json = CmdOutputMetadata.matches_ps1_metadata(out)
            cur_ps1_matches_len = len(ps1_matches)
            # print(cur_ps1_matches_len, init_match_count)
            if cur_ps1_matches_len == init_match_count+1:
                combined_output, combined_output_segment = (self._combine_outputs_between_matches(pane_content=out, ps1_matches=ps1_matches))
                final_output = ''.join(combined_output_segment)

                out = CmdOutputObservation(content=final_output,metadata=CmdOutputMetadata(**ps1_matches_json[-1])) 
                # print('final output', out.to_agent_observation())
                return out
        
            time.sleep(0.5)
        
        return CmdOutputObservation(
            content='Command has not finished executing, maybe its stuck',
            metadata=CmdOutputMetadata(**ps1_matches_json[-1]) 
            ) 


    def _combine_outputs_between_matches(
        self,
        pane_content: str,
        ps1_matches: list[re.Match],
        get_content_before_last_match: bool = False,
    ) -> Tuple[str, list[str]]:
        """Combine all outputs between PS1 matches.

        Args:
            pane_content: The full pane content containing PS1 prompts and command outputs
            ps1_matches: List of regex matches for PS1 prompts
            get_content_before_last_match: when there's only one PS1 match, whether to get
                the content before the last PS1 prompt (True) or after the last PS1 prompt (False)
        Returns:
            Combined string of all outputs between matches
        """
        combined_output_segment = []
        if len(ps1_matches) == 1:
            if get_content_before_last_match:
                # The command output is the content before the last PS1 prompt
                return pane_content[: ps1_matches[0].start()]
            else:
                # The command output is the content after the last PS1 prompt
                return pane_content[ps1_matches[0].end() + 1 :]
        elif len(ps1_matches) == 0:
            return pane_content
        combined_output = ''
        for i in range(len(ps1_matches) - 1):
            # Extract content between current and next PS1 prompt
            output_segment = pane_content[
                ps1_matches[i].end() + 1 : ps1_matches[i + 1].start()
            ]
            combined_output += output_segment + '\n'
            combined_output_segment.append(output_segment)
        # Add the content after the last PS1 prompt
        combined_output += pane_content[ps1_matches[-1].end() + 1 :]
        # logger.debug(f'COMBINED OUTPUT: {combined_output}')
        return combined_output, combined_output_segment