'''Key-value store

Manages JSON objects

kvs.KVS() will return a key-value store. Note that the back-end is
shared, but each

Keys are strings. Values are JSON objects.

To read objects:

'''

import asyncio
import copy
import enum
import functools
import json
import os
import os.path

import learning_observer.paths
import learning_observer.prestartup
import learning_observer.redis_connection
import learning_observer.settings
import learning_observer.util

OBJECT_STORE = dict()


class _KVS:
    async def dump(self, filename=None):
        '''
        Dumps the entire contents of the KVS to a JSON object.

        It is intended to be used in development and for debugging. It is not
        intended to be used in production, as it is not very performant. It can
        be helpful for offline analytics too, at least at a small scale.

        If `filename` is not `None`, the contents of the KVS are written to the
        file. In either case, the contents are returned as a JSON object.

        In the future, we might want to add filters, so that this is scalable
        for extracting specific data from production systems (e.g. dump data
        for one user).

        args:
            filename: The filename to write to. If `None`, don't write to a file.

        returns:
            A JSON object containing the contents of the KVS.
        '''
        data = {}
        for key in await self.keys():
            data[key] = await self[key]
        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        return data

    async def multiget(self, keys):
        '''
        Multiget. It's not fast, but it means we can use appropriate
        abstractions and make it fast later.
        '''
        return [await self[key] for key in keys]

    async def load(self, filename):
        '''
        Loads the contents of a JSON object into the KVS.

        It is intended to be used in development and for debugging. It is not
        intended to be used in production, as it is not very performant. It can
        be helpful for offline analytics too, at least at a small scale.
        '''
        with open(filename) as f:
            data = json.load(f)
        for key, value in data.items():
            await self.set(key, value)


class InMemoryKVS(_KVS):
    '''
    Stores items in-memory. Items expire on system restart.
    '''
    async def __getitem__(self, key):
        '''
        Syntax:

        >> await kvs['item']
        '''
        return copy.deepcopy(OBJECT_STORE.get(key, None))

    async def set(self, key, value):
        '''
        Syntax:
        >> await set('key', value)

        `key` is a string, and `value` is a json object.

        We can't use a setter with async, as far as I can tell. There is no

        `await kvs['item'] = foo

        So we use an explict set function.
        '''
        json.dumps(value)  # Fail early if we're not JSON
        assert isinstance(key, str), "KVS keys must be strings"
        OBJECT_STORE[key] = value

    async def keys(self):
        '''
        Returns all keys.

        Eventually, this might support wildcards.
        '''
        return list(OBJECT_STORE.keys())

    async def clear(self):
        '''
        Clear the KVS.

        This is helpful for debugging and testing. We did not want to
        implement this for the production KVS, since it would be
        too easy to accidentally lose data.
        '''
        global OBJECT_STORE
        OBJECT_STORE = dict()


class _RedisKVS(_KVS):
    '''
    Stores items in redis.
    '''
    def __init__(self, expire):
        self.expire = expire

    async def connect(self):
        '''
        asyncio_redis auto-reconnects. We can't do async in __init__. So
        we connect on the first get / set.
        '''
        await learning_observer.redis_connection.connect()

    async def __getitem__(self, key):
        '''
        Syntax:

        >> await kvs['item']
        '''
        await self.connect()
        item = await learning_observer.redis_connection.get(key)
        if item is not None:
            return json.loads(item)
        return None

    async def set(self, key, value):
        '''
        Syntax:
        >> await set('key', value)

        `key` is a string, and `value` is a json object.

        We can't use a setter with async, as far as I can tell. There is no

        `await kvs['item'] = foo

        So we use an explict set function.
        '''
        await self.connect()
        value = json.dumps(value)  # Fail early if we're not JSON
        assert isinstance(key, str), "KVS keys must be strings"
        return await learning_observer.redis_connection.set(key, value, expiry=self.expire)

    async def keys(self):
        '''
        Return all the keys in the KVS.

        This is obviously not very performant for large-scale dpeloys.
        '''
        await self.connect()
        return await learning_observer.redis_connection.keys()


class EphemeralRedisKVS(_RedisKVS):
    '''
    For testing: redis drops data quickly.
    '''
    def __init__(self, expire=30):
        '''
        We're just a `_RedisKVS` with expiration set
        '''
        super().__init__(expire=expire)


class PersistentRedisKVS(_RedisKVS):
    '''

    For deployment: Data lives forever.
    '''
    def __init__(self):
        '''
        We're just a `_RedisKVS` with expiration unset
        '''
        super().__init__(expire=None)


