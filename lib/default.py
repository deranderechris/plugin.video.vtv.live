# -*- coding: utf-8 -*-
import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]


def build_url(params):
    return BASE_URL + "?" + urllib.parse.urlencode(params)


GROUP_NAMES = {
    "DE": "Deutschland",
    "AT": "Österreich",
    "CH": "Schweiz",
    "FR": "Frankreich",
    "BG": "Bulgarien",
    "TR": "Türkei",
    "IT": "Italien",
    "ES": "Spanien",
    "BALKAN": "Balkan",
    "ARABIC": "Arabisch",
    "INTERNATIONAL": "International",
    "SPORT": "Sport",
    "KIDS": "Kinder",
    "MOVIES": "Filme",
    "SERIES": "Serien"
}


def load_vavoo_groups():
    try:
        url = "https://www2.vavoo.to/live2/index?output=json"
        data = requests.get(url, timeout=5).json()
        groups = []
        for item in data:
            g = item.get("group")
            if g and g not in groups:
                groups.append(g)
        return groups
    except:
        return []


def choose_countries():
    groups = load_vavoo_groups()
    if not groups:
        xbmcgui.Dialog().notification("Fehler", "Keine Gruppen gefunden", xbmcgui.NOTIFICATION_ERROR)
        return

    display = [GROUP_NAMES.get(g, g) for g in groups]

    try:
        old = json.loads(ADDON.getSetting("country_groups"))
    except:
        old = []

    preselect = [groups.index(g) for g in old if g in groups]

    selected = xbmcgui.Dialog().multiselect("Länder wählen", display, preselect=preselect)
    if selected is None:
        return

    chosen = [groups[i] for i in selected]
    ADDON.setSetting("country_groups", json.dumps(chosen))
    xbmcgui.Dialog().notification("Gespeichert", "Länderauswahl aktualisiert", xbmcgui.NOTIFICATION_INFO)


def _status(ok):
    return "OK" if ok else "FEHLER"


def run_system_check():
    lines = []

    has_adaptive = xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)")
    has_ffmpeg = xbmc.getCondVisibility("System.HasAddon(inputstream.ffmpegdirect)")

    lines.append("=== Addon / Player ===")
    lines.append("inputstream.adaptive: %s" % _status(has_adaptive))
    lines.append("inputstream.ffmpegdirect: %s" % _status(has_ffmpeg))
    lines.append("")

    lines.append("=== Aktive Einstellungen ===")
    stream_mode = "Manuell" if ADDON.getSetting("stream_select") == "0" else "Automatisch"
    lines.append("Stream-Auswahl: %s" % stream_mode)
    lines.append("Auto nächster Stream: %s" % ("AN" if ADDON.getSettingBool("auto_try_next_stream") else "AUS"))
    lines.append("InputStream nutzen: %s" % ("AN" if ADDON.getSettingBool("use_inputstream") else "AUS"))
    lines.append("Adaptive bevorzugt: %s" % ("AN" if ADDON.getSettingBool("use_inputstream_adaptive") else "AUS"))
    lines.append("FFmpeg Direct bevorzugt: %s" % ("AN" if ADDON.getSettingBool("use_inputstream_ffmpegdirect") else "AUS"))
    lines.append("Sunshine-Fallback: %s" % ("AN" if ADDON.getSettingBool("allow_sunshine") else "AUS"))
    lines.append("")

    lines.append("=== Netzwerk / Endpunkte ===")
    checks = [
        ("live2 index", "GET", "https://www2.vavoo.to/live2/index?output=json"),
        ("catalog", "POST", "https://vavoo.to/mediahubmx-catalog.json"),
        ("resolver", "POST", "https://vavoo.to/vto-cluster/mediahubmx-resolve.json"),
    ]

    for label, method, url in checks:
        try:
            if method == "GET":
                r = requests.get(url, timeout=6)
            else:
                r = requests.post(url, timeout=6)
            lines.append("%s: HTTP %s" % (label, r.status_code))
        except Exception as e:
            lines.append("%s: FEHLER (%s)" % (label, type(e).__name__))

    lines.append("")
    lines.append("Hinweis: 4xx/5xx kann serverseitig oder DNS/Provider-bedingt sein.")

    xbmcgui.Dialog().textviewer("vtv.live System-Check", "\n".join(lines))


def main_menu():
    items = [
        ("V-Live DE", {"mode": "livetv"}),
        #("V-Welt TV", {"mode": "welt2"}),
        #("V-System-Check", {"mode": "system_check"}),
        #("Länder wählen", {"mode": "choose_countries"}),
        ("V-Filme", {"mode": "movies"}),
        ("V-Serien", {"mode": "series"}),
        ("xS-Portale", {"mode": "open_xstream"}),
        ("xS-Filme&Serien", {"mode": "open_xship"}),
        ("Einstellungen", {"mode": "settings"}),
    ]

    for label, params in items:
        li = xbmcgui.ListItem(label=label)
        url = build_url(params)
        is_folder = not params["mode"].startswith(("open_",))
        xbmcplugin.addDirectoryItem(HANDLE, url, li, is_folder)

    xbmcplugin.endOfDirectory(HANDLE)


def route(params):
    mode = params.get("mode") or params.get("action")

    if mode == "choose_countries":
        choose_countries()
        return

    if mode == "system_check":
        run_system_check()
        return

    if mode == "welt2":
        import vjlive2
        vjlive2.router(params)
        return

    if mode == "welt_menu":
        import vjackson
        vjackson.router({"mode": "countries"})
        return

    if mode == "open_xstream":
        xbmc.executebuiltin('RunAddon("plugin.video.xstream")')
        return

    if mode == "open_xship":
        xbmc.executebuiltin('RunAddon("plugin.video.xship")')
        return

    if mode == "livetv":
        import vjackson
        vjackson.router({"mode": "livetv"})
        return

    if mode == "channels":
        import vjackson
        vjackson.router({"mode": "channels", "group": params.get("group")})
        return

    if mode == "play":
        import vjackson
        vjackson.router({"mode": "play", "url": params.get("url"), "name": params.get("name")})
        return

    if mode == "movies":
        import vmovies
        vmovies.router({"action": "movies_menu"})
        return

    if mode == "series":
        import vmovies
        vmovies.router({"action": "series_menu"})
        return

    if mode in ["list", "seasons", "episodes", "get", "movies_menu", "series_menu"]:
        import vmovies
        vmovies.router(params)
        return

    if mode == "settings":
        ADDON.openSettings()
        return

    main_menu()


if __name__ == "__main__":
    args = sys.argv[2][1:]
    params = dict(urllib.parse.parse_qsl(args))
    route(params)


