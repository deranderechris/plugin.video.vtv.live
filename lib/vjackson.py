# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys, re, json, requests, urllib.parse
import xbmc, xbmcgui, xbmcplugin
import utils

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
CATALOG_URL = "https://vavoo.to/vto-cluster/mediahubmx-catalog.json"
RESOLVE_URL = "https://vavoo.to/vto-cluster/mediahubmx-resolve.json"

groups = {}

# Flaggen
FLAG_DE_ALL = "special://home/addons/plugin.video.vtv.live/flags/country/de.png"
FLAG_DE_SKY = "special://home/addons/plugin.video.vtv.live/flags/country/de_sky.png"
FLAG_DE_SPORT = "special://home/addons/plugin.video.vtv.live/flags/country/de_sport.png"
FLAG_DE_KINDER = "special://home/addons/plugin.video.vtv.live/flags/country/de_kinder.png"
FLAG_DE_DOKU = "special://home/addons/plugin.video.vtv.live/flags/country/de_doku.png"
FLAG_DE_RTL = "special://home/addons/plugin.video.vtv.live/flags/country/de_rtl.png"
FLAG_DE_P7S1 = "special://home/addons/plugin.video.vtv.live/flags/country/de_p7s1.png"
FLAG_DE_OEFF = "special://home/addons/plugin.video.vtv.live/flags/country/de_oeffentlich.png"
FLAG_DE_MUSIK = "special://home/addons/plugin.video.vtv.live/flags/country/de_musik.png"
FLAG_DE_BACKUP = "special://home/addons/plugin.video.vtv.live/flags/country/de_backup.png"
FLAG_DE_QUALI = "special://home/addons/plugin.video.vtv.live/flags/country/de_qualitaet.png"

GROUP_ICONS = {
    "Germany – Alle Sender": FLAG_DE_ALL,
    "Germany – Sky": FLAG_DE_SKY,
    "Germany – Sport": FLAG_DE_SPORT,
    "Germany – Kinder": FLAG_DE_KINDER,
    "Germany – Doku": FLAG_DE_DOKU,
    "Germany – RTL": FLAG_DE_RTL,
    "Germany – ProSiebenSat1": FLAG_DE_P7S1,
    "Germany – Öffentlich‑rechtlich": FLAG_DE_OEFF,
    "Germany – Musik": FLAG_DE_MUSIK,
    "Germany – Backup": FLAG_DE_BACKUP,
    "Germany – Qualität": FLAG_DE_QUALI
}

def _headers():
    return {
        "accept-encoding": "gzip",
        "user-agent": "MediaHubMX/2",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "mediahubmx-signature": utils.getAuthSignature()
    }

def _fetch_catalog():
    global groups
    if groups:
        return
    cursor = 0
    groups = {}
    while True:
        payload = {
            "language": "de",
            "region": "AT",
            "catalogId": "vto-iptv",
            "id": "vto-iptv",
            "adult": False,
            "search": "",
            "sort": "name",
            "filter": {},
            "cursor": cursor,
            "clientVersion": "3.0.2"
        }
        r = requests.post(CATALOG_URL, data=json.dumps(payload), headers=_headers(), timeout=10)
        data = r.json()
        for item in data.get("items", []):
            group = item.get("group") or "Other"
            name = item.get("name") or "Unknown"
            name = re.sub(r'( (SD|HD|FHD|UHD|H265))?( \(BACKUP\))? \(\d+\)$', '', name)
            groups.setdefault(group, {}).setdefault(name, []).append(item)
        cursor = data.get("nextCursor")
        if not cursor:
            break

def _resolve(url):
    payload = {
        "language": "de",
        "region": "AT",
        "url": url,
        "clientVersion": "3.0.2"
    }
    r = requests.post(RESOLVE_URL, data=json.dumps(payload), headers=_headers(), timeout=10)
    data = r.json()
    if isinstance(data, list) and data:
        return data[0].get("url")
    raise ValueError("Stream konnte nicht aufgelöst werden")

def _url(params):
    return sys.argv[0] + "?" + urllib.parse.urlencode(params)

