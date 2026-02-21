# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import json
import requests
import urllib.parse
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

HANDLE = int(sys.argv[1])
SYSADDON = sys.argv[0]
ADDON = xbmcaddon.Addon()
CATALOG_URL = "https://vavoo.to/mediahubmx-catalog.json"
CHANNELS_CACHE = None


def build_url(params):
    return SYSADDON + "?" + urllib.parse.urlencode(params)


def normalize_name(raw_name):
    name = (raw_name or "").strip()
    name = re.sub(r"^\[[^\]]+\]\s*", "", name)
    name = re.sub(r"\s+\.[a-z]$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+\(\d+\)$", "", name)
    return name.strip()


def add_channel_url(chans, name, url):
    if not name or not url:
        return
    if name not in chans:
        chans[name] = []
    if url not in chans[name]:
        chans[name].append(url)


def get_selected_groups():
    raw = ADDON.getSetting("country_groups")
    if not raw:
        return []
    try:
        groups = json.loads(raw)
    except:
        return []
    return groups if isinstance(groups, list) else []


def get_available_groups():
    groups = []
    try:
        data = requests.get("https://www2.vavoo.to/live2/index?output=json", timeout=10).json()
    except:
        data = []

    for item in data:
        group = item.get("group")
        if group and group not in groups:
            groups.append(group)

    return groups


def choose_countries_popup():
    global CHANNELS_CACHE

    groups = get_available_groups()
    if not groups:
        xbmcgui.Dialog().notification("Fehler", "Keine Gruppen gefunden", xbmcgui.NOTIFICATION_ERROR)
        return

    old = get_selected_groups()
    preselect = [groups.index(group) for group in old if group in groups]

    selected = xbmcgui.Dialog().multiselect("Länder wählen", groups, preselect=preselect)
    if selected is None:
        return

    chosen = [groups[i] for i in selected]
    ADDON.setSetting("country_groups", json.dumps(chosen))
    CHANNELS_CACHE = None

    if chosen:
        msg = "Gruppen gespeichert: %d" % len(chosen)
    else:
        msg = "Alle Gruppen aktiv"
    xbmcgui.Dialog().notification("Welt TV", msg, xbmcgui.NOTIFICATION_INFO)


def load_channels_from_index(chans):
    selected_groups = get_selected_groups()

    try:
        data = requests.get("https://www2.vavoo.to/live2/index?output=json", timeout=10).json()
    except:
        data = []

    for item in data:
        if selected_groups:
            group = item.get("group")
            if group not in selected_groups:
                continue

        name = normalize_name(item.get("name", ""))
        add_channel_url(chans, name, item.get("url"))


def load_channels_from_catalog(chans):
    import utils
    h = {
        "accept-encoding": "gzip",
        "user-agent": "MediaHubMX/2",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "mediahubmx-signature": utils.getAuthSignature()
    }

    selected_groups = get_selected_groups()
    group_filters = selected_groups if selected_groups else [None]

    for group_filter in group_filters:
        cursor = 0
        while cursor is not None:
            d = {
                "language": "de",
                "region": "AT",
                "catalogId": "iptv",
                "id": "iptv",
                "adult": False,
                "search": "",
                "sort": "name",
                "filter": {"group": group_filter} if group_filter else {},
                "cursor": cursor,
                "clientVersion": "3.0.2"
            }

            try:
                r = requests.post(CATALOG_URL, json=d, headers=h, timeout=12)
                data = r.json()
            except:
                break

            for item in data.get("items", []):
                if selected_groups:
                    item_group = item.get("group")
                    if item_group not in selected_groups:
                        continue

                name = normalize_name(item.get("name", ""))
                add_channel_url(chans, name, item.get("url"))

            cursor = data.get("nextCursor")


def load_channels():
    global CHANNELS_CACHE
    if CHANNELS_CACHE is not None:
        return CHANNELS_CACHE

    chans = {}

    load_channels_from_index(chans)
    load_channels_from_catalog(chans)

    CHANNELS_CACHE = chans
    return chans


