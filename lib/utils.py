# -*- coding: utf-8 -*-
#
# utils.py – zentrale Tools für dein VTV LiveTV + Movies/Series Addon
#

from __future__ import unicode_literals
import json
import urllib.parse
from urllib.parse import urlparse as _urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import requests
import sys
import time

addon = xbmcaddon.Addon()
_cache = {}

# ---------------------------------------------------------
# CACHE
# ---------------------------------------------------------

def get_cache(key):
    value = _cache.get(key)
    if value is None:
        return None

    if isinstance(value, dict) and "value" in value and "expires_at" in value:
        expires_at = value.get("expires_at")
        if expires_at is not None and time.time() > expires_at:
            _cache.pop(key, None)
            return None
        return value.get("value")

    return value

def set_cache(key, value, timeout=None):
    if timeout is None:
        _cache[key] = value
    else:
        _cache[key] = {
            "value": value,
            "expires_at": time.time() + max(0, timeout)
        }


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

def log(msg, level=None):
    if level is None:
        level = xbmc.LOGINFO
    xbmc.log(f"[plugin.video.vtv.live] {msg}", level)


# ---------------------------------------------------------
# HANDLE + URL BUILDER
# ---------------------------------------------------------

def handle():
    try:
        return int(sys.argv[1])
    except:
        return -1


def getPluginUrl(params):
    base = sys.argv[0]
    return base + "?" + urllib.parse.urlencode(params)


# ---------------------------------------------------------
# URL PARSER (für vmovies Stream-Resolver)
# ---------------------------------------------------------

def urlparse(url):
    try:
        return _urlparse(url)
    except:
        return _urlparse("")


# ---------------------------------------------------------
# HEADERS
# ---------------------------------------------------------

