'''
This is a prototype for our log storage system.

It is only a prototype. To make this not a prototype, we would need to:

- Make it work with Kafka
- Make it work with asyncio
- Make the file system operations not slow
- Use full-length hashes
- Confirm it's robust
- Escape the file names properly or compute interrim session IDs more intelligently
- Etc.
'''

import hashlib
import json
import datetime
from modulefinder import STORE_GLOBAL
import os
from pickle import STOP

# These should be abstracted out into a visualization library.
import matplotlib
import networkx
import pydot

from confluent_kafka import Producer


def json_dump(obj):
    """
    Dump an object to JSON.

    Args:
        obj (object): The object to dump.

    Returns:
        str: The JSON dump.

    This is shorthand so that we have a consistent way to dump objects
    each time. We use JSON dumps to index into dictionaries and such.
    """
    return json.dumps(obj, sort_keys=True)


def json_load(string):
    """
    Load a JSON string.

    Args:
        string (str): The JSON string.

    Returns:
        object: The JSON object.

    We don't really need this, put for symmetry with json_dump and consistency.
    """
    return json.loads(string)


def session_ID(session):
    """
    Return an ID associated with a session.

    Such an ID is used before we have a finished session which we can
    place into the Merkle DAG

    Args:
        session (dict): The session.

    Returns:
        str: The session ID.

    The session ID is currently a JSON dump. We'll do something cleaner later,
    perhaps, but this is good enough for now
    """
    return json_dump(session)


def timestamp():
    """
    Return a timestamp string in ISO 8601 format

    Returns:
        str: The timestamp string.

    The timestamp is in UTC.
    """
    return datetime.datetime.utcnow().isoformat()


def hash(*strings):
    """
    Return a hash of the given strings.

    Args:
        strings (str): The strings to hash.

    Returns:
        str: The hash of the given strings.

    The strings should not contain tabs.
    """
    return hashlib.sha1('\t'.join(strings).encode('utf-8')).hexdigest()[:8]


class Merkle:
    def __init__(self, storage, categories):
        '''
        Initialize the merkle DAG.

        `categories` is a list of categories by which we might
        want to index into events
        '''
        self.storage = storage
        self.categories = categories

    # These are generic to interact with the Merkle DAG
    def event_to_session(self, event, session, children=None, label=None):
        '''
        Append an event to the merkle tree.

        There are two possibilities here:
        1. We have a closure and we're updating the SHA hash with each
            event.
        2. We don't have a closure and we're placing the individual
            events into the Merkle DAG.
        We went with the second option. This makes events into the leaf,
        nodes, whereas the first option makes sessions into the leaf
        nodes.

        This uses a little bit more space, but it's easier to reason about,
        and potentially minimizes some ad-hoc decisions, such as where to
        put boundaries between long-running sessions.

        We might still want a closure, so we don't need to read back the
        last item in the stream. Or perhaps we want both (with one calling
        the other), using a closure for rapid events and a call like this
        one for rare ones.

        Args:
            event (dict): The event to append.
            session (dict): The session to append to. This should specify
                a set of categories, and map those to lists of associated
                IDs. For example, "teacher": ["teacher1", "teacher2"]
            children (list): Additional children of this event, beyond the
                current item and the past event.
            label (str): An optional human-friendly label for this event. This
                should NOT be relied on programmatically, or to be unique. It's
                just for human consumption, e.g. when making visualizations.

        Returns:
            dict: The event envelope, with the session updated, and the
                hash computed.
        '''
        # reverse() so we add children from the parameters to the end of the list
        # of children. This isn't strictly necessary, but it is a little bit
        # nicer to look at manually. We could remove the pair of reverse() calls,
        # since this is an unordered list, if this ever becomes a problem.
        if children is None:
            children = list()
        children.reverse()
        storage = self.storage
        session_id = session_ID(session)
        ts = timestamp()

        event_hash = hash(json_dump(event))
        node_hash = hash(*children, ts)

        last_hash = None
        last_item = storage._most_recent_item(session_id)

        if last_item is not None:
            last_hash = last_item['hash']
            children.append(last_hash)

        children.append(event_hash)

        children.reverse()
        print(children)

        item = {
            'children': children,                 # Points to the full chain / children
            'hash': node_hash,                    # Current node
            'timestamp': ts,                      # Timestamp
            'event': event
        }
        if label is not None:
            item['label'] = label
        storage._append_to_stream(session_id, item)
        print(item['hash'])
        return item

    def start(self, session, metadata=None):
        '''
        Start a new session.

        Args:
            session (dict): The session to start.
            metadata (dict): Optional metadata to attach to the session.

        Returns:
            dict: The session envelope
        '''
        event = {
                'type': 'start',
                'session': session
                # Perhaps we want to add a category here? E.g. 'session_event_stream' for the raw streams
                # and something else to indicate parents?
        }
        if metadata is not None:
            event['metadata'] = metadata
        return self.event_to_session(
            event,
            session,
            label='start'
        )

    def close_session(self, session):
        '''
        Close the session. We update up-stream nodes with the session's
        merkle leaf. and if necessary, we update the session's key /
        topic / alias with the hash of the full chain.
        '''
        final_item = self.event_to_session(
            {'type': 'close', 'session': session},
            session,
            label='close'
        )
        session_hash = final_item['hash']
        self.storage._rename_or_alias_stream(session_ID(session), session_hash)
        if len(session) < 1:
            raise Exception('Session is empty')
        if len(session) == 1:
            print("Parent session")
            print("These sessions shouldn't be closed")
            return
        for key in session:
            if key not in self.categories:
                print("Something is wrong. Session has unexpected key: {}".format(key))
            for item in session[key]:
                parent_session = {key: item}
                self.event_to_session(
                    {
                        'type': 'child_session_finished',
                        'session': session_hash  # This should go into children, maybe?,
                    },
                    parent_session,
                    children=[session_hash],
                    label=f'{key}'
                )
        return session_hash


