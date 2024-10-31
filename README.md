# Pokemon Queue Processor

A Python-based backend service designed to fetch Pokémon data from an external API, process the data, and send it to a
message queue.

## Project Setup

### Install Project

    git clone git@github.com:Ekwinder/poke_deck.git
    cd poke_deck

### Run using Docker

    docker build -t poke-queue .
    docker run -it -rm poke-queue

if you want to check with persistent DB on disk

    docker run -it --rm -v $(pwd)/poke_data.db:/app/poke_data.db poke-queue

### Run directly on Unix

#### Setup Virtual Environment

    python -m venv poke_queue
    source poke_queue/bin/activate
    
    pip install -r requirements.txt #install dependencies

#### Run python app from the entry point

    python main.py

### Run tests

    pytest -v # verbose complete tests
    pytest -k test_process_queue_with_data #run tests on a single file

## Project Structure

### Config

This contains URLS, keys etc. This would be fetched from a central secret manager/env manager
or added to docker while deploying so handle the secrets/config across multiple instances

### Poke API

Has hit to external API. The module uses asyncio for non-blocking requests.

### Poke DB

SQLite DB connection module. I have added SQLite to keep track of items fetched from the source and sent
to the queue for processing. This helps in ensuring duplicate requests are not being made to the 3rd party
API and the message is sent to queue only once. Not an ideal choice as SQLite is not good with concurrent connections.

### Poke Queue

Simple queue Send and Receive implementation. There is no Dead Letter Queue or Retry Queue, so the same queue is being
used to send the data again, ideally they should be separate

### Poke Queue Processor

Acts as the consumer for the queue, this is running as receiver in main.py to simulate message consumption
in a queue.

### Poke Transformer

Contains the business logic. It calls the Poke API module to fetch data, transforms it and sends the
data the queue.

### main.py

This is the entry point of the project. It has basic concurrency control to keep balance between producers and consumers
and control hits to the 3rd party API. It sets up logger, DB, queue objects and starts the process with asyncio.
This would be a Python script that will continuously keep on running until stopped, in a production or cloud
environment this could be cron triggered or event triggered job or this could even be an API.

## Actual Implementation in Cloud environment

I have implemented a production solution similar to this. The solution involved fetching negative headlines,
5000 to 10000 pages of 100 records each from a 3rd party paid source daily and storing them in DB for further
processing.
We used AWS Lambda for this, the trigger event was a cron(AWS EventBridge).

* First, a count/summary API or the first page can be called to get the total count of the records to calculate the
  number of pages there would be, for example count is 100000 and 100 items per page, we know there are 1000 pages in
  total.
* This can be used to plan the concurrent, kind of divide and conquer mechanism, we can divide 1000/10 = 100 pages per
  10 Lambda servers and send start and end page to each of them, where each Lambda might loop over the 100 pages
  asynchronously or synchronously and get the response. This was achieved through AWS SQS. messages in batches were sent
  to SQS which in turn were the entry point for lambdas.
* As the API hits can be expensive, entries can be made in cache or DB as well to track how much data has been processed
  from the source in case of some system failure, there would be point to continue from(not required in this approach)
* In case of request failures or processing failures, we can set retries, the request will again go back into the queue
  and tried again, after a certain number of failures, we can send the request to the Dead Letter Queue and mark the status
  as failure in cache/DB.


