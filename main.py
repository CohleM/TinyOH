from .edit import Editor
from .bash import BashSession
import os
new_file_text = '''I'm just testing if this 
creation of new file works or not'''


sample_code = '''from openhands.runtime.plugins import (
    JupyterRequirement,
    PluginRequirement,
    VSCodeRequirement,
)
'''
new_code = '''
YOLOOO
THIS IS REALLY COOOOOOOOLL!!!!!
'''


from .codeact_agent.codeact import Message, Content,CodeActAgent
if __name__=='__main__':
    e = Editor()
    codeact_agent = CodeActAgent()
    # out = e(command='insert', path='/Users/cohlem/Projects/Experimentation/TinyOH/sample.py', new_str=sample_code, insert_line=10)

    # out = e(command='str_replace', path='/Users/cohlem/Projects/Experimentation/TinyOH/sample.py', old_str=sample_code, new_str=new_code)

    # out =  e(command='view', path='/Users/cohlem/Projects/Experimentation/TinyOH/sample.py', view_range=[0,30])
    # out =  e(command='create', path='/Users/cohlem/Projects/Experimentation/TinyOH/new_file.py', file_text=new_file_text)


    # 
    # AGENT
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

    # AGENT

    # print(out)
    # bash = BashSession(

    #     work_dir='/Users/cohlem/Projects/Experimentation/TinyOH/',
    #     username='to' 
    #     )
    # bash.initialize()
    # bash.execute('iwha -lah')