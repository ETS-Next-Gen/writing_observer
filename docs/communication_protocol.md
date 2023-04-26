# Student Writing Analysis Communication Protocol

## Overview

This document describes the communication protocol for a student writing analysis system. The protocol allows clients to request data from the server, which processes student writing samples and returns relevant insights and visualizations. The protocol is designed to be flexible, extensible, and easy to use for developers building dashboard applications.

## Communication Protocol

The communication protocol is based on JSON messages sent between the client and the server via WebSockets. Clients initiate requests by sending a JSON object to the server, which then processes the request and returns the data in a consistent format for easy parsing and display in the dashboards.

## Request and Response Structure

### Client Request

The client sends a JSON object containing the following properties:

- `course_id`: A string representing the course ID for which the analysis is requested.
- `module`: A string representing the name of the module to be executed (e.g., "vocabulary_complexity").
- `parameters`: An object containing key-value pairs, where each key is a function in the pipeline and the value is another object with keyword arguments defined for that function (optional).

Example request:

```json
{
  "course_id": "example_course_id",
  "module": "vocabulary_complexity",
  "parameters": {
    "extract_vocabulary": {
      "min_word_length": 5
    },
    "calculate_complexity": {
      "metric": "absolute"
    },
    "cluster_students_by_complexity": {
      "num_clusters": 4
    }
  }
}
```

### Server Response

The server processes the request and returns a JSON object with the following properties:

- `data`: An object containing the output of each function in the pipeline. The keys correspond to the function names, and the values represent the output of each function.
- `error`: An object containing information about any errors encountered during processing. If no errors occurred, this property should be set to null.

Example response:

```json
{
  "data": {
    "vocabulary_complexity": [
      {
        "student_id": "student1",
        "complexity_score": 7.3,
        "cluster": 2
      },
      {
        "student_id": "student2",
        "complexity_score": 5.6,
        "cluster": 1
      },
      ...
    ]
  },
  "error": null
}
```

## Error Handling

In case of errors during processing, the server returns an error object for any nodes that error out. The processing will continue for any prior nodes and disconnected subgraphs, but will stop when an error occurs.

## JavaScript WebSocket Example

To establish a WebSocket connection with the server and send a request message, you can use the following JavaScript code:

```javascript
const url = 'ws://localhost:8888/wsapi/dashboard-generic';
const ws = new WebSocket(url);
```

## Modules

### Vocabulary Complexity Module

This module analyzes the complexity of the vocabulary used by students in their essays. It can help middle and high school teachers understand the variety and sophistication of words used by their students in writing.

#### Module Components

- name: "vocabulary_complexity"
- sources: [source_function_1, source_function_2, ...]
- cleaner: vocabulary_complexity_cleaner_function
- aggregator: "digraph { extract_vocabulary -> calculate_complexity; extract_vocabulary -> cluster_students_by_complexity; }"
- default_data: { ... }

#### Pipeline

The Vocabulary Complexity module's aggregator pipeline consists of the following Directed Acyclic Graph (DAG) of functions:

ASCII Diagram of the DAG:

```bash
  +-------------------+
  | extract_vocabulary |
  +-------------------+
           |
           v
  +--------------------+
  | calculate_complexity |
  +--------------------+
           |
           v
  +--------------------------+
  | cluster_students_by_complexity |
  +--------------------------+
```

The pipeline processes the input data in the following order:

1. The `extract_vocabulary` function extracts unique words from students' essays and filters out words shorter than the specified minimum word length.
2. The `calculate_complexity` function calculates the complexity of the vocabulary used in the essays.
3. The `cluster_students_by_complexity` function clusters students based on their vocabulary complexity.

#### Functions and Parameters

##### extract_vocabulary(data, min_word_length=4)

Extracts unique words from students' essays and filters out words shorter than the specified minimum word length (default is 4).

##### calculate_complexity(data, metric='relative')

Calculates the complexity of the vocabulary used in the essays. The metric can be 'relative' (default) or 'absolute'. 'Relative' complexity takes into account the total number of unique words and word frequency, while 'absolute' complexity is based on the average length of words.

##### cluster_students_by_complexity(data, num_clusters=3)

Clusters students based on their vocabulary complexity. The number of clusters can be specified (default is 3).

