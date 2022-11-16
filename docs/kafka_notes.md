# Structure notes

Table for students

student | sessions | hashes
---|---|---
example@email.com | \[kafka_topic_id_00, kafka_topic_id_23\] | \[hash_of_kafka_topic_id_00\]

Create session

* Create Kafka stream
* Add student to student table with session name (REDIS or KAFKA)

Closing behavior

* Socket gets closed
  * Times out?
  * Could we determine when the document is closed?
* Message sent to data server
  * The number of requests between servers will be dramatically fewer than messages between client and WO
  * Could use a simple REST API
* Data server will:
  * Compute the Hash
    * Read data from Kafka stream
    * Compute `hash = hash(data)` from our own hash function
      * SHA 256 with some salt
      * Create a Merkle tree where each leaf is a log event from the session. We use the root hash instead
    * Append `hash` to a student's `hashes`
  * Backup data
    * Determine file location, `f = str(hash[:2]/hash[2:])` or some other way of hashing
    * Create file at `f`
      * There is some note that says Linux handles a lot of directories better than a lot of files in WYAG
    * Write data to `f`

Things TODO:

* Turn on Kafka
* Write some of our data to Kafka stream
  * Make the naming scheme easier to understand, for testing
  * Just run it localy and collect the data through yourself
* Create simple REST API
  * Post command to student
  * Compute the hash, pull data, and store it

How do we create the Merkle tree?

* What is the purpose of the Merkle Tree?
  * Where does it fit in?
  * How will it be used?
  * What is the purpose of the DAG portion?

* Is it autostored in a merkle tree? i.e. the directory structure of our store is a merkle tree
* How are Merkle tree being used here?
  * Do we store each log event as a Merkle Tree? Why?
  * Do we store each log file as a Merkle Tree? Why?
