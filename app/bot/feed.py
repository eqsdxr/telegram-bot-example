from feedparser import parse
from app.bot import exc


def get_rss_data(url: str):
    feed = parse(url)
    if feed.bozo:
        raise exc.InvalidRSSURLError()
    return feed
