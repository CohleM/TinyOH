from .runtime.edit import Editor
from .runtime.bash import BashSession
import os

from .codeact_agent.codeact import Message, Content,CodeActAgent
if __name__=='__main__':
    codeact_agent = CodeActAgent()
    
    try:
        while True:
            print('Enter Instructions:\n')
            instruction = input()

            content = Content(type='text', text=instruction) 
            user_message = Message(content=[content], role='user')
            
            cwd = os.getcwd() 
            user_message.content[0].text += f'\n present working directory: /Users/cohlem/Projects/Experimentation/TinyOH/'

            codeact_agent.execute(user_message=user_message)
    except KeyboardInterrupt:
        print('-----Stopping agent!!!------')

