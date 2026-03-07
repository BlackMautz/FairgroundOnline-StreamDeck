# Fairground Online — Stream Deck Plugin

![Fairground Online Stream Deck Plugin](Githubreadmybild.png)

Ein natives Stream Deck Plugin für [Fairground Online](https://store.steampowered.com/app/3310530/Fairground_Online/), das alle Fahrgeschäfte, Licht, Sound und Effekte direkt über den Stream Deck steuert. Funktioniert mit **allen Stream Deck Modellen** (MK.2, XL, Mini, Plus, etc.).

**Inoffiziell erstellt von BlackMautz** — dieses Plugin ist kein offizielles Produkt des Spielentwicklers.

![Stream Deck](https://img.shields.io/badge/Stream%20Deck-Alle%20Modelle-blue)
![Windows](https://img.shields.io/badge/Platform-Windows-lightgrey)
![.NET 4.0](https://img.shields.io/badge/.NET-4.0-purple)
![Auto-Update](https://img.shields.io/badge/Auto--Update-✓-green)

## Features

- **6 Fahrgeschäfte** komplett steuerbar: BreakDance, StarLight, XPlosion, FunHouse, Rotator, Turaka
- **Lichtsteuerung**: 9 Presets, 9 Einzellichter, Strobo, LED Strobe, Nebel, Flamme, Seifenblasen, Hupe
- **Spotlight**: AN/AUS, Farbstroboskop, Farbwechsel
- **Moving Heads**: AN/AUS, Licht, LightSync, Color Strobe, Farbe, Programm, Gobos
- **Sound & Mikrofon**: Play/Pause, Track-Wechsel, Mikrofon, Mikrofon-Echo
- **12 Jingles + 12 Decks**
- **Timer**: Konfigurierbarer Countdown-Timer mit Property Inspector (Minuten/Sekunden einstellbar), kurz drücken = Start/Pause, lang gedrückt halten = Reset, blinkt 5x am Ende
- **Standard-Steuerung**: Ein-/Aussteigen, Kamerawechsel, Chat, Push to Talk, Sitzplatzwechsel
- **Settings**: Menü, Speed-Steuerung, Repeat Speed (3 Stufen), Schrift AN/AUS
- **159 Aktionen** in 13 Kategorien mit eigenen Kategorie-Icons
- **310+ individuelle Button-Icons** für jede Aktion
- **Toggle-Buttons** mit [AN]/[AUS] Statusanzeige
- **HoldToggle-Modus** (z.B. Mikrofon Echo: 1x drücken = an, nochmal drücken = aus)
- **Repeat-Modus** für alle Speed +/- Buttons mit 3 einstellbaren Geschwindigkeiten
- **Modifier-Unterstützung**: Shift und Ctrl Kombinationen wo vom Spiel gefordert
- **Schrift AN/AUS**: Alle Button-Titel global ein-/ausblenden
- **Auto-Updater**: Prüft beim Start auf neue Versionen auf GitHub

![Plugin Übersicht](readme1.png)

## Funktionsweise

Das Plugin wird komplett durch ein Python-Skript (`create_fairground_plugin.py`) generiert:

1. Generiert C# Quellcode für das native Stream Deck Plugin
2. Kompiliert mit dem .NET Framework 4.0 C# Compiler
3. Erstellt alle Icons, Kategorie-Bilder und Overlay-Bilder
4. Baut die manifest.json mit allen 159 Aktionen in 13 Kategorien
5. Verpackt alles als `.streamDeckPlugin` Installationspaket
6. Kopiert direkt in den installierten Plugin-Ordner und startet Stream Deck neu

Die Tasteneingaben werden über `keybd_event` mit Scan-Codes gesendet — das funktioniert unabhängig vom Tastaturlayout.

## Voraussetzungen

- Windows 10 oder höher
- [Elgato Stream Deck Software](https://www.elgato.com/downloads) (Version 5.0+)
- Elgato Stream Deck (alle Modelle)
- Python 3.x (nur zum Bauen des Plugins)
- .NET Framework 4.0 (in Windows enthalten)

## Installation

```bash
# Plugin bauen und installieren
python create_fairground_plugin.py
```

Das Skript erstellt `Fairground_Online.streamDeckPlugin`. Falls das Plugin bereits installiert ist, wird es direkt aktualisiert und Stream Deck neugestartet. Andernfalls: Doppelklick auf die `.streamDeckPlugin` Datei.

## Kategorien

| Kategorie | Aktionen |
|-----------|----------|
| BreakDance | NOT-AUS, EIN/AUS, Kompressor, Platte (Speed/AN/Tip), Kreuz (Speed/AN/Tip), Gondelbremse |
| StarLight | NOT-AUS, EIN/AUS, Reset, Parking, Gondel/Arm Pumpe, Gondola/Arm Speed+Bremse, Platform |
| XPlosion | NOT-AUS, EIN/AUS, Reset, Freigabe, Hoch/Runter, Null |
| FunHouse | NOT-AUS, EIN/AUS, 3 Drehscheiben, 2 Laufbänder, Vibrierplatte, Drehtunnel |
| Rotator | NOT-AUS, EIN/AUS, Reset, Park, Pumpe, Kompressor, Platte/Kreuz/Inverter, Bügel, Hub |
| Turaka | NOT-AUS, EIN/AUS, Reset, Speed, Richtung, Start/Stop, Platform, Park Wagen |
| Standard | Ein-/Aussteigen, Push to Talk, Sitzplatzwechsel, Kamerawechsel, Chat |
| LightEffect | 9 Presets, 9 Lights, Strobo, LED Strobe, Spot, Nebel, Flamme, Seifenblasen, Hupe |
| MovingHeads | AN/AUS, Licht, LightSync, Color Strobe, Farbe, Programm, Gobos |
| Sound | Play/Pause, Track-Wechsel, Mikrofon, Mikrofon Echo |
| Timer | Konfigurierbarer Countdown-Timer |
| Jingles | 12 Jingles + 12 Decks |
| Settings | Menü, Speed Hoch/Runter, Repeat Speed, Schrift AN/AUS |

## Timer

Der Timer ist ein konfigurierbarer Countdown-Timer mit Property Inspector:

- **Einstellbar**: Minuten und Sekunden über den Property Inspector im Stream Deck
- **Kurz drücken**: Start/Pause
- **Lang gedrückt halten** (>800ms): Reset auf Startzeit
- **Blinkt 5x** wenn der Timer abgelaufen ist
- **Anzeige**: Zeigt verbleibende Zeit und Status (>>>, PAUSE, STOP)

## Button-Modi

| Modus | Beschreibung |
|-------|-------------|
| Normal | Taste wird bei Druck kurz gesendet |
| Hold | Taste wird gehalten solange der Button gedrückt ist |
| Toggle | Erster Druck sendet AN-Taste, zweiter Druck sendet AUS-Taste |
| HoldToggle | Erster Druck hält Taste dauerhaft, zweiter Druck lässt los |
| Repeat | Taste wird wiederholt gedrückt solange der Button gehalten wird (einstellbare Geschwindigkeit) |
| Mod | Modifier (Shift/Ctrl) + Taste wird kurz gesendet |
| ModHold | Modifier + Taste wird gehalten |
| ModRepeat | Modifier + Taste wird wiederholt gedrückt |

## Repeat-Geschwindigkeiten

Über den "Repeat Speed" Button auf jeder Seite einstellbar:

| Stufe | Intervall | Tasten/Sek |
|-------|-----------|-----------|
| Langsam | 400ms | ~2 |
| Mittel | 200ms | ~4 |
| Schnell | 80ms | ~9 |

## Tasten-Referenz

Die Datei `fairground_input_actions.json` enthält die vollständige Tastenbelegung aus dem Spiel (extrahiert aus der Game-DLL).

## Lizenz

MIT License

## Auto-Updater

Das Plugin prüft beim Start automatisch auf neue Versionen auf GitHub. Wenn ein Update verfügbar ist, wird es heruntergeladen und installiert — kein manuelles Update nötig.

## Changelog

### v1.1.0
- **Timer hinzugefügt**: Konfigurierbarer Countdown-Timer mit Property Inspector (Minuten/Sekunden), kurz drücken = Start/Pause, lang halten = Reset, 5x Blinken am Ende
- **Platte Tip & Kreuz Tip gefixt**: Jetzt Hold-Modus (Taste wird gehalten solange Button gedrückt) statt nur kurzes Tippen
- **Umlaute gefixt**: Alle Button-Beschriftungen mit korrekten deutschen Umlauten (ä, ö, ü)
- 159 Aktionen in 13 Kategorien

### v1.0.5
- Universelle Stream Deck Unterstützung (alle Modelle)
- Profile entfernt

### v1.0.4
- Repeat-Beschleunigung (500-100ms)
- Game-Crash-Fix
- Vereinfachter Build

## Autor

Erstellt von **BlackMautz**