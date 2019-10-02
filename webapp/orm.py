''' Abstraction to access database '''
import asyncio
import functools

import yaml

import asyncpg

sql_statements = yaml.safe_load(open("init.sql"))

conn = None

stored_procedures = {}

async def initialize():
    global conn
    print("Connecting to database...")
    # Connect to the database
    conn = await asyncpg.connect()
    # Set up tables and stored procedures, if they don't exist.
    await conn.execute(sql_statements['init'])

    # Set up stored procedures
    for stored_procedure in sql_statements['stored_procedures']:
        stored_procedures[stored_procedure] = \
            await conn.prepare(sql_statements['stored_procedures'][stored_procedure])
    print("Connected...")

asyncio.get_event_loop().run_until_complete(initialize())

# TODO: This should be done with a decorator, rather than cut-and-paste
def fetch_writing_deltas(username, docstring):
    return stored_procedures['fetch_writing_deltas'].cursor(username, docstring)

async def insert_writing_delta (username, docstring, ty, si, ei, ibi, s, ft):
    rv = await stored_procedures['insert_writing_delta'].fetchval(username, docstring, ty, si, ei, ibi, s, ft)
    return rv
    
if __name__ == '__main__':
    async def test():
        print(await insert_writing_delta ("pmitros", "doc", "ts", 5, 7, 2, "hel", "lo"))
        async with conn.transaction():
            cursor = fetch_writing_deltas("pmitros", "doc")
            async for record in cursor:
                print (record)
        
    asyncio.get_event_loop().run_until_complete(test())