def build_headers():
    return {
        "User-Agent": "VAVOO/2.6",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def build_sunshine_headers():
    return {
        "User-Agent": "MediaHubMX/2",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
        "mediahubmx-signature": getAuthSignature(),
    }


# ---------------------------------------------------------
# HTTP GET / POST
# ---------------------------------------------------------

def http_get(url, params=None, timeout=5):
    try:
        r = requests.get(url, params=params, headers=build_headers(), timeout=timeout)
        log(f"GET {url} → Status {r.status_code}")

        if not r.ok:
            log(f"GET fehlgeschlagen: {r.text}", xbmc.LOGERROR)
            return {}

        try:
            return r.json()
        except:
            log("GET: Antwort ist kein JSON", xbmc.LOGERROR)
            return {}
    except Exception as e:
        log(f"HTTP GET Fehler: {e}", xbmc.LOGERROR)
        return {}


def http_post(url, payload=None, timeout=5, sunshine=False):
    try:
        headers = build_sunshine_headers() if sunshine else build_headers()
        data = json.dumps(payload) if payload else None

        r = requests.post(url, headers=headers, data=data, timeout=timeout)
        log(f"POST {url} → Status {r.status_code}")

        if not r.ok:
            log(f"POST fehlgeschlagen: {r.text}", xbmc.LOGERROR)
            return {}

        try:
            return r.json()
        except:
            log("POST: Antwort ist kein JSON", xbmc.LOGERROR)
            return {}
    except Exception as e:
        log(f"HTTP POST Fehler: {e}", xbmc.LOGERROR)
        return {}


# ---------------------------------------------------------
# DIALOGE
# ---------------------------------------------------------

def ok(title, msg):
    xbmcgui.Dialog().ok(title, msg)


# ---------------------------------------------------------
# SIGNATURE (PING2)
# ---------------------------------------------------------

def getAuthSignature(force_refresh=False):
    signfile = None if force_refresh else get_cache('signfile')
    sig_valid_until = None if force_refresh else get_cache('signfile_valid_until')

    if signfile and sig_valid_until:
        try:
            now_ms = int(time.time() * 1000)
            valid_until_ms = int(sig_valid_until)
            if now_ms < (valid_until_ms - 60000):
                return signfile
        except:
            pass
    elif signfile:
        return signfile

    vec = {
        "vec": "9frjpxPjxSNilxJPCJ0XGYs6scej3dW/h/VWlnKUiLSG8IP7mfyDU7NirOlld+VtCKGj03XjetfliDMhIev7wcARo+YTU8KPFuVQP9E2DVXzY2BFo1NhE6qEmPfNDnm74eyl/7iFJ0EETm6XbYyz8IKBkAqPN/Spp3PZ2ulKg3QBSDxcVN4R5zRn7OsgLJ2CNTuWkd/h451lDCp+TtTuvnAEhcQckdsydFhTZCK5IiWrrTIC/d4qDXEd+GtOP4hPdoIuCaNzYfX3lLCwFENC6RZoTBYLrcKVVgbqyQZ7DnLqfLqvf3z0FVUWx9H21liGFpByzdnoxyFkue3NzrFtkRL37xkx9ITucepSYKzUVEfyBh+/3mtzKY26VIRkJFkpf8KVcCRNrTRQn47Wuq4gC7sSwT7eHCAydKSACcUMMdpPSvbvfOmIqeBNA83osX8FPFYUMZsjvYNEE3arbFiGsQlggBKgg1V3oN+5ni3Vjc5InHg/xv476LHDFnNdAJx448ph3DoAiJjr2g4ZTNynfSxdzA68qSuJY8UjyzgDjG0RIMv2h7DlQNjkAXv4k1BrPpfOiOqH67yIarNmkPIwrIV+W9TTV/yRyE1LEgOr4DK8uW2AUtHOPA2gn6P5sgFyi68w55MZBPepddfYTQ+E1N6R/hWnMYPt/i0xSUeMPekX47iucfpFBEv9Uh9zdGiEB+0P3LVMP+q+pbBU4o1NkKyY1V8wH1Wilr0a+q87kEnQ1LWYMMBhaP9yFseGSbYwdeLsX9uR1uPaN+u4woO2g8sw9Y5ze5XMgOVpFCZaut02I5k0U4WPyN5adQjG8sAzxsI3KsV04DEVymj224iqg2Lzz53Xz9yEy+7/85ILQpJ6llCyqpHLFyHq/kJxYPhDUF755WaHJEaFRPxUqbparNX+mCE9Xzy7Q/KTgAPiRS41FHXXv+7XSPp4cy9jli0BVnYf13Xsp28OGs/D8Nl3NgEn3/eUcMN80JRdsOrV62fnBVMBNf36+LbISdvsFAFr0xyuPGmlIETcFyxJkrGZnhHAxwzsvZ+Uwf8lffBfZFPRrNv+tgeeLpatVcHLHZGeTgWWml6tIHwWUqv2TVJeMkAEL5PPS4Gtbscau5HM+FEjtGS+KClfX1CNKvgYJl7mLDEf5ZYQv5kHaoQ6RcPaR6vUNn02zpq5/X3EPIgUKF0r/0ctmoT84B2J1BKfCbctdFY9br7JSJ6DvUxyde68jB+Il6qNcQwTFj4cNErk4x719Y42NoAnnQYC2/qfL/gAhJl8TKMvBt3Bno+va8ve8E0z8yEuMLUqe8OXLce6nCa+L5LYK1aBdb60BYbMeWk1qmG6Nk9OnYLhzDyrd9iHDd7X95OM6X5wiMVZRn5ebw4askTTc50xmrg4eic2U1w1JpSEjdH/u/hXrWKSMWAxaj34uQnMuWxPZEXoVxzGyuUbroXRfkhzpqmqqqOcypjsWPdq5BOUGL/Riwjm6yMI0x9kbO8+VoQ6RYfjAbxNriZ1cQ+AW1fqEgnRWXmjt4Z1M0ygUBi8w71bDML1YG6UHeC2cJ2CCCxSrfycKQhpSdI1QIuwd2eyIpd4LgwrMiY3xNWreAF+qobNxvE7ypKTISNrz0iYIhU0aKNlcGwYd0FXIRfKVBzSBe4MRK2pGLDNO6ytoHxvJweZ8h1XG8RWc4aB5gTnB7Tjiqym4b64lRdj1DPHJnzD4aqRixpXhzYzWVDN2kONCR5i2quYbnVFN4sSfLiKeOwKX4JdmzpYixNZXjLkG14seS6KR0Wl8Itp5IMIWFpnNokjRH76RYRZAcx0jP0V5/GfNNTi5QsEU98en0SiXHQGXnROiHpRUDXTl8FmJORjwXc0AjrEMuQ2FDJDmAIlKUSLhjbIiKw3iaqp5TVyXuz0ZMYBhnqhcwqULqtFSuIKpaW8FgF8QJfP2frADf4kKZG1bQ99MrRrb2A="
    }

    url = 'https://www.vavoo.tv/api/box/ping2'

    try:
        req = requests.post(url, data=vec, timeout=15).json()
    except Exception as e:
        log(f"PING2 Fehler: {e}", xbmc.LOGERROR)
        fallback = get_cache('signfile')
        return fallback

    if not req or "response" not in req:
        log("PING2 liefert keine gültige Antwort", xbmc.LOGERROR)
        fallback = get_cache('signfile')
        return fallback

    response = req.get('response', {})
    signed = response.get('signed')
    valid_until = response.get('sigValidUntil')

    if not signed:
        log("PING2 enthält keine Signatur", xbmc.LOGERROR)
        fallback = get_cache('signfile')
        return fallback

    set_cache('signfile', signed)
    if valid_until:
        try:
            set_cache('signfile_valid_until', int(valid_until))
        except:
            pass

    return signed
