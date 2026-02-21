# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys, json, requests, urllib3, utils
import xbmc
from xbmcplugin import setResolvedUrl, endOfDirectory, setContent, addDirectoryItem as add
from xbmcgui import ListItem, Dialog
from base64 import b64encode, b64decode

urllib3.disable_warnings()
session = requests.session()

BASEURL = 'https://www2.vavoo.to/ccapi/'


# ---------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------

def addDir(name, url, icon="DefaultFolder.png", isFolder=True, isPlayable=False):
    li = ListItem(name)
    li.setArt({"icon": icon, "thumb": icon})
    li.setInfo("video", {"title": name})
    if isPlayable:
        li.setProperty("IsPlayable", "true")
    add(utils.handle(), url, li, isFolder)


def addDir2(name, icon, action, **params):
    params["action"] = action
    url = utils.getPluginUrl(params)
    addDir(name, url)


def end():
    endOfDirectory(utils.handle())


# ---------------------------------------------------------
# MENÜ
# ---------------------------------------------------------

def movies_menu(params):
    setContent(utils.handle(), 'movies')
    addDir2('Beliebte Filme', 'movies', 'list', id='movie.popular')
    addDir2('Angesagte Filme', 'movies', 'list', id='movie.trending')
    #addDir2('Genres', 'genres', 'genres', id='movie.popular')
    #addDir2('Suche', 'search', 'search', id='movie.popular')
    end()


def series_menu(params):
    setContent(utils.handle(), 'tvshows')
    addDir2('Beliebte Serien', 'series', 'list', id='series.popular')
    addDir2('Angesagte Serien', 'series', 'list', id='series.trending')
    #addDir2('Genres', 'genres', 'genres', id='series.popular')
    #addDir2('Suche', 'search', 'search', id='series.popular')
    end()


# ---------------------------------------------------------
# GENRES
# ---------------------------------------------------------

def genres(params):
    base_id = params["id"]  # z.B. movie.popular oder series.popular
    content_type = "movie" if base_id.startswith("movie") else "series"

    data = cachedcall("genres", {"id": base_id})
    setContent(utils.handle(), "genres")

    for g in data.get("data", []):
        p = {
            "action": "list",
            "id": f"{content_type}.genre.{g['id']}"
        }
        li = ListItem(g["name"])
        add(utils.handle(), utils.getPluginUrl(p), li, True)

    end()


# ---------------------------------------------------------
# LISTEN / EPISODEN / STAFFELN
# ---------------------------------------------------------

def prepareListItem(params, e):
    infos = {}

    def setInfo(k, v):
        if v:
            infos[k] = ", ".join(v) if isinstance(v, list) else v

    setInfo('title', e.get('name'))
    setInfo('originaltitle', e.get('originalName'))
    setInfo('year', e.get('year'))
    setInfo('plot', e.get('description'))
    setInfo('premiered', e.get('releaseDate'))
    setInfo('genre', e.get('genres'))
    setInfo('country', e.get('country'))
    setInfo('cast', e.get('cast'))
    setInfo('director', e.get('director'))
    setInfo('writer', e.get('writer'))

    art = {
        'icon': e.get('poster'),
        'thumb': e.get('poster'),
        'poster': e.get('poster'),
        'banner': e.get('backdrop')
    }

    return infos, art


def createListItem(params, e, isPlayable=False):
    infos, art = prepareListItem(params, e)
    li = ListItem(infos.get("title", ""))
    li.setInfo("video", infos)
    li.setArt(art)
    if isPlayable:
        li.setProperty("IsPlayable", "true")
    return li


def _is_de_mirror(mirror):
    lang = str(mirror.get("language", "")).lower()
    return "de" in lang and bool(mirror.get("url"))


def _has_working_movie(content_id):
    try:
        mirrors = cachedcall('links', {'id': content_id, 'language': 'de'})
    except:
        return False

    if not isinstance(mirrors, list):
        return False

    for mirror in mirrors:
        if isinstance(mirror, dict) and _is_de_mirror(mirror):
            return True

    return False


