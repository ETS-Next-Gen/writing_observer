# Event Reducers

The Learning Observer project uses a reducer system to handle events from various event sources, process them, and provide aggregated data for use in dashboards. This page describes the reducer system's architecture, how it processes events, and its components.

## Reducer System Architecture

The reducer system is designed to be modular and flexible, allowing for the addition and removal of event sources, aggregators, and dashboards as needed. The overall system diagram is as follows:

```bash
+---------------+
|               |                                   +-------------+
| Event Source  ---|                                | Key-Value   |
|               |  |                                | Store       |
|               |  |                                |             |
+---------------+  |                                +-------------+
+---------------+  |          +-----------+  <------|-- Internal  |
|               |  |          |           |  -------|-> State     |       +---------------+      +------------+
| Event Source  --------|---->| Reducer   |         |             |------>|               |      |            |
|               |   |   |     |           |         +-------------+       | Communication |----> | Dashboard  |
+---------------+   |   |     +-----------+                               | Protocol      |      |            |
+---------------+   |   |                                                 +---------------+      +------------+
|               |   |   |
| Event Source  ----|   |
|               |       |
+---------------+       v
                  +------------+
                  |            |
                  |  Archival  |
                  | Repository |
                  |            |
                  +------------+
```

The reducer system consists of the following components:

1. **Event Sources**: These are the sources of events that need to be processed. Each event source is responsible for generating events based on user activities, such as clicks, page views, or interactions with learning materials.

2. **Reducer**: The reducer is the central component that processes the events from all event sources. It takes the incoming events and applies a specific reduction function to transform the event data into a more concise and meaningful form. The reducer is created using the `student_event_reducer` decorator, which enables modularity and flexibility in defining reduction functions.

3. **Key-Value Store**: This component stores the internal and external state generated by the reducer. The internal state is used for the reducer's internal processing, while the external state is shared with other components, such as aggregators and dashboards.

4. **Communication Protocol**: The communication protocol handles fetching and transforming data from the key-value store using an SQL-like structure.

5. **Dashboard**: The dashboard is the user interface that displays the data from the communication protocol, providing insights into user activities and learning outcomes.

6. **Archival Repository**: This component is responsible for archiving event data, ensuring that historical data is available for analysis and reporting purposes.

## Using the Reducer System

To create a new reducer, use the `student_event_reducer` decorator. This allows you to define custom reduction functions that process events and transform them into meaningful insights. As the system evolves, it will be possible to plug in different aggregators, state types, and keys (e.g., per-student, per-resource) to the reducer system.

In the long term, the goal is to have pluggable, independent modules that can be connected to create a versatile and extensible analytics system. The current reducer system serves as a foundation for building such a system.

An example of a simple reducer to count events can be defined as

```python
# import student scope reducer decorator
from learning_observer.stream_analytics.helpers import student_event_reducer

@student_event_reducer(null_state={"count": 0})
async def student_event_counter(event, internal_state):
    # do something with the internal state, such as increment
    state = {"count": internal_state.get('count', 0) + 1}

    # return internal state, external state (no longer used)
    return state, state
```

To add a reducer to a module, we much define a `REDUCERS` section in a module's `module.py` file like so

```python
# module.py
# ...other items

REDUCERS = [
    {
        'context': 'org.mitros.writing_analytics',
        'scope': Scope([KeyField.STUDENT]),
        'function': module.path.to.reducers.student_event_counter,
        'default': {'count': 0}
    }
]
```

NOTE: the `default` defined in the `module.py` file is for handling defaults when queries are made, while the `null_state` defined in the reducer decorator is used for initializing state of a new incoming event stream (e.g. a new student started sending events).
