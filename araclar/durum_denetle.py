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
SHA = re.compile(r'[0-9a-f]{64}')
STAGES = ('siparis', 'kurgu', 'onay', 'duzeltme', 'beklemede', 'yayin', 'yayinda')
TIMES = ('ordered_at', 'ready_at', 'approved_at', 'published_at')
MAX_BYTES, MAX_VIDEOS, MAX_TASKS = 60_000, 60, 20
TASK_KEY = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+){0,7}')
WINDOWS = ('09.30', '19.00')


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
        size, sha = x.get('bytes'), x.get('sha256')
        if size is not None and (isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= 300_000_000):
            raise ValueError('%s: bytes 1–300.000.000 arasında tam sayı olmalı.' % slug)
        if sha is not None and (not isinstance(sha, str) or not SHA.fullmatch(sha)):
            raise ValueError('%s: sha256 64 haneli küçük harfli onaltılık olmalı.' % slug)
        if x['stage'] == 'onay' and (size is None or sha is None):
            raise ValueError('%s: onay bekleyen videoda bytes ve sha256 gerekli (sitedeki karar düğmeleri bunlara bağlı).' % slug)
        for key in TIMES:
            when(x.get(key), slug + ': ' + key)
    tasks = data.get('tasks')
    if tasks is not None:
        if not isinstance(tasks, list) or len(tasks) > MAX_TASKS:
            raise ValueError('tasks en fazla %d satırlık bir liste olmalı.' % MAX_TASKS)
        ids = set()
        for t in tasks:
            if not isinstance(t, dict):
                raise ValueError('tasks içindeki her satır bir nesne olmalı.')
            key = t.get('id')
            if not isinstance(key, str) or len(key) > 60 or not TASK_KEY.fullmatch(key):
                raise ValueError('%r: tasks.id küçük harf, rakam ve tireden oluşmalı.' % (key,))
            if key in ids:
                raise ValueError('%s: görev iki kez yazılmış.' % key)
            ids.add(key)
            text(t.get('title'), key + ': title', 140)
            due = t.get('due')
            if due is not None:
                try:
                    ok = isinstance(due, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', due) and datetime.date.fromisoformat(due)
                except ValueError:
                    ok = False
                if not ok:
                    raise ValueError('%s: due YYYY-AA-GG biçiminde olmalı.' % key)
            if t.get('window') not in (None,) + WINDOWS:
                raise ValueError('%s: window yalnız 09.30 ya da 19.00 olabilir.' % key)
            if t.get('done') not in (None, True, False):
                raise ValueError('%s: done true ya da false olmalı.' % key)
            when(t.get('done_at'), key + ': done_at')
    return len(videos)


if __name__ == '__main__':
    try:
        n = check(open(sys.argv[1], 'rb').read())
    except (ValueError, OSError, IndexError) as exc:
        print('HATA: %s' % exc)
        sys.exit(1)
    print('durum.json geçerli: %d video' % n)
