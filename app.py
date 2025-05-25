#!/usr/bin/env python3
"""sitemap_to_wxr.py

Download a site's sitemap, extract post titles (via page <title>), generate new
posts with OpenAI GPT‑4o, and build a WordPress WXR import file.

Usage:
    python sitemap_to_wxr.py https://example.com --domain-filter "/blog/" \
        --max-posts 50 --output secret_hotline_posts.xml

Environment:
    OPENAI_API_KEY  – your OpenAI key (export before running).

Dependencies (pip install ...):
    requests beautifulsoup4 lxml openai tqdm python-slugify
"""
import argparse
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import openai
import requests
from bs4 import BeautifulSoup
from slugify import slugify
from tqdm import tqdm

SITEMAP_RE = re.compile(r"Sitemap:\s*(\S+)")

openai.api_key = os.getenv("OPENAI_API_KEY")

HEADERS = {"User-Agent": "sitemap-to-wxr/1.0 (+https://github.com/yourrepo)"}

def discover_sitemap(base_url: str) -> str:
    """Return sitemap URL – checks robots.txt then falls back to /sitemap.xml."""
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    robots_url = base_url.rstrip("/") + "/robots.txt"
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            for m in SITEMAP_RE.finditer(r.text):
                return m.group(1)
    except requests.RequestException:
        pass
    # Fallback
    return base_url.rstrip("/") + "/sitemap.xml"

def parse_sitemap(sitemap_url: str) -> list[str]:
    """Return list of <loc> URLs from sitemap (handles sitemap index)."""
    urls = []
    try:
        r = requests.get(sitemap_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        sys.exit(f"Failed to fetch sitemap: {e}")

    soup = BeautifulSoup(r.content, "xml")
    # If sitemap index
    if soup.find("sitemapindex"):
        for loc in soup.find_all("loc"):
            urls.extend(parse_sitemap(loc.text.strip()))
    else:
        for loc in soup.find_all("loc"):
            urls.append(loc.text.strip())
    return urls

def fetch_title(url: str) -> str | None:
    """Retrieve <title> text from page."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        title_tag = soup.find("title")
        return title_tag.text.strip() if title_tag else None
    except requests.RequestException:
        return None

def generate_post(title: str, max_tokens: int = 512) -> str:
    """Generate a blog‑style post using OpenAI GPT‑4o given a title."""
    prompt = (
        f"Write a compelling, original blog post of 800‑1000 words titled \"{title}\". "
        "The tone should be conversational and insightful, suitable for a tech‑savvy audience. "
        "Do NOT reference the original website or any copyrighted material."
    )
    # Temperature 0.8 for creativity
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # upgrade/downgrade as available
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()

def build_wxr(posts: list[dict], site_title: str, site_url: str) -> ET.Element:
    """Create base RSS/WXR Element with items for each post."""
    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
        "xmlns:wfw": "http://wellformedweb.org/CommentAPI/",
        "xmlns:dc": "http://purl.org/dc/elements/1.1/",
        "xmlns:wp": "http://wordpress.org/export/1.2/",
    })
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = site_title
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = f"Import generated posts for {site_title}"
    ET.SubElement(channel, "wp:wxr_version").text = "1.2"
    ET.SubElement(channel, "wp:author").extend([
        ET.Element("wp:author_id", text="1"),
        ET.Element("wp:author_login", text="admin"),
    ])

    for p in posts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = p["title"]
        ET.SubElement(item, "link").text = site_url.rstrip("/") + "/" + slugify(p["title"]) + "/"
        ET.SubElement(item, "pubDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        ET.SubElement(item, "dc:creator").text = "admin"
        ET.SubElement(item, "guid", isPermaLink="false").text = p["guid"]
        ET.SubElement(item, "description").text = "Generated with GPT‑4o"
        content = ET.SubElement(item, "content:encoded")
        content.text = f"<![CDATA[{p['content']}]]>"
        ET.SubElement(item, "wp:post_id").text = str(p["id"])
        ET.SubElement(item, "wp:post_type").text = "post"
        ET.SubElement(item, "wp:status").text = "publish"
    return rss

def main():
    parser = argparse.ArgumentParser(description="Generate WordPress WXR from sitemap titles via GPT")
    parser.add_argument("url", help="Base website URL (e.g. https://example.com)")
    parser.add_argument("--domain-filter", default=None, help="Substring to filter blog URLs (optional)")
    parser.add_argument("--max-posts", type=int, default=20, help="Limit number of posts to generate")
    parser.add_argument("--output", default="generated_posts.xml", help="Output WXR file path")
    args = parser.parse_args()

    sitemap_url = discover_sitemap(args.url)
    print(f"Discovered sitemap: {sitemap_url}")
    urls = parse_sitemap(sitemap_url)

    # Filter blog URLs if pattern given
    if args.domain_filter:
        urls = [u for u in urls if args.domain_filter in u]

    if not urls:
        sys.exit("No URLs found.")

    posts = []
    for i, url in enumerate(tqdm(urls[: args.max_posts], desc="Generating posts")):
        title = fetch_title(url) or f"Untitled Post {i+1}"
        content = generate_post(title)
        posts.append({
            "id": i + 1,
            "title": title,
            "content": content,
            "guid": f"{args.url.rstrip('/')}/?p={i+1}",
        })
        time.sleep(1)  # Respect rate‑limit & politeness

    rss = build_wxr(posts, site_title="Secret Hotline AI Blog", site_url=args.url)
    tree = ET.ElementTree(rss)
    Path(args.output).write_bytes(ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True))
    print(f"WXR file saved to {args.output}")

if __name__ == "__main__":
    main()
