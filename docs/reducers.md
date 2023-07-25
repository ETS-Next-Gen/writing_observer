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
|               |  |          |           |  -------|-> State     |       +------------+      +------------+
| Event Source  --------|---->| Reducer   |         |             |       |            |      |            |
|               |   |   |     |           | --------|-> External -------->| Aggregator |----> | Dashboard  |
+---------------+   |   |     +-----------+         |   State     |       |            |      |            |
+---------------+   |   |                           |             |       +------------+      +------------+
|               |   |   |                           +-------------+
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

4. **Aggregator**: The aggregator takes the external state from the key-value store and performs additional processing or aggregation to prepare the data for display in a dashboard.

5. **Dashboard**: The dashboard is the user interface that displays the aggregated data, providing insights into user activities and learning outcomes.

6. **Archival Repository**: This component is responsible for archiving event data, ensuring that historical data is available for analysis and reporting purposes.

## Using the Reducer System

To create a new reducer, use the `student_event_reducer` decorator. This allows you to define custom reduction functions that process events and transform them into meaningful insights. As the system evolves, it will be possible to plug in different aggregators, state types, and keys (e.g., per-student, per-resource) to the reducer system.

In the long term, the goal is to have pluggable, independent modules that can be connected to create a versatile and extensible analytics system. The current reducer system serves as a foundation for building such a system.