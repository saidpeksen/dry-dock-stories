"""plan.json denetimi. Kullanım: python3 -I araclar/plan_denetle.py plan.json

Plan, durum dosyasıyla aynı depodaki `plan.json` dosyasında durur (adres durum kaynağından türetilir:
`…/<sahip>/<depo>/main/plan.json`). Sunucu onu durum dosyasıyla birlikte okur, doğrular ve son geçerli kopyayı
saklar. Plan okunamazsa durum etkilenmez. İçerik güvenilmez kabul edilir: her alan tür, uzunluk ve biçim
denetiminden geçer, bilinmeyen alanlar atılır. Sunucu planı değiştirmez; planı üretim hattı yazar.
"""
import datetime
import json
import re

CONTROL = re.compile(r'[\x00-\x1f\x7f]')
YOUTUBE = re.compile(r'https://(?:(?:www\.)?youtube\.com/(?:shorts/|watch\?v=)|youtu\.be/)[A-Za-z0-9_-]{6,20}')
MAX_BYTES = 60_000


def plan_url(source):
    """Durum kaynağından plan adresini türetir."""
    if not isinstance(source, str) or not source.endswith('/main/durum.json'):
        raise ValueError('Durum kaynağı tanınmıyor.')
    return source[:-len('durum.json')] + 'plan.json'


def initialize(con):
    cols = {r[1] for r in con.execute('PRAGMA table_info(youtube_office)')}
    for col in ('plan', 'plan_fetched_at', 'plan_error'):
        if col not in cols:
            con.execute('ALTER TABLE youtube_office ADD COLUMN %s TEXT' % col)


def _text(v, name, limit, required=True):
    if v is None and not required:
        return None
    if not isinstance(v, str) or CONTROL.search(v):
        raise ValueError('%s düz metin olmalı.' % name)
    v = ' '.join(v.split())
    if not v:
        if required:
            raise ValueError('%s gerekli.' % name)
        return None
    if len(v) > limit:
        raise ValueError('%s en fazla %d karakter.' % (name, limit))
    return v


def _list(v, name, limit, required=False):
    if v is None and not required:
        return []
    if not isinstance(v, list) or len(v) > limit:
        raise ValueError('%s en çok %d satırlık bir liste olmalı.' % (name, limit))
    return v