def resolve_link(link):
    import utils
    h = {
        "accept-encoding": "gzip",
        "user-agent": "MediaHubMX/2",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "mediahubmx-signature": utils.getAuthSignature()
    }

    d = {
        "language": "de",
        "region": "AT",
        "url": link,
        "clientVersion": "3.0.2"
    }

    try:
        r = requests.post(
            "https://vavoo.to/vto-cluster/mediahubmx-resolve.json",
            data=json.dumps(d),
            headers=h,
            timeout=10
        ).json()

        if isinstance(r, list) and r:
            return r[0].get("url", link)
        if isinstance(r, dict):
            return r.get("url", link)
        return link
    except:
        return link


def apply_playback_properties(list_item, stream_url):
    if not stream_url:
        return

    lower_url = stream_url.lower()
    if ".m3u8" in lower_url or "/vavoo-iptv/" in lower_url:
        list_item.setMimeType("application/vnd.apple.mpegurl")
        list_item.setContentLookup(False)

        if not ADDON.getSettingBool("use_inputstream"):
            return

        use_adaptive = ADDON.getSettingBool("use_inputstream_adaptive")
        use_ffmpegdirect = ADDON.getSettingBool("use_inputstream_ffmpegdirect")
        has_adaptive = xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)")
        has_ffmpegdirect = xbmc.getCondVisibility("System.HasAddon(inputstream.ffmpegdirect)")

        if use_adaptive and has_adaptive:
            list_item.setProperty("inputstream", "inputstream.adaptive")
            list_item.setProperty("inputstreamaddon", "inputstream.adaptive")
            list_item.setProperty("inputstream.adaptive.manifest_type", "hls")
            list_item.setProperty("inputstream.adaptive.stream_headers", "User-Agent=MediaHubMX/2&Accept=*/*")
        elif use_ffmpegdirect and has_ffmpegdirect:
            list_item.setProperty("inputstream", "inputstream.ffmpegdirect")
            list_item.setProperty("inputstreamaddon", "inputstream.ffmpegdirect")
        elif has_adaptive:
            list_item.setProperty("inputstream", "inputstream.adaptive")
            list_item.setProperty("inputstreamaddon", "inputstream.adaptive")
            list_item.setProperty("inputstream.adaptive.manifest_type", "hls")
            list_item.setProperty("inputstream.adaptive.stream_headers", "User-Agent=MediaHubMX/2&Accept=*/*")
        elif has_ffmpegdirect:
            list_item.setProperty("inputstream", "inputstream.ffmpegdirect")
            list_item.setProperty("inputstreamaddon", "inputstream.ffmpegdirect")


def is_sunshine_url(url):
    return "/vavoo-iptv/" in (url or "")


def url_reachable(url):
    try:
        r = requests.get(url, timeout=6, allow_redirects=True, stream=True)
        ok = r.status_code in (200, 206)
        r.close()
        return ok
    except:
        return False


def live2_variants(url):
    variants = []
    if "live2/play3/" in (url or ""):
        for n in ("1", "2", "4"):
            variants.append(url.replace("/play3/", "/play%s/" % n))
    return variants


def build_candidates(raw_url):
    candidates = []

    if is_sunshine_url(raw_url):
        candidates.append(raw_url)
        return candidates

    resolved = resolve_link(raw_url)
    if resolved:
        candidates.append(resolved)

    candidates.append(raw_url)
    candidates.extend(live2_variants(raw_url))

    unique = []
    for c in candidates:
        if c and c not in unique:
            unique.append(c)
    return unique


