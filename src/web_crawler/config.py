from dataclasses import dataclass


@dataclass
class Defaults:
    depth_limit: int = -1
    re_filter: str = ".*"
    debug: bool = False
    re_blacklist: str = r"^.*\.(jpg|JPG|gif|GIF|doc|DOC|pdf|PDF|png|PNG)$"
    log_errors: bool = False
    stop_timeout: int = -1
