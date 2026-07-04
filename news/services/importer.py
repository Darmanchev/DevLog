import requests
from readability import Document
from bs4 import BeautifulSoup, NavigableString, Tag
from calendar import timegm
from datetime import datetime
from datetime import UTC
import re

import feedparser

from news.models import ImportedArticle, NewsSource


DIR_BG_DONATION_PHRASES = (
    "Днес, повече от всякога, независимата журналистика има нужда от вас",
    "В мисията си да предоставяме обективни, достоверни и навременни новини",
    "разчитаме на вашата подкрепа",
    "Вашето дарение",
    "Скъпи читатели",
)


def normalize_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def is_dir_bg_donation_text(text):
    normalized = normalize_text(text)
    return any(phrase in normalized for phrase in DIR_BG_DONATION_PHRASES)


def starts_with_dir_bg_donation(text):
    normalized = normalize_text(text)
    return normalized.startswith(DIR_BG_DONATION_PHRASES[0])


def find_removable_spam_container(node):
    selected = node
    for candidate in node.parents:
        if candidate.name in {'body', 'html', '[document]'}:
            break

        text = normalize_text(candidate.get_text(' ', strip=True))
        if len(text) > 1200 or not is_dir_bg_donation_text(text):
            break

        if starts_with_dir_bg_donation(text):
            selected = candidate
        else:
            break

    return selected


def is_visual_only_node(node):
    if isinstance(node, NavigableString):
        return not node.strip()
    if not isinstance(node, Tag):
        return False
    if normalize_text(node.get_text(' ', strip=True)):
        return False
    return node.name in {'div', 'span', 'p', 'figure', 'svg', 'img', 'picture'}


def remove_adjacent_visual_nodes(node):
    for direction in ('previous_sibling', 'next_sibling'):
        sibling = getattr(node, direction)
        removed_count = 0
        while sibling and removed_count < 3:
            next_sibling = getattr(sibling, direction)
            if isinstance(sibling, NavigableString) and not sibling.strip():
                sibling.extract()
            elif is_visual_only_node(sibling):
                sibling.decompose()
                removed_count += 1
            else:
                break
            sibling = next_sibling


def normalize_actualno_showcase_blocks(soup):
    for block in soup.find_all(id='end-of-main-content'):
        text = normalize_text(block.get_text(' ', strip=True))
        link = block.find('a', string=lambda value: value and 'Google News Showcase' in value)
        if not link or 'Последвайте ни в' not in text:
            continue

        link.extract()
        link.string = normalize_text(link.get_text(' ', strip=True))
        paragraph = soup.new_tag('p')
        paragraph.append('Последвайте ни в ')
        paragraph.append(link)
        paragraph.append(', за да получавате още актуални новини.')

        block.clear()
        block.append(paragraph)


def clean_html_spam(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, 'html.parser')
    normalize_actualno_showcase_blocks(soup)
    
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
                    if is_dir_bg_donation_text(parent.get_text(' ', strip=True)):
                        nodes_to_remove.append(find_removable_spam_container(parent))
                    elif len(parent.get_text(strip=True)) < 300:
                        nodes_to_remove.append(parent)
                break
    
    for node in nodes_to_remove:
        try:
            remove_adjacent_visual_nodes(node)
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
                
            ImportedArticle.objects.create(
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

    return datetime.fromtimestamp(timegm(published), tz=UTC)


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
