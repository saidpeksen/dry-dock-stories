#!/usr/bin/env python3
"""durum.json denetimi. Kullanım: python3 -I araclar/durum_denetle.py durum.json
Kurallar, durumu gösteren sitenin kabul ettiği biçimle aynıdır; geçmeyen dosya sitede görünmez."""
import datetime
import json
import re
import sys

SLUG = re.compile(r'[0-9]{2,3}-[a-z0-9]+(?:-[a-z0-9]+){0,7}')
YOUTUBE = re.compile(r'https://(?:(?:www\.)?youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)[A-Za-z0-9_-]{6,20}')
CONTROL = re.compile(r'[\x00-\x1f\x7f]')
STAGES = ('siparis', 'kurgu', 'onay', 'duzeltme', 'beklemede', 'yayin', 'yayinda')
TIMES = ('ordered_at', 'ready_at', 'approved_at', 'published_at')
MAX_BYTES, MAX_VIDEOS = 60_000, 60


def text(v, name, limit, required=True):
    if v is None and not required:
        return
    if not isinstance(v, str) or CONTROL.search(v):
        raise ValueError('%s düz metin olmalı.' % name)
    if required and not v.strip():
        raise ValueError('%s gerekli.' % name)
    if len(' '.join(v.split())) > limit:
        raise ValueError('%s en fazla %d karakter.' % (name, limit))


def when(v, name, required=False):
    if v is None and not required:
        return
    try:
        parsed = datetime.datetime.fromisoformat(v.replace('Z', '+00:00')) if isinstance(v, str) and len(v) <= 40 else None
    except ValueError:
        parsed = None
    if parsed is None or parsed.tzinfo is None:
        raise ValueError('%s saat dilimli ISO tarih olmalı (ör. 2026-11-21T08:30:00Z).' % name)


def check(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('Dosya %d bayttan büyük.' % MAX_BYTES)
    data = json.loads(raw.decode('utf-8'))
    if not isinstance(data, dict) or data.get('schema') != 1:
        raise ValueError('schema 1 olmalı.')
    when(data.get('updated_at'), 'updated_at', True)
    text(data.get('channel'), 'channel', 60, False)
    text(data.get('note'), 'note', 300, False)
    runs = data.get('runs') if data.get('runs') is not None else {}
    if not isinstance(runs, dict):
        raise ValueError('runs bir nesne olmalı.')
    for name in ('claude', 'chatgpt'):
        when(runs.get(name), 'runs.' + name)
    videos = data.get('videos')
    if not isinstance(videos, list) or len(videos) > MAX_VIDEOS:
        raise ValueError('videos en fazla %d satırlık bir liste olmalı.' % MAX_VIDEOS)
    seen = set()
    for x in videos:
        if not isinstance(x, dict):
            raise ValueError('Her video bir nesne olmalı.')
        no, slug = x.get('no'), x.get('slug')
        if isinstance(no, bool) or not isinstance(no, int) or not 1 <= no <= 999:
            raise ValueError('no 1–999 arasında tam sayı olmalı.')
        if not isinstance(slug, str) or len(slug) > 48 or not SLUG.fullmatch(slug):
            raise ValueError('%r: slug "NN-kisa-ad" biçiminde olmalı.' % (slug,))
        if no in seen or slug in seen:
            raise ValueError('%s iki kez yazılmış.' % slug)
        seen.update((no, slug))
        if x.get('stage') not in STAGES:
            raise ValueError('%s: stage şunlardan biri olmalı: %s' % (slug, ', '.join(STAGES)))
        text(x.get('topic'), slug + ': topic', 80)
        text(x.get('title'), slug + ': title', 100, False)
        text(x.get('hook'), slug + ': hook', 240, False)
        yt = x.get('youtube_url')
        if yt is not None and (not isinstance(yt, str) or not YOUTUBE.fullmatch(yt)):
            raise ValueError('%s: youtube_url yalnız bir YouTube video adresi olabilir.' % slug)
        if x['stage'] == 'yayinda' and not yt:
            raise ValueError('%s: yayındaki videonun youtube_url alanı gerekli.' % slug)
        sec = x.get('seconds')
        if sec is not None and (isinstance(sec, bool) or not isinstance(sec, (int, float)) or not 1 <= sec <= 3600):
            raise ValueError('%s: seconds 1–3600 arasında sayı olmalı.' % slug)
        if x.get('video') not in (None, True, False):
            raise ValueError('%s: video true ya da false olmalı.' % slug)
        for key in TIMES:
            when(x.get(key), slug + ': ' + key)
    return len(videos)


if __name__ == '__main__':
    try:
        n = check(open(sys.argv[1], 'rb').read())
    except (ValueError, OSError, IndexError) as exc:
        print('HATA: %s' % exc)
        sys.exit(1)
    print('durum.json geçerli: %d video' % n)
