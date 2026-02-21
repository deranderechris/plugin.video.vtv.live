# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcplugin
import urllib.parse
import utils

HANDLE = utils.handle()

XSTREAM_ID = "plugin.video.xstream"
XSHIP_ID   = "plugin.video.xship"


# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------

def run_plugin(plugin_id, action, params=None):
    if params is None:
        params = {}

    params["action"] = action
    query = urllib.parse.urlencode(params)
    url = f"plugin://{plugin_id}/?{query}"

    xbmc.executebuiltin(f'RunPlugin("{url}")')


def play_with_fallback(params):
    """
    1. Versuch: XStream
    2. Fallback: XShip
    """

    # XStream
    try:
        run_plugin(XSTREAM_ID, "playExtern", params)
        return
    except:
        pass

    # XShip
    try:
        run_plugin(XSHIP_ID, "playExtern", params)
        return
    except:
        pass

    xbmcgui.Dialog().ok("Meta‑Portal", "Keine Streams gefunden.")


# ---------------------------------------------------------
# Suche
# ---------------------------------------------------------

def search():
    query = xbmcgui.Dialog().input("Film/Serie suchen")
    if not query:
        return

    # XStream zuerst
    try:
        run_plugin(XSTREAM_ID, "moviesSearch", {"query": query})
        return
    except:
        pass

    # Fallback XShip
    run_plugin(XSHIP_ID, "moviesSearch", {"query": query})


# ---------------------------------------------------------
# Filme / Serien Listen
# ---------------------------------------------------------

def movies():
    try:
        run_plugin(XSTREAM_ID, "movies")
        return
    except:
        pass

    run_plugin(XSHIP_ID, "movies")


def series():
    try:
        run_plugin(XSTREAM_ID, "tvshows")
        return
    except:
        pass

    run_plugin(XSHIP_ID, "tvshows")


# ---------------------------------------------------------
# Router
# ---------------------------------------------------------

def router(params):
    action = params.get("action")

    if action == "portal_menu":
        portal_menu()

    elif action == "portal_search":
        search()

    elif action == "portal_movies":
        movies()

    elif action == "portal_series":
        series()

    elif action == "portal_play":
        play_with_fallback(params)


# ---------------------------------------------------------
# Menü
# ---------------------------------------------------------

def portal_menu():
    xbmcplugin.setContent(HANDLE, "addons")

    def add(name, action):
        url = utils.getPluginUrl({"action": action})
        li = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(HANDLE, url, li, True)

    add("Filme (Auto)", "portal_movies")
    add("Serien (Auto)", "portal_series")
    add("Suche (Auto)", "portal_search")

    xbmcplugin.endOfDirectory(HANDLE)