def _show_groups():
    _fetch_catalog()
    order = [
        "Germany – Alle Sender",
        "Germany – Sky",
        "Germany – Sport",
        "Germany – Kinder",
        "Germany – Doku",
        "Germany – RTL",
        "Germany – ProSiebenSat1",
        "Germany – Öffentlich‑rechtlich",
        "Germany – Musik",
        "Germany – Backup",
        "Germany – Qualität"
    ]
    for g in order:
        li = xbmcgui.ListItem(label=g)
        icon = GROUP_ICONS.get(g)
        li.setArt({"icon": icon, "thumb": icon})
        xbmcplugin.addDirectoryItem(HANDLE, _url({"mode": "channels", "group": g}), li, True)
    xbmcplugin.endOfDirectory(HANDLE)

def _match_group(name, group):
    n = name.lower()
    g = group.lower()
    if "alle sender" in g: return True
    if "sky" in g and "sky" in n: return True
    if "sport" in g and "sport" in n: return True
    if "kinder" in g and ("kinder" in n or "kids" in n): return True
    if "doku" in g and "doku" in n: return True
    if "rtl" in g and "rtl" in n: return True
    if "prosiebensat1" in g and ("prosieben" in n or "sat" in n): return True
    if "öffentlich" in g and ("ard" in n or "zdf" in n): return True
    if "musik" in g and ("musik" in n or "music" in n): return True
    if "backup" in g and "backup" in n: return True
    if "qualität" in g and ("hd" in n or "fhd" in n or "uhd" in n): return True
    return False

def _show_channels(group):
    _fetch_catalog()
    items = []
    if group.startswith("Germany"):
        for name, lst in groups.get("Germany", {}).items():
            if _match_group(name, group):
                items.extend(lst)
    else:
        for name, lst in groups.get(group, {}).items():
            items.extend(lst)

    for item in items:
        name = item.get("name")
        url_raw = item.get("url")

        logo = FLAG_DE_ALL

        li = xbmcgui.ListItem(label=name)
        li.setArt({"icon": logo, "thumb": logo})
        li.setProperty("IsPlayable", "true")
        li.setInfo("video", {"title": name})

        xbmcplugin.addDirectoryItem(
            HANDLE,
            _url({"mode": "play", "url": url_raw, "name": name}),
            li,
            False
        )

    xbmcplugin.endOfDirectory(HANDLE)

def _play(url, name):
    try:
        stream = _resolve(url)
    except:
        xbmcgui.Dialog().ok("Live TV", "Stream konnte nicht aufgelöst werden.")
        return

    li = xbmcgui.ListItem(label=name, path=stream)
    li.setProperty("IsPlayable", "true")
    li.setInfo("video", {"title": name})

    use_inputstream = utils.addon.getSettingBool("use_inputstream")
    use_adaptive = utils.addon.getSettingBool("use_inputstream_adaptive")
    use_ffmpegdirect = utils.addon.getSettingBool("use_inputstream_ffmpegdirect")
    has_adaptive = xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)")
    has_ffmpegdirect = xbmc.getCondVisibility("System.HasAddon(inputstream.ffmpegdirect)")

    # ⭐ Fire‑TV‑Fix
    if ".m3u8" in stream:
        li.setMimeType("application/vnd.apple.mpegurl")
        li.setContentLookup(False)

        if use_inputstream:
            if use_adaptive and has_adaptive:
                li.setProperty("inputstream", "inputstream.adaptive")
                li.setProperty("inputstreamaddon", "inputstream.adaptive")
                li.setProperty("inputstream.adaptive.manifest_type", "hls")
                li.setProperty("inputstream.adaptive.stream_headers", "User-Agent=MediaHubMX/2&Accept=*/*")
            elif use_ffmpegdirect and has_ffmpegdirect:
                li.setProperty("inputstream", "inputstream.ffmpegdirect")
                li.setProperty("inputstreamaddon", "inputstream.ffmpegdirect")
            elif has_adaptive:
                li.setProperty("inputstream", "inputstream.adaptive")
                li.setProperty("inputstreamaddon", "inputstream.adaptive")
                li.setProperty("inputstream.adaptive.manifest_type", "hls")
                li.setProperty("inputstream.adaptive.stream_headers", "User-Agent=MediaHubMX/2&Accept=*/*")
            elif has_ffmpegdirect:
                li.setProperty("inputstream", "inputstream.ffmpegdirect")
                li.setProperty("inputstreamaddon", "inputstream.ffmpegdirect")

    xbmcplugin.setResolvedUrl(HANDLE, True, li)

def router(params):
    mode = params.get("mode")
    if mode is None or mode == "livetv":
        _show_groups()
    elif mode == "channels":
        _show_channels(params.get("group"))
    elif mode == "play":
        _play(params.get("url"), params.get("name"))
