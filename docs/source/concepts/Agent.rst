*****
Agent
*****

This file describes how to use Agent objects.


Agent State
===========

An Agent's state can be one of the following:

:START: Agent is initialized.
:IDLE: No tool is staged and Agent is waiting for input.
:TOOL_STAGED: Agent has staged a tool for execution.
:STOP: If ``task_complete`` is executed.

Initialize Agent
================

An agent can be initialized using

.. code-block:: python

    import loopgpt
    agent = loopgpt.Agent()

See :class:`loopgpt.Agent <loopgpt.agent.Agent>` to see how to configure the agent.

Goals and Constraints
=====================

You can set goals and constraints for the Agent by simply updating the corresponding lists:

.. code-block:: python

    agent.goals = [...]
    agent.constraints = [...]

Chat with Agent
===============

:meth:`agent.chat` deals with sending prompts to the agent and executing commands. It returns the Agent's response (see [loopgpt/constants.py](https://github.com/farizrahman4u/loopgpt/blob/main/loopgpt/constants.py) for the response format).

It takes two arguments:

:message: Optional[str]: The message to send to the agent. Defaults to ``None``.
:run_tool: bool: If specified as ``True``, any staged command will be executed. Defaults to ``False``.

Prompts
=======

There are two kinds of prompts that are attached with the ``message`` argument:

:agent.init_prompt: This prompt is sent along with the first message and in case ``message`` is ``None``.
:agent.next_prompt: This prompt is sent along with the subsequent messages.

Staged Tool
===========

The staged tool (if any), can be accessed through ``agent.staging_tool`` and the response that staged the tool is stored in ``agent.staging_response``.
You can see the name and arguments of the staged tool using ``agent.staging_tool.get("name")`` and ``agent.staging_tool.get("args")`` respectively.

To run the staged tool, just do:

.. code-block:: python

    agent.chat(run_tool=True)

The tool's response can be found at `agent.tool_response`.