def _has_working_series(content_id):
    try:
        info = cachedcall('info', {'id': content_id, 'language': 'de'})
    except:
        return False

    if not isinstance(info, dict):
        return False

    seasons = dict(info.get('seasons', {}))
    seasons.pop('0', None)
    if not seasons:
        return False

    checks = 0
    for season in seasons.keys():
        for ep in seasons.get(season, []):
            ep_no = str(ep.get('episode'))
            if not ep_no:
                continue

            stream_id = f"{content_id}.{season}.{ep_no}"
            try:
                mirrors = cachedcall('links', {'id': stream_id, 'language': 'de'})
            except:
                mirrors = []

            if isinstance(mirrors, list):
                for mirror in mirrors:
                    if isinstance(mirror, dict) and _is_de_mirror(mirror):
                        return True

            checks += 1
            if checks >= 3:
                return False

    return False


def list_items(params):
    data = cachedcall('list', {'id': params['id']})
    isMovie = params['id'].startswith('movie')
    only_working = utils.addon.getSettingBool('only_working_content')
    action = 'get' if isMovie else 'seasons'
    content = 'movies' if isMovie else 'tvshows'

    setContent(utils.handle(), content)

    for e in data.get('data', []):
        content_id = e.get('id')
        if not content_id:
            continue

        if only_working:
            if isMovie and not _has_working_movie(content_id):
                continue
            if not isMovie and not _has_working_series(content_id):
                continue

        urlParams = {'action': action, 'id': e['id']}
        li = createListItem(urlParams, e, isPlayable=isMovie)
        add(utils.handle(), utils.getPluginUrl(urlParams), li, not isMovie)

    end()


def seasons(params):
    data = cachedcall('info', {'id': params['id'], "language": "de"})
    data['seasons'].pop('0', None)

    setContent(utils.handle(), 'seasons')

    for season in data['seasons'].keys():
        p = {'action': 'episodes', 'id': params['id'], 'season': season}
        li = createListItem(p, data)
        add(utils.handle(), utils.getPluginUrl(p), li, True)

    end()


def episodes(params):
    data = cachedcall('info', {'id': params['id'], "language": "de"})
    season = str(params['season'])

    setContent(utils.handle(), 'episodes')

    for ep in data['seasons'][season]:
        data['current_episode'] = ep
        p = {
            'action': 'get',
            'id': params['id'],
            'season': season,
            'episode': str(ep["episode"])
        }
        li = createListItem(p, data, isPlayable=True)
        add(utils.handle(), utils.getPluginUrl(p), li, False)

    end()


# ---------------------------------------------------------
# STREAM RESOLVER
# ---------------------------------------------------------

