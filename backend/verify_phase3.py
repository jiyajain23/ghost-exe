"""Opt-in local Gemma smoke/latency check; uses an isolated temporary save."""
import asyncio
import logging
import os
from pathlib import Path
import statistics
import tempfile
import time

from app.config import Settings
from app.director.game import Director
from app.ghost.adapter import GhostContext, MockGhostAdapter
from app.ghost.ollama import OllamaGhostAdapter
from app.storage.repository import Repository


async def main():
    if os.getenv('GHOST_DEV_DIAGNOSTICS') == '1':
        logging.basicConfig(level=logging.INFO)
    timings = []
    rejected = 0
    with tempfile.TemporaryDirectory() as directory:
        director = Director(Repository(Path(directory) / 'verify.sqlite3'),
                            OllamaGhostAdapter(Settings(agent_mode='ollama')))
        run = director.start(None).run_id
        director.open_file(run, 'F03')
        director.open_file(run, 'F04')
        for question in ['Why is the clock frozen at 23:17?', 'What happened to Ada?', 'What can I read next?', 'Hello HELPER.', 'Where are the logs?']:
            start = time.perf_counter()
            reply = await director.chat(run, question)
            elapsed = time.perf_counter() - start
            timings.append(elapsed)
            rejected += reply.fallback
            mock = await MockGhostAdapter().reply(question, GhostContext())
            print(f'{question}\n  Gemma ({elapsed:.2f}s; fallback={reply.fallback}): {reply.reply}\n  Mock: {mock.say}', flush=True)
        print(f'Mean: {statistics.mean(timings):.2f}s; fallbacks: {rejected}/{len(timings)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
