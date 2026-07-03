import requests
from readability import Document
from bs4 import BeautifulSoup
from datetime import datetime
from time import mktime

import feedparser
from django.db import transaction
from django.utils import timezone

from news.models import ImportedArticle, NewsSource

def clean_html_spam(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    spam_texts = [
        "Днес, повече от всякога",
        "В мисията си да предоставяме",
        "Ако вярвате в правото",
        "Вашето дарение",
        "Скъпи читатели"
    ]
    
    nodes_to_remove = []
    for text_node in soup.find_all(string=True):
        for spam in spam_texts:
            if spam in text_node:
                parent = text_node.parent
                if parent and parent.name in ['p', 'span', 'strong', 'em', 'b', 'i', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if len(parent.get_text(strip=True)) < 300:
                        nodes_to_remove.append(parent)
                break
    
    for node in nodes_to_remove:
        try:
            node.decompose()
        except Exception:
            pass
            
    for empty_p in soup.find_all('p'):
        if not empty_p.get_text(strip=True) and not empty_p.find('img'):
            empty_p.decompose()

    if soup.body:
        return "".join(str(tag) for tag in soup.body.children)
    else:
        return "".join(str(tag) for tag in soup.contents)



def import_source(source):
    if source.source_type != NewsSource.SourceType.RSS:
        raise ValueError('Only RSS sources are supported for now.')

    feed = feedparser.parse(source.url)

    created_count = 0
    skipped_count = 0

    for entry in feed.entries:
        article_url = entry.get('link')

        if not article_url:
            skipped_count += 1
            continue

        
        # Determine if we need to create it first
        if not ImportedArticle.objects.filter(url=article_url).exists():
            full_text = ""
            try:
                # Fetch full article text
                response = requests.get(article_url, timeout=10)
                if response.status_code == 200:
                    doc = Document(response.text)
                    raw_html = doc.summary()
                    full_text = clean_html_spam(raw_html)
            except Exception as e:
                print(f"Failed to fetch full text for {article_url}: {e}")
                
            article = ImportedArticle.objects.create(
                url=article_url,
                source=source,
                title=entry.get('title', '')[:255],
                summary=clean_html_spam(entry.get('summary', '')),
                full_text=full_text,
                source_category=get_entry_source_category(entry),
                image_url=get_entry_image_url(entry),
                published_at=get_entry_published_at(entry),
                status=ImportedArticle.Status.PUBLISHED,
            )
            created = True
        else:
            article = ImportedArticle.objects.get(url=article_url)
            created = False

        if created:
            created_count += 1
        else:
            skipped_count += 1


    return {
        'created': created_count,
        'skipped': skipped_count,
    }

def get_entry_published_at(entry):
    published = entry.get('published_parsed') or entry.get('updated_parsed')

    if not published:
        return None

    naive_datetime = datetime.fromtimestamp(mktime(published))
    return timezone.make_aware(naive_datetime)

import re

def get_entry_image_url(entry):
    media_content = entry.get('media_content')
    if media_content:
        return media_content[0].get('url', '')

    media_thumbnail = entry.get('media_thumbnail')
    if media_thumbnail:
        return media_thumbnail[0].get('url', '')
        
    # Check enclosures (used by Dir.bg, bTV, etc.)
    for link in entry.get('links', []):
        if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
            return link.get('href', '')
            
    # Check <img> tags inside summary (used by 24 Chasa, Vesti.bg, etc.)
    summary = entry.get('summary', '')
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary, re.IGNORECASE)
    if img_match:
        return img_match.group(1)

    return ''

def get_entry_source_category(entry):
    category = entry.get('category')

    if category:
        return category[:50]

    tags = entry.get('tags', [])

    if tags:
        return tags[0].get('term', '')[:50]

    return ''