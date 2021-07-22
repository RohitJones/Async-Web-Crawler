import asyncio
import logging
import re
import signal
from dataclasses import dataclass
from time import perf_counter
from typing import List, Optional, Set

import bs4
import httpx

from web_crawler.config import Defaults


@dataclass
class ParseTarget:
    url: str
    depth: int
    queued_ts: float


class AsyncWebCrawler:
    def __init__(
        self,
        base_url: str,
        depth_limit: int = Defaults.depth_limit,
        re_filter: str = Defaults.re_filter,
        *,
        re_blacklist: str = Defaults.re_blacklist,
        log_errors: bool = Defaults.log_errors,
        debug: bool = Defaults.debug,
        timeout: int = Defaults.stop_timeout,
    ):
        self.base_url = base_url
        self.depth_limit = depth_limit  # Optional stopping condition based on the depth
        self.re_filter = re_filter  # Filter on with URLs to parse. For example only rescale URLS
        self.event_loop = asyncio.get_event_loop()
        self._visited_urls: Set[str] = set()  # visited set to make avoid crawling duplicate URLs
        self._httpx_client = httpx.AsyncClient()
        self._re_blacklist = re_blacklist
        self._log_errors = log_errors
        self.start_time = 0.0
        self._logger = logging.getLogger(__name__)
        self._debug = debug
        self._timeout = timeout

        # Set log level and message format
        if debug:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(self._logger.level)
        ch.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(ch)

    def start(self) -> None:
        # Add signal handlers to cleanly stop the webcrawler
        for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
            self.event_loop.add_signal_handler(s, lambda: asyncio.create_task(self.stop(s)))

        self._logger.debug("started")
        self.start_time = perf_counter()  # Initialization timestamp of the webcrawler
        # Create the first task. Start with URL passed in and set starting depth to 0
        self.event_loop.create_task(
            self._process_url(ParseTarget(url=self.base_url, depth=0, queued_ts=perf_counter()))
        )

        if self._timeout > 0:
            # Create task monitor that will cleanly stop the webcrawler when there are not running or scheduled tasks
            self.event_loop.create_task(self._task_monitor())

        # start the event loop that will execute all queued up tasks
        self.event_loop.run_forever()

    async def _task_monitor(self) -> None:
        while True:
            await asyncio.sleep(self._timeout)
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if not tasks:
                self._logger.debug("No running tasks for 5s. Starting stop task")
                asyncio.create_task(self.stop())
                break

        return None

    async def stop(self, received_signal: signal.Signals = None) -> None:
        """Cleanup tasks tied to the service's shutdown."""

        if received_signal:
            self._logger.debug(f"Received exit signal {received_signal.name}...")

        # get all running and queued up tasks on the event loop, except this task (the stop task)
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]  # cancel all the tasks

        self._logger.debug(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)

        # clean up
        await self._httpx_client.aclose()
        self.event_loop.stop()

    async def _process_url(self, target: ParseTarget) -> None:
        # Ensure that url has not be processed already
        # if depth limit is > 0, ensure that the current target is less than the depth limit
        # Ensure that the url of the current target passes the re-blacklist
        if (
            target.url in self._visited_urls
            or (0 < self.depth_limit < target.depth)
            or re.search(self._re_blacklist, target.url)
        ):
            return None

        # Add the current target url to the visited set
        self._visited_urls.add(target.url)

        try:
            response = await self._httpx_client.get(target.url)
            response.raise_for_status()  # if status is 4xx or 5xx raise error

            # performance statistics if logging level is DEBUG
            if self._debug:
                complete_ts = perf_counter()
                self._logger.debug(
                    target.url + f" [abs-time: {complete_ts - self.start_time :0.2f}s]"
                    f"[queue-time: {complete_ts - target.queued_ts: 0.2f}s]"
                    f"[depth: {target.depth}]"
                )
            else:
                self._logger.info(target.url)

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            if self._log_errors:
                self._logger.error(
                    "[ERROR] {error_type} {url} [{status}]: {message}".format(
                        url=target.url,
                        error_type=type(e),
                        status=getattr(e, "status", "NULL"),
                        message=getattr(e, "message", "NULL"),
                    )
                )
            return None

        soup = bs4.BeautifulSoup(response.content, "lxml")  # parse response
        all_a: List[bs4.element.Tag] = soup.find_all(name="a")  # find all "a" tags

        for a in all_a:
            url: Optional[str] = a.attrs.get("href")
            if url and url.startswith("http") and re.search(self.re_filter, url):
                self._logger.info(" " * 4 + url)
                # Create new task and increase the depth by 1
                new_target = ParseTarget(url=url, depth=target.depth + 1, queued_ts=perf_counter())
                self.event_loop.create_task(self._process_url(new_target))