class StreamStorage:
    def _append_to_stream(self, stream, item):
        '''
        Append an item to a stream.
        '''
        raise NotImplementedError

    def _rename_or_alias_stream(self, stream, alias):
        '''
        Rename a stream.
        '''
        raise NotImplementedError

    def _get_stream_data(self, stream):
        '''
        Get the stream.
        '''
        raise NotImplementedError

    def _delete_stream(self, sha_key):
        '''
        Delete a stream.

        Mostly for right-to-be-forgotten requests
        '''
        raise NotImplementedError

    def _most_recent_item(self, stream):
        '''
        Get the most recent item in a stream.
        '''
        raise NotImplementedError

    def _walk(self):
        '''
        Walk the DAG. This is used for debugging.
        '''
        raise NotImplementedError

    def _make_label(self, item):
        '''
        Make a label for an item.

        This is cosmetic, when rendering the graph.
        '''
        if 'label' in item and item['label'] is not None:
            return item['label']
        print(item)
        if 'session' in item and len(item['session']) == 1:
            return "-".join(item['session'].items()[0])
        return item['hash'][:4]

    def to_networkx(self):
        '''
        Convert the DAG to a network.

        This is used for testing, experimentation, and demonstration. It
        would never scale with real data.
        '''
        G = networkx.DiGraph()
        for item in self._walk():
            print(item)
            G.add_node(item['hash'], label=self._make_label(item))
            if 'children' in item:
                for child in item['children']:
                    G.add_edge(item['hash'], child)
        return G

    def to_graphviz(self):
        '''
        Convert the DAG to a graphviz graph.

        This is used for testing, experimentation, and demonstration. It
        would never scale with real data.
        '''
        G = pydot.Dot(graph_type='graph')
        for item in self._walk():
            node = pydot.Node(item['hash'], label=self._make_label(item))
            G.add_node(node)
        for item in self._walk():
            if 'children' in item:
                for child in item['children']:
                    edge = pydot.Edge(item['hash'], child)
                    G.add_edge(edge)
        return G


class KafkaStorage(StreamStorage):
    """
    A Merkle DAG implementation that uses Kafka as a backing store.
    """
    def __init__(self):
        super().__init__()
        self.producer = Producer()


