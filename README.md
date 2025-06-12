Trying to replicate tiny open hand [CodeActAgent](https://github.com/All-Hands-AI/OpenHands.git)

## What is the repo?

It's my attempt at reproducing OpenHand's CodeActAgent. It throws away all the complexity such as Controller, EventStream, Runtime UIs and many other thing, keeping only what's cruical to the CodeActAgent, which means it is not complete and breaks most of time, but still works, thus it's called TinyOpenHands (TinyOH).
Most of the code is from the Open Hands repo itself.

## What did I learn from this?

![meme](/utils/meme.webp)

Agents are almost:

- collections of carefully curated prompts.
- wrapped within try except blocks, covering almost all the edge cases

It's much like whats shown in the meme, instead inplace of AI it's the agent, it's almost running code within try except blocks and passing the result to the LLM, and expecting LLM to fix it, with the help of available tool (aka prompts in disguise)

## How do i run this project?

just run the main.py file, it will ask for your instructions, enter it and see what it does with it.

```python
python main.py
```