class FilesystemKVS(_KVS):
    '''
    This is a very non-scalable, non-performant KVS, where each item is a file
    on the filesystem. It can be helpful for debugging. Note that any sort
    of real-world use as the main KVS is not only non-performant, but could
    result in SSD wear.

    It's not a bad solution for caching some files in small-scale deploys.
    '''
    def __init__(self, path=None, subdirs=False):
        '''
        path: Where to store the kvs. Default: kvs
        subdirs: If set, keys with slashes will result in the creation of
        subdirs. For example, self.set("foo/bar", "hello") would create the
        directory foo (if it doesn't exist) and store "hello" in the file "bar"
        '''
        self.path = path or learning_observer.paths.data('kvs')
        self.subdirs = subdirs

    def key_to_safe_filename(self, key):
        '''
        Convert a key to a safe filename
        '''
        if self.subdirs:
            paths = key.split('/')
            # Add underscores to directories so they don't conflict with files
            for i in range(len(paths) - 1):
                paths[i] = '_' + paths[i]
            safename = (os.sep).join(map(learning_observer.util.to_safe_filename, paths))
        else:
            safename = learning_observer.util.to_safe_filename(key)
        return os.path.join(self.path, safename)

    def safe_filename_to_key(self, filename):
        raise NotImplementedError("Code this up, please. Or for debugging, comment out the exception")
        return filename

    async def __getitem__(self, key):
        path = self.key_to_safe_filename(key)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return f.read()

    async def set(self, key, value):
        path = self.key_to_safe_filename(key)
        if self.subdirs:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(value)

    async def __delitem__(self, key):
        path = key_to_safe_filename(key)
        os.remove(path)

    async def keys(self):
        '''
        This one is a little bit tricky, since if subdirs, we need to do a full
        walk
        '''
        if self.subdirs:
            for root, dirs, files in os.walk(self.path):
                for f in files:
                    yield self.safe_filename_to_key(os.path.join(root, f).replace(os.sep, '/'))
        else:
            for f in os.listdir(self.path):
                yield self.safe_filename_to_key(f)


class KVSCallable:
    def __init__(self, default=None):
        self._items = {'default': default}

    def __call__(self):
        return self._items['default']()

    def add_item(self, key, value):
        self._items[key] = value

    def remove_item(self, key):
        del self._items[key]

    def __getattr__(self, key):
        if key in self._items:
            return self._items[key]
        else:
            raise AttributeError(f'KVS Callable has no object: {key}')


KVS = None


@learning_observer.prestartup.register_startup_check
def kvs_startup_check():
    '''
    This is a startup check. If confirms that the KVS is properly configured
    in settings.py. It should happen after we've loaded settings.py, so we
    register this to run in prestartup.

    Checks like this one allow us to fail on startup, rather than later
    '''
    global KVS
    try:
        KVS_MAP = {
            'stub': InMemoryKVS,
            'redis_ephemeral': EphemeralRedisKVS,
            'redis': PersistentRedisKVS
        }
        # register KVSs
        # KVSOptions = enum.Enum('KVSOptions', learning_observer.settings.settings['kvs'])
        KVS = KVSCallable()
        for key, kvs_item in learning_observer.settings.settings['kvs'].items():
            kvs_type = kvs_item['type']
            kvs_class = KVS_MAP[kvs_type]
            # set timeout for ephemeral redis connections
            if kvs_type == 'redis_ephemeral':
                kvs_class = functools.partial(kvs_class, kvs_item['expiry'])
            KVS.add_item(key, kvs_class)

    except KeyError:
        if 'kvs' not in learning_observer.settings.settings:
            raise learning_observer.prestartup.StartupCheck(
                "No KVS configured. Please set kvs.type in settings.py\n"
                "Look at example settings file to see what's available."
            )
        elif any([kvs['type'] not in KVS_MAP for _, kvs in learning_observer.settings.settings['kvs'].items()]):
            raise learning_observer.prestartup.StartupCheck(
                "Unknown KVS type: {}\n"
                "Look at example settings file to see what's available. \n"
                "Suppported types: {}".format(
                    ', '.join([kvs['type'] for _, kvs in learning_observer.settings.settings['kvs'].items() if kvs['type'] not in KVS_MAP]),
                    list(KVS_MAP.keys())
                )
            )
        elif 'default' not in learning_observer.settings.settings['kvs']:
            raise learning_observer.prestartup.StartupCheck(
                "No default KVS configured. Please set default kvs.\n"
                "See example settings file for usage."
            )
        else:
            raise learning_observer.prestartup.StartupCheck(
                "KVS incorrectly configured. Please fix the error, and\n"
                "then replace this with a more meaningful error message"
            )
    return True


async def test():
    '''
    Simple test case: Spin up a few KVSes, write data to them, make
    sure it's persisted globally.
    '''
    learning_observer.settings.load_settings('creds.yaml')
    mk1 = InMemoryKVS()
    mk2 = InMemoryKVS()
    ek1 = EphemeralRedisKVS()
    ek2 = EphemeralRedisKVS()
    fs1 = FilesystemKVS(path="/tmp/flatkvs")
    fs2 = FilesystemKVS(path="/tmp/dirkvs", subdirs=True)
    assert (await mk1["hi"]) is None
    print(await ek1["hi"])
    assert (await ek1["hi"]) is None
    await mk1.set("hi", 5)
    await mk2.set("hi", 7)
    await ek1.set("hi", 8)
    await ek2.set("hi", 9)
    if True:
        os.makedirs("/tmp/flatkvs", exist_ok=True)
        os.makedirs("/tmp/dirkvs", exist_ok=True)
        await fs1.set("fooo", "poof")
        await fs1.set("foo/barła", "zoo")
        await fs2.set("foob", "loo")
        await fs2.set("fob/perła", "koo")
        assert (await fs1["fooo"]) == "poof"
    if False:  # We don't do this correctly yet
        async for k in fs2.keys():
            print(k)
        async for k in fs1.keys():
            print(k)

    assert (await mk1["hi"]) == 7
    print(await ek1["hi"])
    print(type(await ek1["hi"]))
    print((await ek1["hi"]) == 9)
    assert (await ek1["hi"]) == 9
    print(await mk1.keys())
    print(await ek1.keys())
    print("Test successful")
    print("Please wait before running test again")
    print("redis needs to flush expiring objects")
    print("This delay is set in the config file.")
    print("It is typically 1s - 24h, depending on")
    print("the work.")

if __name__ == '__main__':
    asyncio.run(test())
