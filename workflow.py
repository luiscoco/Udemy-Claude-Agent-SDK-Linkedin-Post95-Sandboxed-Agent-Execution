"""Lesson-specific workflow. Read this file before the execution adapter."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from runtime import atomic_json, contained_path, in_process_tool

async def run(agent, data):
    target = contained_path(agent.root, data['filename'])
    if not target.is_file() or not target.is_relative_to((agent.root / 'data').resolve()):
        raise ValueError('Only bundled data files may be inspected')
    async def gate(tool_name, arguments, context):
        from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny
        permitted = tool_name == 'Read' and Path(arguments.get('file_path', '')).resolve() == target
        return PermissionResultAllow(updated_input=arguments) if permitted else PermissionResultDeny(message='Read target is outside the exact fixture grant.')
    answer = await agent.ask('contained_read', 'Use Read only on the exact fixture. Explain the exercise without claiming cwd is a sandbox.', {'target': str(target), 'task': data['task']},
        'The application restricts its read target. Actual process isolation comes from the separately invoked container.',
        sdk={'tools': ['Read'], 'allowed_tools': [], 'can_use_tool': gate})
    return {'target': target.relative_to(agent.root).as_posix(), 'answer': answer, 'container_started_by_app': False}
