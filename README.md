# vtv.live (Kodi Add-on)

`vtv.live` ist ein deutsch ausgerichtetes Kodi Video-Add-on mit Live-TV, Welt-TV und VAVOO-Film-/Seriennavigation.

## Status

Diese Version ist für Kodi mit Python 3 ausgelegt und wurde für stabileres Verhalten auf Fire TV angepasst.

## Funktionen

- **Live TV** (Gruppen/Kanäle)
#- **Welt TV** über `vjlive2` (Alle Sender + A-Z) ausgeblendet in default.py funktioniert nur im Emulator
- **Filme / Serien** (VAVOO-Menüs)
- **Länderauswahl** im Add-on
- **Einstellungen** in klassischem Kodi-Stil

## Wichtige Anpassungen in dieser Version

- Routing für `welt2` korrigiert, damit Untermenüs und Wiedergabe in `vjlive2.py` funktionieren
- Fire-TV-Playback verbessert (Adaptive/FFmpeg-Handling für HLS/m3u8)
- Robustere Link-Auflösung in `vjlive2.py`
- `settings.xml` vereinfacht und crash-sicherer gestaltet
- Einheitliche Playback-Settings für `vjlive2.py`, `vjackson.py` und `vmovies.py`
- Neuer **System-Check** direkt im Hauptmenü

## Einstellungen (wichtig)

Die Wiedergabe-Einstellungen gelten jetzt konsistent für **Welt TV**, **Live TV** und **Movies/Serien**:

- **Stream-Auswahl**: `Manuell` oder `Automatisch`
- **Auto nächster Stream**: probiert bei Fehlern weitere Quellen
- **InputStream nutzen**: globale Ein-/Aus-Schaltung
- **InputStream Adaptive aktivieren**: bevorzugt `inputstream.adaptive`
- **InputStream FFmpeg Direct aktivieren**: bevorzugt `inputstream.ffmpegdirect`
- **Nur funktionierende Filme/Serien anzeigen**: blendet Einträge ohne nutzbare Streams aus
- **Sunshine-Fallback erlauben**: erlaubt zusätzliche Fallback-Quellen

Hinweis: Wenn das bevorzugte InputStream-Addon auf einer Box fehlt, wird automatisch auf ein verfügbares Backend zurückgefallen.

## System-Check (neu)

Im Hauptmenü gibt es jetzt den Punkt **System-Check**. Dieser zeigt:

- ob `inputstream.adaptive` installiert ist
- ob `inputstream.ffmpegdirect` installiert ist
- welche Playback-Einstellungen aktiv sind
- HTTP-Status wichtiger Endpunkte (`live2 index`, `catalog`, `resolver`)

Damit lassen sich Probleme auf Fire TV / Android TV Boxen schneller eingrenzen.

## Installation

### ZIP-Installation (empfohlen)

1. Projekt als ZIP bereitstellen
2. In Kodi: **Einstellungen → Add-ons → Aus ZIP-Datei installieren**
3. Add-on installieren und starten

### Manuell (Entwicklung)

```bash
git clone https://github.com/deranderechris/vtv.live.git plugin.video.vtv.live
```

Dann den Ordner nach Kodi-Addon-Verzeichnis kopieren (plattformabhängig).

## Abhängigkeiten

In `addon.xml` definiert:

- `xbmc.python` (3.0.0)
- `script.module.requests`
- `inputstream.adaptive` (optional)
- `inputstream.ffmpegdirect` (optional)

## Fire TV Hinweise

- Für HLS-Streams (`.m3u8`) sollte `inputstream.adaptive` installiert/aktiv sein.
- Alternativ kann `inputstream.ffmpegdirect` genutzt werden.
- Bei Wiedergabeproblemen in Kodi einmal komplett neu starten.
- Falls ein Stream nicht startet, anderen Stream der gleichen Quelle testen.
- Bei DNS-/Provider-Problemen den **System-Check** öffnen und Status prüfen.

## Empfohlene Standardwerte (Fire TV)

Diese Kombination ist für die meisten Fire-TV-/Android-TV-Boxen stabil:

- **Stream-Auswahl**: `Automatisch`
- **Auto nächster Stream**: `AN`
- **InputStream nutzen**: `AN`
- **InputStream Adaptive aktivieren**: `AN`
- **InputStream FFmpeg Direct aktivieren**: `AUS`
- **Sunshine-Fallback erlauben**: `AN`

Wenn Streams häufig hängen oder nicht starten:

- testweise **Adaptive AUS** und **FFmpeg Direct AN**
- danach Kodi neu starten und erneut testen

## Support-Vorlage (zum Kopieren)

Bei Problemen diese Vorlage ausfüllen und mitsenden:

```text
Gerät/Box:
Kodi-Version:
Addon-Version:

Problem:
(z. B. kein Streamstart, schwarzes Bild, nur einzelne Sender betroffen)

Getesteter Bereich:
(Welt TV / Live TV / Filme / Serien)

System-Check:
inputstream.adaptive: 
inputstream.ffmpegdirect: 
live2 index (HTTP): 
catalog (HTTP): 
resolver (HTTP): 

Aktive Einstellungen:
Stream-Auswahl: 
Auto nächster Stream: 
InputStream nutzen: 
Adaptive aktivieren: 
FFmpeg Direct aktivieren: 
Sunshine-Fallback erlauben: 

Netzwerk:
(normal / anderes WLAN / Hotspot / VPN)
```

## Fehleranalyse

- Kodi-Log prüfen (bei Bedarf Debug aktivieren)
- Netzwerkzugriff auf die genutzten Endpunkte sicherstellen
- Add-on-Einstellungen öffnen und Standardwerte testen

## Rechtlicher Hinweis

Dieses Add-on ist nur eine technische Oberfläche. Für Inhalte sind ausschließlich deren jeweilige Anbieter verantwortlich.
