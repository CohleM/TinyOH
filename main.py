from .edit import Editor

sample_code = '''with tempfile.NamedTemporaryFile(delete=False) as temp_file:
    temp_file.write(b"Persistent content")
    print("Persistent file name:", temp_file.name)

# The file remains even after the program ends.
'''
new_code = '''This is like a really nice thing man
woooo and this is enormous thing hahaha
'''
if __name__=='__main__':
    e = Editor()
    # e(command='insert', path='/Users/cohlem/Projects/Experimentation/TinyOH/sample.py', new_str=sample_code, insert_line=10)

    e(command='str_replace', path='/Users/cohlem/Projects/Experimentation/TinyOH/sample.py', old_str=sample_code, new_str=new_code)
    e(command='view', path='/Users/cohlem/Projects/Experimentation/TinyOH/sample.py', view_range=[0,30])