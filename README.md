# redline
A simple CLI client for redis when `redis-cli` cannot be easily installed

It is recommended that you use `redis-cli` if it is available, but, if not, this may be cloned and 'installed' 
for basic CLI usage.

## Installation

1. Create a virtual environment and activate it
2. Run `pip install -e .` to install all of the dependencies
3. Run `python3 deploy.py` to build the application and place it on your `PATH`

## Usage

If the application is on your `PATH`, simple write commands like the following in your terminal:

```shell
redline GET some-key
redline PING
redline -h host -p port register
redline SET some-key some-value
```

As of 9/18/2025, functionality is limited. Hopefully in the future other commands may be added, like hash manipulation 
and stream investigation.

This works on both Redis and Valkey.

## Notice

Use at your own risk - this has not been fully tested and is just a convenient fallback for now.
