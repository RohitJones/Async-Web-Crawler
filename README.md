# Async Web Crawler

## Basic Usage
```
usage: runner.py [-h] [-d DEPTH] [-re RE_FILTER] [-reb RE_BLACKLIST]
                 [--log-errors] [--debug] [--timeout TIMEOUT]
                 url

Recursively crawl a target url

positional arguments:
  url                   Target url which crawling will start from

optional arguments:
  -h, --help            show this help message and exit
  -d DEPTH, --depth DEPTH
                        Maximum depth of urls to crawl
  -re RE_FILTER, --re-filter RE_FILTER
                        re string to filter URLs to crawl
  -reb RE_BLACKLIST, --re-blacklist RE_BLACKLIST
                        re string to blacklist URLs to fetch. For example
                        prevent fetches of images or PDFs etc
  --log-errors          Log errors that occur when crawling URLs
  --debug               Enable debug messages
  --timeout TIMEOUT     Number of seconds after which the web crawler will
                        stop if there are no running or scheduled tasks

```

### Run using Docker
```
docker build -t web-crawler .
docker run --rm web-crawler <INPUT ARGS>
```
for example:
```shell
docker run --rm web-crawler http://www.rescale.com --depth 2 --re-filter "^.*rescale.com.*" --timeout 5
```

### Run using local python
#### Note:
it is highly recommend use create and activate a new python virtual environment before running the following commands
```shell
# Install prerequisites for python virtual environments
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
```
#### Install requirements
```
pip install -r requirements.txt
```
#### Start webcrawler
```shell
src/runner.py <INPUT ARGS>
```
for example:
```shell
src/runner.py https://www.rescale.com --depth 2 --re-filter "^.*rescale.com.*" --timeout 5
```

## TESTING
Included is a basic python server that will serve a skeletal HTML website with the following structure:
```
index
  |
  ---> level 1a -> level 2a -> level 3a ===> index
         |           |
         |           +-------> level 3b ===> level 3a
         |
         +-------> level 2b ===> level 1a
         |
         +-------> level 2c
```
The expected result with crawling this test website is as follows:
```
http://localhost:8080
    http://localhost:8080/level1a.html
http://localhost:8080/level1a.html
    http://localhost:8080/level2a.html
    http://localhost:8080/level2b.html
    http://localhost:8080/level2c.html
http://localhost:8080/level2a.html
    http://localhost:8080/level3a.html
    http://localhost:8080/level3b.html
http://localhost:8080/level2b.html
    http://localhost:8080/level1a.html
http://localhost:8080/level2c.html
http://localhost:8080/level3a.html
    http://localhost:8080/index.html
http://localhost:8080/level3b.html
    http://localhost:8080/level3a.html
http://localhost:8080/index.html
    http://localhost:8080/level1a.html
```
To validate the above results
1. start the test server
```shell
cd testserver && python3 server.py
```
2. run the webcrawler and point it to `http://localhost:8080`

Docker command
```shell
docker build -t web-crawler . && docker run --rm --net=host web-crawler http://localhost:8080 --timeout 5
```

Native python command
```shell
python src/runner.py http://localhost:8080 --timeout 5
```

## Comments
* The webcrawler uses python's stdlib asyncio module to fetch multiple URLs in an asynchronous fashion
* The webcrawler will not fetch URLs that is has previously fetched.
  This avoids infinite recursive fetches when two pages link to each other
* It has a signal handler that will intercept signals like `SIGINT` and `SIGTERM` to cleanly
  close cancel all running tasks and exit the script
* When passing a timeout value via the `--timeout` arg, a `task_monitor` task is created that will sleep for
  the duration of the timeout and upon waking up will check if there are any running or scheduled tasks.
  If no tasks are found it will initiate a clean exit of the webcrawler similar to the signal handler.
  If there are running tasks it will go back to sleep and try again after the timeout duration
* The intention of the `re_blacklist` flag was to avoid fetching images, PDFs and binary files.
  The default value is `^.*\.(jpg|JPG|gif|GIF|doc|DOC|pdf|PDF|png|PNG)$`
  that will exclude fetching all urls that end with the specified URLs
* When the `--debug` flag is passed, additional info like queued time is displayed
* When the `--log-errors` flag is passed, any errors in fetching a URL will be printed out.
  By the default this is disabled and errors will be silently suppressed
* The whole project use `pre-commit` to run things like `black` and `mypy`
* The whole project has been run against `mypy` with no issues

## Core requirements
```
python3.8
beautifulsoup4 - Used to parse HTML content and extract tags
httpx - Used to fetch URLs asynchronous fashion
lxml - high performance parsing lib used by beautifulsoup4
```
