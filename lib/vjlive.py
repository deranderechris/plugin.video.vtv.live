# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import requests

try:
    import xbmc
    import xbmcgui
    import xbmcplugin
except ImportError:
    xbmc = None
    xbmcgui = None
    xbmcplugin = None

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1


def log(msg, level=None):
    if xbmc:
        if level is None:
            level = xbmc.LOGINFO
        xbmc.log(f"[vjlive] {msg}", level)
    else:
        print(f"[vjlive] {msg}")


def fallback_live2(url):
    """
    Wenn live2/play3 404 liefert → automatisch play1, play2, play4 testen.
    """
    if "live2/play3" not in url:
        return url

    base = url.replace("play3", "play{}")
    for i in ["1", "2", "4"]:
        test_url = base.format(i)
        try:
            r = requests.get(test_url, timeout=5, stream=True)
            if r.status_code == 200:
                log(f"Fallback erfolgreich: {test_url}")
                return test_url
        except Exception as e:
            log(f"Fallback-Fehler bei {test_url}: {e}")
            continue

    log("Kein Fallback erfolgreich, nutze Original-URL")
    return url


def resolve_url(url):
    # hier können später Sunshine/ccapi etc. rein
    url = fallback_live2(url)
    return url


def play(url, name=""):
    if not url:
        if xbmcgui:
            xbmcgui.Dialog().ok("Fehler", "Keine URL zum Abspielen.")
        return

    url = resolve_url(url)
    log(f"Spiele: {name} - {url}")

    if xbmcplugin and HANDLE >= 0:
        li = xbmcgui.ListItem(label=name, path=url)
        li.setProperty("IsPlayable", "true")
        li.setInfo("video", {"title": name})
        if ".m3u8" in url:
            li.setMimeType("application/vnd.apple.mpegurl")
            li.setProperty("inputstream", "inputstream.adaptive")
            li.setProperty("inputstream.adaptive.manifest_type", "hls")
        xbmcplugin.setResolvedUrl(HANDLE, True, li)


def router(params):
    mode = params.get("mode")
    if mode == "play":
        play(params.get("url"), params.get("name"))


if __name__ == "__main__":
    log("vjlive Testmodus")
