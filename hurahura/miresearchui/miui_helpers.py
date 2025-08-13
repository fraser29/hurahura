#!/usr/bin/env python3

import asyncio

DEBUG = True


# ==========================================================================================
# HELPER FUNCTIONS  
# ==========================================================================================

async def cleanup():
    # Clean up any remaining tasks, close any event loops
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop = asyncio.get_event_loop()
    if not loop.is_closed():
        loop.close()


def get_index_of_field_open(data):
    for index, dictionary in enumerate(data):
        if dictionary.get('field') == 'open':
            return index
    return -1  # Return -1 if no dictionary with field 'open' is found