class FSStorage(StreamStorage):
    """
    A Merkle DAG implementation that uses a file system as a backing store.
    """
    def __init__(self, path):
        super().__init__()
        self.path = path

    def _fn(self, stream):
        '''
        Get the filename for a stream.

        This is prototype code. We should escape the stream name robustly to avoid
        security issues and collisions.
        '''
        safer_filename = "".join(c for c in stream if c.isalnum() or c in '-_')
        return os.path.join(self.path, safer_filename)

    def _append_to_stream(self, stream, item):
        '''
        Append an item to a stream.
        '''
        with open(self._fn(stream), 'a') as f:
            f.write(json_dump(item))
            f.write('\n')

    def _rename_or_alias_stream(self, stream, alias):
        '''
        Rename a stream.
        '''
        os.rename(self._fn(stream), self._fn(alias))

    def _get_stream_data(self, stream):
        '''
        Get the stream.
        '''
        if not os.path.exists(self._fn(stream)):
            return None
        with open(self._fn(stream), 'r') as f:
            return [json_load(line) for line in f.readlines()]

    def _delete_stream(self, sha_key):
        '''
        Delete a stream.
        '''
        os.remove(self._fn(sha_key))

    def _most_recent_item(self, stream):
        '''
        Get the most recent item in a stream.
        '''
        data = self._get_stream_data(stream)
        if data is None:
            return None
        if len(data) == 0:
            return None
        return data[-1]

    def _walk(self):
        '''
        Walk the DAG. This is used for debugging.
        '''
        for filename in os.listdir(self.path):
            with open(os.path.join(self.path, filename), 'r') as f:
                for line in f.readlines():
                    yield json_load(line)


class InMemoryStorage(StreamStorage):
    """
    A Merkle DAG implementation that uses in-memory storage.
    """
    def __init__(self):
        super().__init__()
        self.store = {}

    def _append_to_stream(self, stream, item):
        if stream not in self.store:
            self.store[stream] = []
        self.store[stream].append(item)

    def _rename_or_alias_stream(self, stream, alias):
        if alias == stream:
            return
        self.store[alias] = self.store[stream]
        del self.store[stream]

    def _get_stream_data(self, stream):
        return self.store[stream]

    def _delete_stream(self, stream):
        del self.store[stream]

    def _most_recent_item(self, stream):
        if stream not in self.store:
            return None
        if len(self.store[stream]) == 0:
            return None
        return self.store[stream][-1]

    def _walk(self):
        for stream in self.store:
            for item in self.store[stream]:
                yield item


CATEGORIES = set(
    [
        "teacher",
        "student",
        "school",
        "classroom",
        "course",
        "assignment"
    ]
)


def test_case():
    """
    A test case, mostly used to demo the Merkle DAG. It doesn't check for
    correctness yet, but does show a simple visualization of the DAG.
    """
    big_session = {
        "teacher": ["Ms. Q", "Mr. R"],
        "student": ["John"],
        "school": ["Washington Elementary"],
        "classroom": ["4A"],
        "course": ["Math"]
    }
    small_session = {
        "teacher": ["Mr. A"],
        "student": ["John"]
    }
    session = small_session

    STORAGE = 'FS'

    if STORAGE == 'MEMORY':
        storage = InMemoryStorage()
    elif STORAGE == 'FS':
        if not os.path.exists('/tmp/merkle_dag'):
            os.mkdir('/tmp/merkle_dag')
        storage = FSStorage('/tmp/merkle_dag')
    else:
        raise NotImplementedError(STORAGE)

    merkle = Merkle(storage, CATEGORIES)
    merkle.start(session)
    merkle.event_to_session({"type": "event", "event": "A", "name": "1st"}, session, label="A")
    merkle.event_to_session({"type": "event", "event": {"B": "c"}, "name": "2nd"}, session, label="B")
    merkle.event_to_session({"type": "event", "event": {"B": "c"}}, session, label="C")
    merkle.close_session(session)
    G = storage.to_graphviz()
    import PIL.Image as Image
    import io
    Image.open(io.BytesIO(G.create_png())).show()


if __name__ == "__main__":
    test_case()