def choose_best_stream(streams):
    allow_sunshine = ADDON.getSettingBool("allow_sunshine")
    nonsunshine = [s for s in streams if not is_sunshine_url(s)]
    sunshine = [s for s in streams if is_sunshine_url(s)] if allow_sunshine else []
    ordered = nonsunshine + sunshine

    for raw in ordered:
        for candidate in build_candidates(raw):
            if url_reachable(candidate):
                return candidate

    if ordered:
        return build_candidates(ordered[0])[0]
    return None


def livePlay(name):
    chans = load_channels()

    if name not in chans:
        xbmcgui.Dialog().ok("Fehler", "Kein Stream gefunden.")
        return

    streams = chans[name]

    stream_select_mode = ADDON.getSetting("stream_select")
    manual_select = stream_select_mode == "0"
    auto_try_next = ADDON.getSettingBool("auto_try_next_stream")

    if len(streams) == 1:
        chosen_streams = [streams[0]]
    elif manual_select:
        labels = ["Stream %s" % (i + 1) for i in range(len(streams))]
        idx = xbmcgui.Dialog().select("Stream auswählen", labels)
        if idx < 0:
            return

        if auto_try_next:
            chosen_streams = [streams[idx]] + [s for i, s in enumerate(streams) if i != idx]
        else:
            chosen_streams = [streams[idx]]
    else:
        chosen_streams = list(streams) if auto_try_next else [streams[0]]

    ordered_streams = chosen_streams
    url = choose_best_stream(ordered_streams)

    if not url:
        xbmcgui.Dialog().ok("Fehler", "Kein funktionierender Stream gefunden.")
        return

    li = xbmcgui.ListItem(name)
    li.setPath(url)
    li.setProperty("IsPlayable", "true")
    apply_playback_properties(li, url)

    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def channels():
    chans = load_channels()

    for name in sorted(chans.keys()):
        li = xbmcgui.ListItem(name)
        li.setProperty("IsPlayable", "true")

        url = build_url({
            "mode": "welt2",
            "action": "livePlay",
            "name": name
        })

        xbmcplugin.addDirectoryItem(HANDLE, url, li, False)

    xbmcplugin.endOfDirectory(HANDLE)


def a_z_tv():
    from collections import defaultdict

    chans = load_channels()
    groups = defaultdict(list)

    for name in chans:
        first = name[0].upper() if name and name[0].isalpha() else "#"
        groups[first].append(name)

    for letter in sorted(groups.keys()):
        li = xbmcgui.ListItem(letter)

        url = build_url({
            "mode": "welt2",
            "action": "listLetter",
            "letter": letter
        })

        xbmcplugin.addDirectoryItem(HANDLE, url, li, True)

    xbmcplugin.endOfDirectory(HANDLE)


def listLetter(letter):
    chans = load_channels()

    for name in sorted(chans.keys()):
        first = name[0].upper() if name and name[0].isalpha() else "#"
        if first != letter:
            continue

        li = xbmcgui.ListItem(name)
        li.setProperty("IsPlayable", "true")

        url = build_url({
            "mode": "welt2",
            "action": "livePlay",
            "name": name
        })

        xbmcplugin.addDirectoryItem(HANDLE, url, li, False)

    xbmcplugin.endOfDirectory(HANDLE)


def live():
    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_url({"mode": "welt2", "action": "channels"}),
        xbmcgui.ListItem("Alle Sender"),
        True
    )

    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_url({"mode": "welt2", "action": "a_z_tv"}),
        xbmcgui.ListItem("A-Z"),
        True
    )

    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_url({"mode": "welt2", "action": "chooseCountries"}),
        xbmcgui.ListItem("Länderwahl"),
        False
    )

    xbmcplugin.endOfDirectory(HANDLE)


def router(params):
    a = params.get("action")

    if a in (None, "live"):
        live()
    elif a == "channels":
        channels()
    elif a == "livePlay":
        livePlay(params.get("name"))
    elif a == "a_z_tv":
        a_z_tv()
    elif a == "listLetter":
        listLetter(params.get("letter"))
    elif a == "chooseCountries":
        choose_countries_popup()
