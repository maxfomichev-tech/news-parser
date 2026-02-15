
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from utils import clean_html
from config import config

@dataclass
class NewsItem:
    title: str
    summary: str
    link: str
    source: str
    published: Optional[datetime] = None
    raw_date: str = ""

class RSSFetcher:
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_feed(self, url: str) -> List[NewsItem]:
        if not self.session:
            raise RuntimeError("Use async with")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9',
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"⚠️ {url}: HTTP {response.status}")
                    return []
                content = await response.text()
                return self._parse_xml(content, url)
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return []

    def _parse_xml(self, content: str, source_url: str) -> List[NewsItem]:
        items = []
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            print(f"XML parse error: {e}")
            return []

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        channel = root.find('.//channel')
        feed = root.find('.//{http://www.w3.org/2005/Atom}feed')

        source_name = source_url.split('/')[2] if '://' in source_url else "Unknown"

        if channel is not None:
            title_elem = channel.find('title')
            source_name = title_elem.text if title_elem is not None else source_name
            entries = channel.findall('item')
            date_tag, desc_tag = 'pubDate', 'description'
        elif feed is not None:
            title_elem = feed.find('atom:title', ns)
            source_name = title_elem.text if title_elem is not None else source_name
            entries = feed.findall('atom:entry', ns)
            date_tag, desc_tag = 'published', 'summary'
        else:
            entries = root.findall('.//item') or root.findall('.//entry', ns)
            date_tag, desc_tag = 'pubDate', 'description'

        for entry in entries[:10]:
            try:
                title = self._get_text(entry, 'title', ns) or "Без заголовка"
                link = self._get_link(entry, ns)
                summary = self._get_text(entry, desc_tag, ns) or ""

                items.append(NewsItem(
                    title=title.strip(),
                    summary=clean_html(summary)[:300],
                    link=link,
                    source=source_name,
                    raw_date=self._get_text(entry, date_tag, ns) or ""
                ))
            except Exception as e:
                continue

        return items

    def _get_text(self, element, tag: str, ns: dict) -> Optional[str]:
        if ns:
            elem = element.find(f'atom:{tag}', ns)
            if elem is not None and elem.text:
                return elem.text
        elem = element.find(tag)
        if elem is not None and elem.text:
            return elem.text
        return None

    def _get_link(self, element, ns: dict) -> str:
        link_elem = element.find('atom:link', ns) if ns else None
        if link_elem is not None:
            href = link_elem.get('href')
            if href:
                return href

        link_elem = element.find('link')
        if link_elem is not None and link_elem.text:
            return link_elem.text

        guid = element.find('guid')
        if guid is not None and guid.text:
            return guid.text
        return ""

    async def fetch_all(self, urls: List[str]) -> List[NewsItem]:
        tasks = [self.fetch_feed(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                print(f"Task failed: {result}")

        return all_items[:config.MAX_NEWS_ITEMS]

def load_rss_urls(filename: str) -> List[str]:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = []
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith(('http://', 'https://')):
                    urls.append(line)
            return urls
    except FileNotFoundError:
        print(f"File {filename} not found")
        return []