class get_stream(object):
    def __init__(self, params):
        if params.get('episode'):
            self.params = {
                'id': f"{params['id']}.{params['season']}.{params['episode']}",
                "language": "de"
            }
        else:
            self.params = {'id': params['id'], "language": "de"}

        self.data = cachedcall('info', {'id': params['id'], "language": "de"})
        self.run()

    def run(self):
        mirrors = cachedcall('links', self.params)
        if not mirrors:
            xbmc.executebuiltin('Notification(VAVOO,Keine Streams gefunden,5000)')
            return

        new = []
        for i, m in enumerate(mirrors, start=1):
            if 'de' not in m['language']:
                continue

            m['hoster'] = utils.urlparse(m['url']).netloc
            quality = m['name']

            if "1080" in quality:
                w = 1080
            elif "720" in quality:
                w = 720
            elif "480" in quality:
                w = 480
            elif "360" in quality:
                w = 360
            else:
                w = 1

            m['weight'] = w
            m['name'] = f"{i}. {m['hoster']} {quality}"
            new.append(m)

        new = sorted(new, key=lambda x: x['weight'], reverse=True)

        if utils.addon.getSetting('stream_select') == '0':
            captions = [m['name'] for m in new]
            index = Dialog().select("VAVOO", captions)
            if index < 0:
                return
            mirrors = [new[index]]
        else:
            mirrors = new

        for m in mirrors:
            res = callApi2('open', {'link': m['url']})
            if not res:
                continue

            r = session.get(res[-1].get('url'), stream=True, verify=False)
            if "text" in r.headers.get('Content-Type', "text"):
                continue

            url = r.url
            li = createListItem(self.params, self.data, isPlayable=True)
            li.setPath(url)
            li.setProperty("IsPlayable", "true")

            use_inputstream = utils.addon.getSettingBool("use_inputstream")
            use_adaptive = utils.addon.getSettingBool("use_inputstream_adaptive")
            use_ffmpegdirect = utils.addon.getSettingBool("use_inputstream_ffmpegdirect")
            has_adaptive = xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)")
            has_ffmpegdirect = xbmc.getCondVisibility("System.HasAddon(inputstream.ffmpegdirect)")

            if ".m3u8" in url:
                li.setMimeType("application/vnd.apple.mpegurl")
                li.setContentLookup(False)
                if use_inputstream:
                    if use_adaptive and has_adaptive:
                        li.setProperty("inputstream", "inputstream.adaptive")
                        li.setProperty("inputstreamaddon", "inputstream.adaptive")
                        li.setProperty("inputstream.adaptive.manifest_type", "hls")
                    elif use_ffmpegdirect and has_ffmpegdirect:
                        li.setProperty("inputstream", "inputstream.ffmpegdirect")
                        li.setProperty("inputstreamaddon", "inputstream.ffmpegdirect")
                    elif has_adaptive:
                        li.setProperty("inputstream", "inputstream.adaptive")
                        li.setProperty("inputstreamaddon", "inputstream.adaptive")
                        li.setProperty("inputstream.adaptive.manifest_type", "hls")
                    elif has_ffmpegdirect:
                        li.setProperty("inputstream", "inputstream.ffmpegdirect")
                        li.setProperty("inputstreamaddon", "inputstream.ffmpegdirect")

            setResolvedUrl(utils.handle(), True, li)
            return


# ---------------------------------------------------------
# API / CACHE
# ---------------------------------------------------------

def cachedcall(action, params):
    key = action + '?' + '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    c = utils.get_cache(key)
    if c:
        return c
    c = callApi2(action, params)
    utils.set_cache(key, c)
    return c


def callApi(action, params, method='GET', headers=None, **kwargs):
    if not headers:
        headers = {}

    token = utils.getAuthSignature()
    if token:
        headers['auth-token'] = token

    r = session.request(method, BASEURL + action, params=params, headers=headers, verify=False)

    if r.status_code >= 500 and 'auth error' in r.text.lower():
        new_token = utils.getAuthSignature(force_refresh=True)
        if new_token and new_token != token:
            headers['auth-token'] = new_token
            r = session.request(method, BASEURL + action, params=params, headers=headers, verify=False)

    r.raise_for_status()
    return r.json()


def callApi2(action, params):
    res = callApi(action, params)
    while True:
        if not isinstance(res, dict) or 'id' not in res or 'data' not in res:
            return res

        data = res['data']

        if isinstance(data, dict) and data.get('type') == 'fetch':
            fetch = data['params']
            method = fetch.get('method', 'GET').upper()
            headers = fetch.get('headers', {})
            body = fetch.get('body')
            if body:
                body = b64decode(body)

            r = session.request(
                method,
                data['url'],
                headers={k: (v[0] if isinstance(v, list) else v) for k, v in headers.items()},
                data=body,
                allow_redirects=True,
                verify=False
            )

            resData = {
                "status": r.status_code,
                "url": r.url,
                "headers": dict(r.headers),
                "data": b64encode(r.content).decode("utf-8") if data.get("body") else None
            }

            res = callApi("res", {"id": res["id"]}, method="POST", json=resData)

        else:
            return data


# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------

def router(params):
    action = params.get("action")

    if action == "movies_menu":
        movies_menu(params)
    elif action == "series_menu":
        series_menu(params)
    elif action == "list":
        list_items(params)
    elif action == "seasons":
        seasons(params)
    elif action == "episodes":
        episodes(params)
    elif action == "get":
        get_stream(params)
    elif action == "genres":
        genres(params)