def _date(v, name, required=False):
    if v is None and not required:
        return None
    if not isinstance(v, str) or len(v) > 40:
        raise ValueError('%s tarih olmalı (YYYY-AA-GG).' % name)
    try:
        if len(v) == 10:
            return datetime.date.fromisoformat(v).isoformat()
        parsed = datetime.datetime.fromisoformat(v.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('%s tarih olmalı (YYYY-AA-GG).' % name)
    if parsed.tzinfo is None:
        raise ValueError('%s saat dilimi içermeli.' % name)
    return parsed.astimezone(datetime.timezone.utc).isoformat(timespec='seconds')


def _number(v, name, low, high):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not low <= v <= high:
        raise ValueError('%s %s–%s arasında bir sayı olmalı.' % (name, low, high))
    return v


def _obj(v, name):
    if not isinstance(v, dict):
        raise ValueError('%s bir nesne olmalı.' % name)
    return v


def parse(raw):
    """Plan dosyasının baytlarını doğrular; panelin göstereceği sade yapıyı döner."""
    if not isinstance(raw, (bytes, bytearray)) or len(raw) > MAX_BYTES:
        raise ValueError('Plan dosyası fazla büyük.')
    try:
        data = json.loads(bytes(raw).decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        raise ValueError('Plan dosyası geçerli JSON değil.')
    if not isinstance(data, dict) or data.get('schema') != 1 or data.get('kind') != 'plan':
        raise ValueError('Plan dosyası tanınmıyor (schema 1, kind "plan" bekleniyor).')
    now = _obj(data.get('now') or {}, 'now')
    out = {'updated_at': _date(data.get('updated_at'), 'updated_at', True),
           'title': _text(data.get('title'), 'title', 100, False),
           'goal': _text(data.get('goal'), 'goal', 500, False),
           'now': {'summary': _text(now.get('summary'), 'now.summary', 500, False),
                   'next': [_text(x, 'now.next', 240) for x in _list(now.get('next'), 'now.next', 10)]},
           'calendar': [], 'phases': [], 'videos': [], 'thresholds': [], 'open': []}
    for x in _list(data.get('calendar'), 'calendar', 30):
        x = _obj(x, 'calendar')
        out['calendar'].append({'date': _date(x.get('date'), 'calendar.date', True), 'what': _text(x.get('what'), 'calendar.what', 240),
                                'you': _text(x.get('you'), 'calendar.you', 160, False)})
    for p in _list(data.get('phases'), 'phases', 10):
        p = _obj(p, 'phases')
        items = []
        for i in _list(p.get('items'), 'phases.items', 30):
            i = _obj(i, 'phases.items')
            if not isinstance(i.get('done', False), bool):
                raise ValueError('phases.items.done true ya da false olmalı.')
            items.append({'text': _text(i.get('text'), 'phases.items.text', 200), 'done': i.get('done', False)})
        out['phases'].append({'title': _text(p.get('title'), 'phases.title', 100), 'period': _text(p.get('period'), 'phases.period', 80, False),
                              'note': _text(p.get('note'), 'phases.note', 400, False), 'current': p.get('current') is True,
                              'items': items, 'done_count': sum(1 for i in items if i['done'])})
    for v in _list(data.get('videos'), 'videos', 200):
        v = _obj(v, 'videos')
        no = v.get('no')
        if isinstance(no, bool) or not isinstance(no, int) or not 1 <= no <= 999:
            raise ValueError('videos.no 1–999 arasında bir tam sayı olmalı.')
        url = v.get('youtube_url')
        if url is not None and (not isinstance(url, str) or not YOUTUBE.fullmatch(url)):
            raise ValueError('videos.youtube_url yalnız bir YouTube video adresi olabilir.')
        out['videos'].append({'no': no, 'topic': _text(v.get('topic'), 'videos.topic', 80), 'opening': _text(v.get('opening'), 'videos.opening', 60, False),
                              'published': _date(v.get('published'), 'videos.published'), 'youtube_url': url,
                              'views_48h': _number(v.get('views_48h'), 'videos.views_48h', 0, 10**9),
                              'views_total': _number(v.get('views_total'), 'videos.views_total', 0, 10**9),
                              'viewed_pct': _number(v.get('viewed_pct'), 'videos.viewed_pct', 0, 100),
                              'avg_view_pct': _number(v.get('avg_view_pct'), 'videos.avg_view_pct', 0, 1000),
                              'likes': _number(v.get('likes'), 'videos.likes', 0, 10**9),
                              'subscribers': _number(v.get('subscribers'), 'videos.subscribers', -10**6, 10**9),
                              'note': _text(v.get('note'), 'videos.note', 300, False)})
    out['videos'].sort(key=lambda v: -v['no'])
    for t in _list(data.get('thresholds'), 'thresholds', 10):
        t = _obj(t, 'thresholds')
        out['thresholds'].append({'name': _text(t.get('name'), 'thresholds.name', 80), 'need': _text(t.get('need'), 'thresholds.need', 200),
                                  'unlocks': _text(t.get('unlocks'), 'thresholds.unlocks', 160, False)})
    out['open'] = [_text(x, 'open', 200) for x in _list(data.get('open'), 'open', 20)]
    return out


def store(con, source, plan, error, stamp):
    """Plan okumasını yazar. Hatalı okumada son geçerli kopya korunur. Kaynak bu arada değiştiyse yazmaz."""
    if plan is not None:
        con.execute('UPDATE youtube_office SET plan=?, plan_fetched_at=?, plan_error=NULL WHERE id=1 AND source=?',
                    (json.dumps(plan, ensure_ascii=False), stamp, source))
    else:
        con.execute('UPDATE youtube_office SET plan_error=? WHERE id=1 AND source=?', (error, source))


def clear(con):
    con.execute('UPDATE youtube_office SET plan=NULL, plan_fetched_at=NULL, plan_error=NULL WHERE id=1')


def read(con):
    plan, fetched, error = con.execute('SELECT plan, plan_fetched_at, plan_error FROM youtube_office WHERE id=1').fetchone()
    return {'plan': json.loads(plan) if plan else None, 'plan_fetched_at': fetched, 'plan_error': error}


if __name__ == '__main__':
    import sys
    try:
        d = parse(open(sys.argv[1], 'rb').read())
    except (ValueError, OSError, IndexError) as exc:
        print('HATA: %s' % exc)
        sys.exit(1)
    print('plan.json geçerli: %d aşama, %d video, %d takvim satırı' % (len(d['phases']), len(d['videos']), len(d['calendar'])))