#### Example

Example request for the Vocabulary Complexity module with custom parameters:
{
  "course_id": "example_course_id",
  "module": "vocabulary_complexity",
  "parameters": {
    "extract_vocabulary": {
      "min_word_length": 5
    },
    "calculate_complexity": {
      "metric": "absolute"
    },
    "cluster_students_by_complexity": {
      "num_clusters": 4
    }
  }
}

Example server response:
{
  "data": {
    "vocabulary_complexity": [
      {
        "student_id": "student1",
        "complexity_score": 7.3,
        "cluster": 2
      },
      {
        "student_id": "student2",
        "complexity_score": 5.6,
        "cluster": 1
      },
      ...
    ]
  },
  "error": null
}

In this example, the server returns a JSON object containing an array of student vocabulary complexity scores and their corresponding clusters. Teachers could use this data to visualize students' vocabulary complexity and better understand their writing development.

### Sentence Length Analysis Module

This module analyzes the sentence length in students' essays to provide insights into their writing style and help identify areas for improvement.

#### Module Components

- name: "sentence_length_analysis"
- sources: [fetch_student_essays]
- cleaner: clean_student_essays
- aggregator: "digraph { extract_sentences -> calculate_sentence_lengths; calculate_sentence_lengths -> calculate_average_length; calculate_sentence_lengths -> calculate_length_distribution; calculate_average_length -> merge_length_data; calculate_length_distribution -> merge_length_data; }"
- default_data: {}

#### Pipeline

The Sentence Length Analysis module's aggregator pipeline consists of the following Directed Acyclic Graph (DAG) of functions:

ASCII Diagram of the DAG:

```bash
  +------------------+
  | extract_sentences |
  +------------------+
           |
           v
  +---------------------+
  | calculate_sentence_lengths |
  +---------------------+
           |
           v
  +-------------------+            +---------------------------+
  | calculate_average_length |---->| calculate_length_distribution |
  +-------------------+            +---------------------------+
           |                         |
           v                         v
         +----------------+
         | merge_length_data |
         +----------------+
```

The pipeline processes the input data in the following order:

1. The `extract_sentences` function extracts sentences from the cleaned student essays.
2. The `calculate_sentence_lengths` function calculates the length of each sentence in terms of the number of words.
3. The `calculate_average_length` and `calculate_length_distribution` functions process the sentence lengths data concurrently.
4. The `merge_length_data` function merges the outputs from `calculate_average_length` and `calculate_length_distribution` into a single data object.

#### Functions and Parameters

##### extract_sentences(data)

Extracts sentences from the cleaned student essays.

##### calculate_sentence_lengths(data)

Calculates the length of each sentence in terms of the number of words.

##### calculate_average_length(data)

Calculates the average sentence length for each student.

##### calculate_length_distribution(data, bins=5)

Calculates the distribution of sentence lengths for each student, dividing the lengths into a specified number of bins (default is 5).

##### merge_length_data(data)

Merges the outputs from `calculate_average_length` and `calculate_length_distribution` into a single data object.

#### Example

Example request for the Sentence Length Analysis module with custom parameters:

```json
{
  "course_id": "example_course_id",
  "module": "sentence_length_analysis",
  "parameters": {
    "calculate_length_distribution": {
      "bins": 6
    }
  }
}
```

Example server response:

```json
{
  "data": {
    "calculate_average_length": [
      {
        "student_id": "student1",
        "average_length": 14.7
      },
      {
        "student_id": "student2",
        "average_length": 17.2
      },
      ...
    ],
    "calculate_length_distribution": [
      {
        "student_id": "student1",
        "length_distribution": {
          "1-5": 3,
          "6-10": 8,
          "11-15": 12,
          "16-20": 7,
          "21-25": 4,
          "26-30": 1
        }
      },
      {
        "student_id": "student2",
        "length_distribution": {
          "1-5": 2,
          "6-10": 6,
          "11-15": 11,
          "16-20": 9,
          "21-25": 5,
          "26-30": 0
        }
      },
      ...
    ]
  },
  "error": null
}
```

In this example, the server returns a JSON object containing two separate arrays: one with the calculated average sentence length for each student and another with the distribution of sentence lengths for each student.
