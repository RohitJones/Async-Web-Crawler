#!/usr/bin/env python3
import argparse

from web_crawler import AsyncWebCrawler
from web_crawler.config import Defaults

parser = argparse.ArgumentParser(description="Recursively crawl a target url")
parser.add_argument("url", help="Target url which crawling will start from")
parser.add_argument("-d", "--depth", help="Maximum depth of urls to crawl", type=int, default=Defaults.depth_limit)
parser.add_argument(
    "-re", "--re-filter", help="re string to filter URLs to crawl", default=Defaults.re_filter, dest="re_filter"
)
parser.add_argument(
    "-reb",
    "--re-blacklist",
    help="re string to blacklist URLs to fetch. For example prevent fetches of images or PDFs etc",
    default=Defaults.re_blacklist,
    dest="re_blacklist",
)
parser.add_argument(
    "--log-errors",
    help="Log errors that occur when crawling URLs",
    default=Defaults.log_errors,
    action="store_true",
    dest="log_errors",
)
parser.add_argument("--debug", help="Enable debug messages", default=Defaults.debug, action="store_true")
parser.add_argument(
    "--timeout",
    help="Number of seconds after which the web crawler will stop if there are no running or scheduled tasks",
    type=int,
    default=Defaults.stop_timeout,
)


args = parser.parse_args()
async_web_crawler = AsyncWebCrawler(
    base_url=args.url,
    depth_limit=args.depth,
    re_filter=args.re_filter,
    re_blacklist=args.re_blacklist,
    log_errors=args.log_errors,
    debug=args.debug,
    timeout=args.timeout,
)

async_web_crawler.start()
