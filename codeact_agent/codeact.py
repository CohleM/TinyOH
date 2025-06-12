import json
from ..tools.bash import create_cmd_run_tool
from ..tools.str_replace_editor import create_str_replace_editor_tool
from ..tools.finish import FinishTool
from ..edit import Editor
from ..bash import BashSession
from ..exceptions import ToolError
from ..prompts.system_prompt import SYSTEM_PROMPT
from dataclasses import dataclass

from litellm import completion
from pydantic import BaseModel

class Config(BaseModel):
    model: str = "gpt-4o-mini-2024-07-18"


class Content(BaseModel):
    type: str
    text: str

class Message(BaseModel):
    role: str 
    content: list[Content]


class CodeActAgent:
    status = 'RUNNING'
    def __init__(self):
        self.history = [SYSTEM_PROMPT] # Add a system prompt here
        self.tools = [create_cmd_run_tool(), create_str_replace_editor_tool(), FinishTool]
        self.editor = Editor()
        self.bash_session = BashSession(
            work_dir='/Users/cohlem/Projects/Experimentation/TinyOH/',
            username='to' 
        )
        self.bash_session.initialize()

    def step(self):
        params = {
            **Config().dict()
        }
        # print(self.history)
        params['messages'] = self.history
        params['tools'] = self.tools
        # print('PARAMS', params)
        return completion(**params)

    def execute(self, user_message: Message):
        print(user_message.dict())
        self.history.append(user_message.dict())
        while True:
            # run when user message is triggered this function is called
            # when /finish tool is called, we break this loop
            print('running execution loop')
            response = self.step()  # out is the observation
            assistant_msg = response.choices[0].message

            # check the output of out, see if there is function call with finish tool

            if (
                hasattr(assistant_msg,'tool_calls') and
                len(assistant_msg.tool_calls) == 1 and
                assistant_msg.tool_calls[0].function.name == 'finish'
            ):
                output = json.loads(assistant_msg.tool_calls[0].function.arguments)
                print('FINISH TOOL CALLED\n', output.get('message', ''))
                #output the last message
                print('BREAKING LOOP')
                break
            else:
                
                # perform the action
                if hasattr(assistant_msg, 'tool_calls') and assistant_msg.tool_calls:
                    for tool in assistant_msg.tool_calls:
                        print('--------TOOL---------\n', tool)
                        observation = self.perform_action(tool)
                        print('performing action!!')
                        self.history.append(convert_fn_call_to_dict(tool))
                        self.history.append(observation)

                # get the observation
                # append to history
                

    def perform_action(self,tool):
        if tool.function.name == 'str_replace_editor':
            
            arguments = json.loads(tool.function.arguments)
            args = {
                'command': arguments.get('command', ''),
                'path': arguments.get('path', ''),
                'file_text': arguments.get('file_text', ''),
                'old_str': arguments.get('old_str', ''),
                'new_str': arguments.get('new_str', ''),
                'insert_line': arguments.get('insert_line', ''),
                'view_range': arguments.get('view_range', '')
            }

            try:
                result = self.editor(**args)
                result = result.success_message
            except ToolError as e:
                result = e.message
            

            print(f'---------- OBS RESULT --------', result)
            return convert_obs_to_json(result=result, tool=tool)     
        
        elif tool.function.name == 'execute_bash':
            arguments = json.loads(tool.function.arguments) 
            args = {
                'command': arguments.get('command', ''),
                'is_input': arguments.get('is_input',''),
                'timeout': arguments.get('timeout', '')
            }
            out = self.bash_session.execute(args['command'])
            result = out.to_agent_observation()
            print(f'---------- OBS RESULT --------', result)
            return convert_obs_to_json(result=result, tool=tool)


def convert_obs_to_json(result, tool):

    output = {
        'role': 'tool',
        'content': [ {'type': 'text', 'text' : result}],
        'tool_call_id': tool.id,
        'name': tool.function.name
    }
    return output
    

def convert_fn_call_to_dict(tool):
    return {
        'content' : None,
        'role' : 'assistant',
        'tool_calls' : [tool.to_dict()]
        }
    
