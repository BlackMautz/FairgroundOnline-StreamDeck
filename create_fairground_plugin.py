#!/usr/bin/env python3
"""
Erstellt ein Stream Deck Plugin (.streamDeckPlugin) fuer Fairground Online.
Das Plugin sendet Tastenkuerzel (Scan-Codes) an das Spiel.

Ausgabe: Fairground_Online.streamDeckPlugin (Doppelklick zum Installieren)
"""
import os
import json
import struct
import zlib
import zipfile
import subprocess
import shutil
import uuid as uuid_mod
import random
import string

# â”€â”€â”€ Konfiguration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PLUGIN_ID = "com.blackmautz.fairground"
PLUGIN_NAME = "Fairground Online"
PLUGIN_AUTHOR = "BlackMautz"
PLUGIN_DESC = "Steuerung fuer Fairground Online Fahrgeschaefte"
PLUGIN_VERSION = "1.0.4"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SDPLUGIN_DIR = os.path.join(BASE_DIR, f"{PLUGIN_ID}.sdPlugin")
OUTPUT_FILE = os.path.join(BASE_DIR, "Fairground_Online.streamDeckPlugin")

CSC_PATH = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

DEVICE_MODEL = "20GAT9901"   # Stream Deck XL
DEVICE_UUID = "@(1)[4057/108/CL33L2A04413]"

# â”€â”€â”€ Scan Codes (AT-Tastatur, positionsbasiert) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Diese Codes sind physisch, d.h. layout-unabhaengig.
# Unity Input System: <Keyboard>/y = physische Y-Position (US-Layout)
SCAN = {
    "backspace": 0x0E, "tab": 0x0F, "enter": 0x1C,
    "escape": 0x01, "space": 0x39,
    "shift": 0x2A, "rightShift": 0x36, "alt": 0x38, "leftCtrl": 0x1D,
    "leftArrow": 0x4B, "rightArrow": 0x4D,
    "a": 0x1E, "b": 0x30, "c": 0x2E, "d": 0x20,
    "e": 0x12, "f": 0x21, "g": 0x22, "h": 0x23,
    "i": 0x17, "j": 0x24, "k": 0x25, "l": 0x26,
    "m": 0x32, "n": 0x31, "o": 0x18, "p": 0x19,
    "q": 0x10, "r": 0x13, "s": 0x1F, "t": 0x14,
    "u": 0x16, "v": 0x2F, "w": 0x11, "x": 0x2D,
    "y": 0x15, "z": 0x2C,
    "0": 0x0B, "1": 0x02, "2": 0x03, "3": 0x04,
    "4": 0x05, "5": 0x06, "6": 0x07, "7": 0x08,
    "8": 0x09, "9": 0x0A,
    "numpad1": 0x4F, "numpad2": 0x50, "numpad3": 0x51,
    "numpad4": 0x4B, "numpad5": 0x4C, "numpad6": 0x4D,
    "numpad7": 0x47, "numpad8": 0x48, "numpad9": 0x49,
    "f1": 0x3B, "f2": 0x3C, "f3": 0x3D, "f4": 0x3E,
    "f5": 0x3F, "f6": 0x40, "f7": 0x41, "f8": 0x42,
    "f9": 0x43, "f10": 0x44, "f11": 0x57, "f12": 0x58,
    "minus": 0x0C, "slash": 0x35,
    "leftBracket": 0x1A, "rightBracket": 0x1B,
    "quote": 0x28, "semicolon": 0x27,
}

# Extended Keys brauchen KEYEVENTF_EXTENDEDKEY Flag
EXTENDED_KEYS = {"leftArrow", "rightArrow"}

# â”€â”€â”€ Fahrgeschaeft-Definitionen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Format: (ride_id, ride_name, (R,G,B), [
#   (action_id, button_label, unity_key, is_hold), ...
#   Toggle: (action_id, label, (key_on, key_off), "toggle")
# ])
RIDES = [
    ("breakdance", "BreakDance", (200, 50, 50), [
        ("emergencystop", "NOT-AUS", "backspace", True),
        ("onoff", "EIN/AUS", "enter", False),
        ("kompressor", "Kompressor", (("leftCtrl", "q"), ("leftCtrl", "w")), "toggle"),
        ("plattespeeddown", "Platte -", "f", "repeat"),
        ("plattespeedup", "Platte +", "r", "repeat"),
        ("platte", "Platte", ("y", "u"), "toggle"),
        ("plattetippen", "Platte Tip", "v", False),
        ("kreuzspeeddown", "Kreuz -", "g", "repeat"),
        ("kreuzspeedup", "Kreuz +", "t", "repeat"),
        ("kreuz", "Kreuz", ("h", "j"), "toggle"),
        ("kreuztippen", "Kreuz Tip", "b", False),
        ("gondelbremse", "Gondelbremse", "n", True),
    ]),
    ("starlight", "StarLight", (50, 100, 200), [
        ("emergencystop", "NOT-AUS", "backspace", True),
        ("onoff", "EIN/AUS", "enter", False),
        ("reset", "Reset", "rightShift", False),
        ("parking", "Parking", "p", False),
        ("gondelpumpe", "Gondel Pumpe", ("q", "w"), "toggle"),
        ("armpumpe", "Arm Pumpe", ("a", "s"), "toggle"),
        ("gondolaspeeddown", "Gondola -", "r", "repeat"),
        ("gondolaspeedup", "Gondola +", "v", "repeat"),
        ("gondolabremse", "Gondola Bremse", "u", True),
        ("gondel0", "Gondel 0", "f", False),
        ("armspeeddown", "Arm -", "t", "repeat"),
        ("armspeedup", "Arm +", "b", "repeat"),
        ("armbremse", "Arm Bremse", "j", False),
        ("arm0", "Arm 0", "g", False),
        ("platformup", "Platform Hoch", "y", True),
        ("platformdown", "Platform Runter", "h", True),
    ]),
    ("xplosion", "XPlosion", (200, 130, 0), [
        ("emergencystop", "NOT-AUS", "backspace", True),
        ("onoff", "EIN/AUS", "enter", False),
        ("reset", "Reset", "rightShift", False),
        ("freigabe", "Freigabe", "t", False),
        ("up", "Hoch", "r", True),
        ("down", "Runter", "f", True),
        ("zero", "Null", "v", False),
    ]),
    ("funhouse", "FunHouse", (150, 50, 200), [
        ("emergencystop", "NOT-AUS", "backspace", True),
        ("onoff", "EIN/AUS", "enter", False),
        ("turntable1", "Drehsch. 1.OG", "r", False),
        ("turntable2", "Drehsch. 2.OG", "f", False),
        ("turntable3", "Drehsch. Dach", "v", False),
        ("conveyor1", "Laufband 1.OG", "t", False),
        ("conveyor2", "Laufband 2.OG", "g", False),
        ("vibrate1", "Vibrierplatte", "y", False),
        ("tunnel1", "Drehtunnel", "u", False),
    ]),
    ("rotator", "Rotator", (0, 150, 150), [
        ("emergencystop", "NOT-AUS", "backspace", True),
        ("onoff", "EIN/AUS", "enter", False),
        ("reset", "Reset", "rightShift", False),
        ("park", "Park", "p", False),
        ("pumpe", "Pumpe", ("q", "w"), "toggle"),
        ("kompressor", "Kompressor", ("a", "s"), "toggle"),
        ("plattespeeddown", "Platte -", "r", "repeat"),
        ("plattespeedup", "Platte +", "v", "repeat"),
        ("platte0", "Platte 0", "f", False),
        ("platte", "Platte", ("o", "l"), "toggle"),
        ("kreuzspeeddown", "Kreuz -", "y", "repeat"),
        ("kreuzspeedup", "Kreuz +", "n", "repeat"),
        ("kreuz0", "Kreuz 0", "h", False),
        ("kreuz", "Kreuz", ("leftBracket", "quote"), "toggle"),
        ("inverterspeeddown", "Inverter -", "t", "repeat"),
        ("inverterspeedup", "Inverter +", "b", "repeat"),
        ("inverter0", "Inverter 0", "g", False),
        ("inverter", "Inverter", ("p", "semicolon"), "toggle"),
        ("buegel", "Buegel", ("i", "k"), "toggle"),
        ("hubup", "Hub Hoch", "u", True),
        ("hubstop", "Hub Stop", "j", False),
        ("hubdown", "Hub Runter", "m", True),
    ]),
    ("turaka", "Turaka", (50, 150, 50), [
        ("emergencystop", "NOT-AUS", "backspace", True),
        ("onoff", "EIN/AUS", "enter", False),
        ("reset", "Reset", "rightShift", False),
        ("speeddown", "Speed -", "f", "repeat"),
        ("speedup", "Speed +", "r", "repeat"),
        ("direction", "Richtung", "t", False),
        ("start", "Start", "h", False),
        ("stop", "Stop", "n", False),
        ("platform", "Platform", "y", False),
        ("parkcar1", "Park Wagen 1", "g", False),
        ("parkcar2", "Park Wagen 2", "b", False),
    ]),
    ("standard", "Standard", (100, 100, 100), [
        ("enterleave", "Ein-/Aussteigen", "e", False),
        ("pushtotalk", "Push to Talk", "alt", True),
        ("ingamevoice", "Ingame Voice", "alt", True),
        ("nextseat", "Naechster Platz", ("leftCtrl", "z"), "mod"),
        ("lastseat", "Letzter Platz", ("leftCtrl", "x"), "mod"),
        ("camera", "Kamerawechsel", "tab", False),
        ("chat", "Chat", "slash", False),
    ]),
   
    ("lighteffect", "LightEffect", (200, 150, 0), [
        ("preset1", "Preset 1", "numpad1", False),
        ("preset2", "Preset 2", "numpad2", False),
        ("preset3", "Preset 3", "numpad3", False),
        ("preset4", "Preset 4", "numpad4", False),
        ("preset5", "Preset 5", "numpad5", False),
        ("preset6", "Preset 6", "numpad6", False),
        ("preset7", "Preset 7", "numpad7", False),
        ("preset8", "Preset 8", "numpad8", False),
        ("preset9", "Preset 9", "numpad9", False),
        ("light1", "Light 1", "1", False),
        ("light2", "Light 2", "2", False),
        ("light3", "Light 3", "3", False),
        ("light4", "Light 4", "4", False),
        ("light5", "Light 5", "5", False),
        ("light6", "Light 6", "6", False),
        ("light7", "Light 7", "7", False),
        ("light8", "Light 8", "8", False),
        ("light9", "Light 9", "9", False),
        ("alloff", "Alle AUS", "0", False),
        ("strobo", "Strobo", "space", True),
        ("ledstrobe", "LED Strobe", "minus", True),
        ("colorstrobe", "Farbstroboskop", ("shift", "a"), "mod"),
        ("spotonoff", "Spot AN/AUS", ("shift", "q"), "mod"),
        ("spotcolorup", "SpotColor +", ("shift", "w"), "modrepeat"),
        ("spotcolordown", "SpotColor -", ("shift", "s"), "modrepeat"),
        ("fog", "Nebel", "d", True),
        ("flame", "Flamme", "c", True),
        ("bubbles", "Seifenblasen", ("leftCtrl", "c"), "modhold"),
        ("horn", "Hupe", "z", True),
    ]),
    ("movingheads", "MovingHeads", (200, 50, 150), [
        ("onoff", "Moving Head AN", ("shift", "z"), "mod"),
        ("light", "MH Licht", ("shift", "x"), "mod"),
        ("lightsync", "MH Light Sync", ("shift", "c"), "mod"),
        ("colorstrobe", "MH Color Strobe", ("shift", "v"), "mod"),
        ("colorup", "Color +", ("shift", "e"), "modrepeat"),
        ("colordown", "Color -", ("shift", "d"), "modrepeat"),
        ("programup", "Programm +", ("shift", "r"), "modrepeat"),
        ("programdown", "Programm -", ("shift", "f"), "modrepeat"),
        ("gobosup", "Gobos +", ("shift", "t"), "modrepeat"),
        ("gobosdown", "Gobos -", ("shift", "g"), "modrepeat"),
    ]),
    ("sound", "Sound", (0, 120, 150), [
        ("playpause", "Play/Pause", "x", False),
        ("next", "Naechster Track", "s", False),
        ("prev", "Vorheriger Track", "a", False),
        ("micro", "Mikro", "q", True),
        ("microecho", "Mikro Echo", "w", "holdtoggle"),
    ]),
    ("settings", "Settings", (60, 60, 60), [
        ("menu", "Menue", "escape", False),
        ("speedup", "Speed Hoch", "rightArrow", False),
        ("speeddown", "Speed Runter", "leftArrow", False),
        ("repeatspeed", "Repeat Speed", None, "system"),
        ("showtitle", "Schrift AN/AUS", None, "system"),
        ("credits", "Unofficial by BlackMautz", None, "system"),
    ]),
    ("jingles", "Jingles", (180, 150, 0), [
        ("jingle1", "Jingle 1", "f1", False),
        ("jingle2", "Jingle 2", "f2", False),
        ("jingle3", "Jingle 3", "f3", False),
        ("jingle4", "Jingle 4", "f4", False),
        ("jingle5", "Jingle 5", "f5", False),
        ("jingle6", "Jingle 6", "f6", False),
        ("jingle7", "Jingle 7", "f7", False),
        ("jingle8", "Jingle 8", "f8", False),
        ("jingle9", "Jingle 9", "f9", False),
        ("jingle10", "Jingle 10", "f10", False),
        ("jingle11", "Jingle 11", "f11", False),
        ("jingle12", "Jingle 12", "f12", False),
        ("deck1", "Deck 1", ("shift", "f1"), "mod"),
        ("deck2", "Deck 2", ("shift", "f2"), "mod"),
        ("deck3", "Deck 3", ("shift", "f3"), "mod"),
        ("deck4", "Deck 4", ("shift", "f4"), "mod"),
        ("deck5", "Deck 5", ("shift", "f5"), "mod"),
        ("deck6", "Deck 6", ("shift", "f6"), "mod"),
        ("deck7", "Deck 7", ("shift", "f7"), "mod"),
        ("deck8", "Deck 8", ("shift", "f8"), "mod"),
        ("deck9", "Deck 9", ("shift", "f9"), "mod"),
        ("deck10", "Deck 10", ("shift", "f10"), "mod"),
        ("deck11", "Deck 11", ("shift", "f11"), "mod"),
        ("deck12", "Deck 12", ("shift", "f12"), "mod"),
    ]),
]

# â”€â”€â”€ Button-Farben â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
RED = "#ff4444"
GREEN = "#44ff44"
BLUE = "#44aaff"
YELLOW = "#ffcc00"
ORANGE = "#ffaa00"
PURPLE = "#cc66ff"
CYAN = "#00cccc"
WHITE = "#ffffff"
PINK = "#ff66aa"

# â”€â”€â”€ Profil-Seiten (gleiche Anordnung wie vorheriges Profil) â”€
def pbtn(title, ride_id, action_id, font_size=10, color="#ffffff"):
    """Erstellt einen Plugin-Button fuer das eingebettete Profil."""
    return {
        "Controllers": ["Keypad"],
        "Name": PLUGIN_NAME,
        "State": 0,
        "States": [{
            "FontSize": font_size,
            "FontStyle": "Bold",
            "ShowTitle": True,
            "Title": title,
            "TitleAlignment": "middle",
            "TitleColor": color,
        }],
        "UUID": f"{PLUGIN_ID}.{ride_id}.{action_id}",
    }

PAGES = [
    {"name": "BreakDance", "buttons": {
        "0,0": pbtn("NOT-\nAUS", "breakdance", "emergencystop", 12, RED),
        "1,0": pbtn("Anlage\nEIN/AUS", "breakdance", "onoff", 10, GREEN),
        "3,0": pbtn("Kompr.\nAN/AUS", "breakdance", "kompressor", 10, GREEN),
        "0,1": pbtn("Platte\nSpeed -", "breakdance", "plattespeeddown", 10, ORANGE),
        "1,1": pbtn("Platte\nSpeed +", "breakdance", "plattespeedup", 10, ORANGE),
        "2,1": pbtn("Platte\nAN/AUS", "breakdance", "platte", 10, GREEN),
        "3,1": pbtn("Platte\nTippen", "breakdance", "plattetippen", 10, BLUE),
        "0,2": pbtn("Kreuz\nSpeed -", "breakdance", "kreuzspeeddown", 10, ORANGE),
        "1,2": pbtn("Kreuz\nSpeed +", "breakdance", "kreuzspeedup", 10, ORANGE),
        "2,2": pbtn("Kreuz\nAN/AUS", "breakdance", "kreuz", 10, GREEN),
        "3,2": pbtn("Kreuz\nTippen", "breakdance", "kreuztippen", 10, BLUE),
        "0,3": pbtn("Gondel-\nbremse", "breakdance", "gondelbremse", 10, YELLOW),
        "6,3": pbtn("Schrift\n[ AN ]", "settings", "showtitle", 10, CYAN),
        "7,3": pbtn("Repeat\nSchnell", "settings", "repeatspeed", 10, CYAN),
    }},
    {"name": "StarLight", "buttons": {
        "0,0": pbtn("NOT-\nAUS", "starlight", "emergencystop", 12, RED),
        "1,0": pbtn("Anlage\nEIN/AUS", "starlight", "onoff", 10, GREEN),
        "2,0": pbtn("Reset", "starlight", "reset", 10, YELLOW),
        "3,0": pbtn("Parking", "starlight", "parking", 10, BLUE),
        "5,0": pbtn("Gondel\nPumpe", "starlight", "gondelpumpe", 10, GREEN),
        "7,0": pbtn("Arm\nPumpe", "starlight", "armpumpe", 10, GREEN),
        "2,1": pbtn("Gondola\nSpeed -", "starlight", "gondolaspeeddown", 10, ORANGE),
        "3,1": pbtn("Gondola\nSpeed +", "starlight", "gondolaspeedup", 10, ORANGE),
        "4,1": pbtn("Gondola\nBremse", "starlight", "gondolabremse", 10, YELLOW),
        "5,1": pbtn("Gondel 0", "starlight", "gondel0", 10, BLUE),
        "2,2": pbtn("Arm\nSpeed -", "starlight", "armspeeddown", 10, ORANGE),
        "3,2": pbtn("Arm\nSpeed +", "starlight", "armspeedup", 10, ORANGE),
        "4,2": pbtn("Arm\nBremse", "starlight", "armbremse", 10, YELLOW),
        "5,2": pbtn("Arm 0", "starlight", "arm0", 10, BLUE),
        "2,3": pbtn("Platform\nHoch", "starlight", "platformup", 10, GREEN),
        "3,3": pbtn("Platform\nRunter", "starlight", "platformdown", 10, RED),
        "6,3": pbtn("Schrift\n[ AN ]", "settings", "showtitle", 10, CYAN),
        "7,3": pbtn("Repeat\\nSchnell", "settings", "repeatspeed", 10, CYAN),
    }},
    {"name": "XPlosion + FunHouse", "buttons": {
        "0,0": pbtn("NOT-AUS\nXPlosion", "xplosion", "emergencystop", 9, RED),
        "1,0": pbtn("Anlage\nEIN/AUS", "xplosion", "onoff", 10, GREEN),
        "2,0": pbtn("Reset", "xplosion", "reset", 10, YELLOW),
        "3,0": pbtn("Freigabe", "xplosion", "freigabe", 10, GREEN),
        "0,1": pbtn("Hoch", "xplosion", "up", 11, ORANGE),
        "1,1": pbtn("Runter", "xplosion", "down", 11, ORANGE),
        "2,1": pbtn("Null", "xplosion", "zero", 11, BLUE),
        "0,2": pbtn("NOT-AUS\nFunHouse", "funhouse", "emergencystop", 9, RED),
        "1,2": pbtn("Anlage\nEIN/AUS", "funhouse", "onoff", 10, GREEN),
        "3,2": pbtn("Drehsch.\n1.OG", "funhouse", "turntable1", 9, PURPLE),
        "4,2": pbtn("Drehsch.\n2.OG", "funhouse", "turntable2", 9, PURPLE),
        "5,2": pbtn("Drehsch.\nDach", "funhouse", "turntable3", 9, PURPLE),
        "6,2": pbtn("Laufband\n1.OG", "funhouse", "conveyor1", 9, CYAN),
        "7,2": pbtn("Laufband\n2.OG", "funhouse", "conveyor2", 9, CYAN),
        "3,3": pbtn("Vibrier-\nplatte", "funhouse", "vibrate1", 9, PINK),
        "4,3": pbtn("Dreh-\ntunnel", "funhouse", "tunnel1", 9, PINK),
    }},
    {"name": "Rotator", "buttons": {
        "0,0": pbtn("NOT-\nAUS", "rotator", "emergencystop", 12, RED),
        "1,0": pbtn("Anlage\nEIN/AUS", "rotator", "onoff", 10, GREEN),
        "2,0": pbtn("Reset", "rotator", "reset", 10, YELLOW),
        "3,0": pbtn("Park", "rotator", "park", 10, BLUE),
        "4,0": pbtn("Pumpe\nAN/AUS", "rotator", "pumpe", 10, GREEN),
        "5,0": pbtn("Kompr.\nAN/AUS", "rotator", "kompressor", 10, GREEN),
        "0,1": pbtn("Platte\nSpeed -", "rotator", "plattespeeddown", 10, ORANGE),
        "1,1": pbtn("Platte\nSpeed +", "rotator", "plattespeedup", 10, ORANGE),
        "2,1": pbtn("Platte 0", "rotator", "platte0", 10, BLUE),
        "3,1": pbtn("Platte\nAN/AUS", "rotator", "platte", 10, GREEN),
        "0,2": pbtn("Kreuz\nSpeed -", "rotator", "kreuzspeeddown", 10, ORANGE),
        "1,2": pbtn("Kreuz\nSpeed +", "rotator", "kreuzspeedup", 10, ORANGE),
        "2,2": pbtn("Kreuz 0", "rotator", "kreuz0", 10, BLUE),
        "3,2": pbtn("Kreuz\nAN/AUS", "rotator", "kreuz", 10, GREEN),
        "5,1": pbtn("Inverter\nSpeed -", "rotator", "inverterspeeddown", 9, PURPLE),
        "6,1": pbtn("Inverter\nSpeed +", "rotator", "inverterspeedup", 9, PURPLE),
        "7,1": pbtn("Invers. 0", "rotator", "inverter0", 10, BLUE),
        "5,2": pbtn("Inverter\nAN/AUS", "rotator", "inverter", 9, GREEN),
        "0,3": pbtn("Buegel\nAUF/ZU", "rotator", "buegel", 10, GREEN),
        "2,3": pbtn("Hub\nHoch", "rotator", "hubup", 10, GREEN),
        "3,3": pbtn("Hub\nStop", "rotator", "hubstop", 10, YELLOW),
        "4,3": pbtn("Hub\nRunter", "rotator", "hubdown", 10, RED),
        "6,3": pbtn("Schrift\n[ AN ]", "settings", "showtitle", 10, CYAN),
        "7,3": pbtn("Repeat\\nSchnell", "settings", "repeatspeed", 10, CYAN),
    }},
    {"name": "Turaka + Standard", "buttons": {
        "0,0": pbtn("NOT-AUS\nTuraka", "turaka", "emergencystop", 9, RED),
        "1,0": pbtn("Anlage\nEIN/AUS", "turaka", "onoff", 10, GREEN),
        "2,0": pbtn("Reset", "turaka", "reset", 10, YELLOW),
        "3,0": pbtn("Speed -", "turaka", "speeddown", 10, ORANGE),
        "4,0": pbtn("Speed +", "turaka", "speedup", 10, ORANGE),
        "5,0": pbtn("Richtung", "turaka", "direction", 10, PURPLE),
        "0,1": pbtn("Start", "turaka", "start", 11, GREEN),
        "1,1": pbtn("Stop", "turaka", "stop", 11, RED),
        "2,1": pbtn("Platform", "turaka", "platform", 10, BLUE),
        "3,1": pbtn("Park\nWagen 1", "turaka", "parkcar1", 10, BLUE),
        "4,1": pbtn("Park\nWagen 2", "turaka", "parkcar2", 10, BLUE),
        "0,2": pbtn("Ein-/Aus-\nsteigen", "standard", "enterleave", 9, GREEN),
        "1,2": pbtn("Push\nto Talk", "standard", "pushtotalk", 10, YELLOW),
        "2,2": pbtn("Naechster\nSitz", "standard", "nextseat", 10, BLUE),
        "3,2": pbtn("Letzter\nSitz", "standard", "lastseat", 10, BLUE),
        "4,2": pbtn("Kamera\nwechsel", "standard", "camera", 10, PURPLE),
        "5,2": pbtn("Chat", "standard", "chat", 11, WHITE),
        "6,2": pbtn("Ingame\nVoice", "standard", "ingamevoice", 10, YELLOW),
        "0,3": pbtn("Menue", "settings", "menu", 10, WHITE),
        "1,3": pbtn("Speed\nHoch", "settings", "speedup", 10, GREEN),
        "2,3": pbtn("Speed\nRunter", "settings", "speeddown", 10, RED),
        "2,3": pbtn("Schrift\n[ AN ]", "settings", "showtitle", 10, CYAN),
        "3,3": pbtn("Repeat\\nSchnell", "settings", "repeatspeed", 10, CYAN),
    }},
    {"name": "LightEffect", "buttons": {
        "0,0": pbtn("Preset 1", "lighteffect", "preset1", 10, PURPLE),
        "1,0": pbtn("Preset 2", "lighteffect", "preset2", 10, PURPLE),
        "2,0": pbtn("Preset 3", "lighteffect", "preset3", 10, PURPLE),
        "3,0": pbtn("Preset 4", "lighteffect", "preset4", 10, PURPLE),
        "4,0": pbtn("Preset 5", "lighteffect", "preset5", 10, PURPLE),
        "5,0": pbtn("Preset 6", "lighteffect", "preset6", 10, PURPLE),
        "6,0": pbtn("Preset 7", "lighteffect", "preset7", 10, PURPLE),
        "7,0": pbtn("Preset 8", "lighteffect", "preset8", 10, PURPLE),
        "0,1": pbtn("Preset 9", "lighteffect", "preset9", 10, PURPLE),
        "1,1": pbtn("Light 1", "lighteffect", "light1", 10, CYAN),
        "2,1": pbtn("Light 2", "lighteffect", "light2", 10, CYAN),
        "3,1": pbtn("Light 3", "lighteffect", "light3", 10, CYAN),
        "4,1": pbtn("Light 4", "lighteffect", "light4", 10, CYAN),
        "5,1": pbtn("Light 5", "lighteffect", "light5", 10, CYAN),
        "6,1": pbtn("Light 6", "lighteffect", "light6", 10, CYAN),
        "7,1": pbtn("Light 7", "lighteffect", "light7", 10, CYAN),
        "0,2": pbtn("Light 8", "lighteffect", "light8", 10, CYAN),
        "1,2": pbtn("Light 9", "lighteffect", "light9", 10, CYAN),
        "2,2": pbtn("Alle\nAUS", "lighteffect", "alloff", 10, RED),
        "3,2": pbtn("Strobo", "lighteffect", "strobo", 10, YELLOW),
        "4,2": pbtn("LED\nStrobe", "lighteffect", "ledstrobe", 10, YELLOW),
        "5,2": pbtn("Color\nStrobe", "lighteffect", "colorstrobe", 10, YELLOW),
        "6,2": pbtn("Spot\nAN/AUS", "lighteffect", "spotonoff", 10, GREEN),
        "7,2": pbtn("SpotColor\nHoch", "lighteffect", "spotcolorup", 10, ORANGE),
        "0,3": pbtn("SpotColor\nRunter", "lighteffect", "spotcolordown", 10, ORANGE),
        "1,3": pbtn("Nebel", "lighteffect", "fog", 10, BLUE),
        "2,3": pbtn("Flamme", "lighteffect", "flame", 10, RED),
        "3,3": pbtn("Seifenbl.", "lighteffect", "bubbles", 10, BLUE),
        "4,3": pbtn("Horn", "lighteffect", "horn", 11, YELLOW),
        "6,3": pbtn("Schrift\n[ AN ]", "settings", "showtitle", 10, CYAN),
        "7,3": pbtn("Repeat\\nSchnell", "settings", "repeatspeed", 10, CYAN),
    }},
    {"name": "MovingHeads + Sound", "buttons": {
        "0,0": pbtn("Moving\nHead AN", "movingheads", "onoff", 10, GREEN),
        "1,0": pbtn("MH\nLicht", "movingheads", "light", 10, YELLOW),
        "2,0": pbtn("MH Light\nSync", "movingheads", "lightsync", 10, BLUE),
        "3,0": pbtn("MH Color\nStrobe", "movingheads", "colorstrobe", 10, PURPLE),
        "0,1": pbtn("Color\nHoch", "movingheads", "colorup", 10, ORANGE),
        "1,1": pbtn("Color\nRunter", "movingheads", "colordown", 10, ORANGE),
        "2,1": pbtn("Progr.\nHoch", "movingheads", "programup", 10, CYAN),
        "3,1": pbtn("Progr.\nRunter", "movingheads", "programdown", 10, CYAN),
        "4,1": pbtn("Gobos\nHoch", "movingheads", "gobosup", 10, PINK),
        "5,1": pbtn("Gobos\nRunter", "movingheads", "gobosdown", 10, PINK),
        "0,2": pbtn("Play /\nPause", "sound", "playpause", 10, GREEN),
        "1,2": pbtn("Naechster\nTrack", "sound", "next", 10, BLUE),
        "2,2": pbtn("Vorher.\nTrack", "sound", "prev", 10, BLUE),
        "3,2": pbtn("Mikro", "sound", "micro", 10, YELLOW),
        "4,2": pbtn("Mikro\nEcho", "sound", "microecho", 10, PURPLE),
        "5,3": pbtn("Unofficial\nby BlackMautz", "settings", "credits", 7, WHITE),
        "6,3": pbtn("Schrift\n[ AN ]", "settings", "showtitle", 10, CYAN),
        "7,3": pbtn("Repeat\\nSchnell", "settings", "repeatspeed", 10, CYAN),
    }},
    {"name": "Jingles", "buttons": {
        "0,0": pbtn("Jingle 1", "jingles", "jingle1", 10, YELLOW),
        "1,0": pbtn("Jingle 2", "jingles", "jingle2", 10, YELLOW),
        "2,0": pbtn("Jingle 3", "jingles", "jingle3", 10, YELLOW),
        "3,0": pbtn("Jingle 4", "jingles", "jingle4", 10, YELLOW),
        "4,0": pbtn("Jingle 5", "jingles", "jingle5", 10, YELLOW),
        "5,0": pbtn("Jingle 6", "jingles", "jingle6", 10, YELLOW),
        "6,0": pbtn("Jingle 7", "jingles", "jingle7", 10, ORANGE),
        "7,0": pbtn("Jingle 8", "jingles", "jingle8", 10, ORANGE),
        "0,1": pbtn("Jingle 9", "jingles", "jingle9", 10, ORANGE),
        "1,1": pbtn("Jingle 10", "jingles", "jingle10", 10, ORANGE),
        "2,1": pbtn("Jingle 11", "jingles", "jingle11", 10, ORANGE),
        "3,1": pbtn("Jingle 12", "jingles", "jingle12", 10, ORANGE),
        "0,2": pbtn("Deck 1", "jingles", "deck1", 10, PURPLE),
        "1,2": pbtn("Deck 2", "jingles", "deck2", 10, PURPLE),
        "2,2": pbtn("Deck 3", "jingles", "deck3", 10, PURPLE),
        "3,2": pbtn("Deck 4", "jingles", "deck4", 10, PURPLE),
        "4,2": pbtn("Deck 5", "jingles", "deck5", 10, PURPLE),
        "5,2": pbtn("Deck 6", "jingles", "deck6", 10, PURPLE),
        "6,2": pbtn("Deck 7", "jingles", "deck7", 10, CYAN),
        "7,2": pbtn("Deck 8", "jingles", "deck8", 10, CYAN),
        "0,3": pbtn("Deck 9", "jingles", "deck9", 10, CYAN),
        "1,3": pbtn("Deck 10", "jingles", "deck10", 10, CYAN),
        "2,3": pbtn("Deck 11", "jingles", "deck11", 10, CYAN),
        "3,3": pbtn("Deck 12", "jingles", "deck12", 10, CYAN),
    }},
]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Hilfsfunktionen
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def create_png(width, height, r, g, b):
    """Erstellt ein einfarbiges PNG-Bild."""
    def chunk(ctype, data):
        crc = struct.pack('>I', zlib.crc32(ctype + data) & 0xffffffff)
        return struct.pack('>I', len(data)) + ctype + data + crc

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    row = struct.pack('BBB', r, g, b) * width
    raw = b''
    for _ in range(height):
        raw += b'\x00' + row
    idat = chunk(b'IDAT', zlib.compress(raw, 9))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend


def generate_map_entries():
    """Generiert C# Dictionary-Eintraege fuer alle Aktionen."""
    lines = []
    for ride_id, _, _, actions in RIDES:
        for action in actions:
            action_id, label, key_data, mode = action
            uuid = f"{PLUGIN_ID}.{ride_id}.{action_id}"
            if mode == "holdtoggle":
                scan = SCAN[key_data]
                ext = key_data in EXTENDED_KEYS
                flags = 8 | (1 if ext else 0)
                lines.append(f'        tg["{uuid}"]=new TG{{sOn=0x{scan:02X},fOn={flags},mOn=0,sOff=0x{scan:02X},fOff={flags},mOff=0}};')
                lines.append(f'        ht.Add("{uuid}");')
            elif mode == "toggle":
                key_on, key_off = key_data
                if isinstance(key_on, tuple):
                    mod_on_key, k_on = key_on
                    scan_mod_on = SCAN[mod_on_key]
                    scan_on = SCAN[k_on]
                    ext_on = k_on in EXTENDED_KEYS
                else:
                    scan_mod_on = 0
                    scan_on = SCAN[key_on]
                    ext_on = key_on in EXTENDED_KEYS
                if isinstance(key_off, tuple):
                    mod_off_key, k_off = key_off
                    scan_mod_off = SCAN[mod_off_key]
                    scan_off = SCAN[k_off]
                    ext_off = k_off in EXTENDED_KEYS
                else:
                    scan_mod_off = 0
                    scan_off = SCAN[key_off]
                    ext_off = key_off in EXTENDED_KEYS
                flags_on = 8 | (1 if ext_on else 0)
                flags_off = 8 | (1 if ext_off else 0)
                lines.append(f'        tg["{uuid}"]=new TG{{sOn=0x{scan_on:02X},fOn={flags_on},mOn=0x{scan_mod_on:02X},sOff=0x{scan_off:02X},fOff={flags_off},mOff=0x{scan_mod_off:02X}}};')
            elif mode in ("mod", "modhold"):
                mod_key, main_key = key_data
                scan_mod = SCAN[mod_key]
                scan_main = SCAN[main_key]
                ext = main_key in EXTENDED_KEYS
                flags = 8 | (1 if ext else 0)
                hold = "true" if mode == "modhold" else "false"
                lines.append(f'        km["{uuid}"]=new KI{{s=0x{scan_main:02X},f={flags},h={hold},m=0x{scan_mod:02X}}};')
            elif mode == "repeat":
                scan = SCAN[key_data]
                ext = key_data in EXTENDED_KEYS
                flags = 8 | (1 if ext else 0)
                lines.append(f'        km["{uuid}"]=new KI{{s=0x{scan:02X},f={flags},h=true}};')
                lines.append(f'        rp.Add("{uuid}");')
            elif mode == "modrepeat":
                mod_key, main_key = key_data
                scan_mod = SCAN[mod_key]
                scan_main = SCAN[main_key]
                ext = main_key in EXTENDED_KEYS
                flags = 8 | (1 if ext else 0)
                lines.append(f'        km["{uuid}"]=new KI{{s=0x{scan_main:02X},f={flags},h=true,m=0x{scan_mod:02X}}};')
                lines.append(f'        rp.Add("{uuid}");')
            elif mode == "system":
                pass
            else:
                scan = SCAN[key_data]
                ext = key_data in EXTENDED_KEYS
                flags = 8 | (1 if ext else 0)
                hold = "true" if mode else "false"
                lines.append(f'        km["{uuid}"]=new KI{{s=0x{scan:02X},f={flags},h={hold}}};')
    return '\n'.join(lines)


def generate_title_entries():
    """Generiert C# Dictionary-Eintraege fuer Button-Titel aus PAGES (formatiert mit Zeilenumbruechen)."""
    lines = []
    seen = set()
    # Zuerst die schoen formatierten Titel aus den PAGES nehmen
    for page_def in PAGES:
        for pos, btn in page_def["buttons"].items():
            uuid = btn["UUID"]
            title = btn["States"][0]["Title"]
            safe_title = title.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            lines.append(f'        tm["{uuid}"]="{safe_title}";')
            seen.add(uuid)
    # Dann fehlende aus RIDES ergaenzen (falls ein Button nicht in PAGES ist)
    for ride_id, ride_name, _, actions in RIDES:
        for action in actions:
            action_id, label, _, mode = action
            uuid = f"{PLUGIN_ID}.{ride_id}.{action_id}"
            if uuid not in seen:
                safe_label = label.replace('\\', '\\\\').replace('"', '\\"')
                lines.append(f'        tm["{uuid}"]="{safe_label}";')
    return '\n'.join(lines)


def generate_cs():
    """Generiert den C# Quellcode fuer das Plugin."""
    map_entries = generate_map_entries()
    title_entries = generate_title_entries()
    return f'''using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.WebSockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

class P
{{
    [DllImport("user32.dll")]
    static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

    struct KI {{ public byte s; public uint f; public bool h; public byte m; }}
    struct TG {{ public byte sOn; public uint fOn; public byte mOn; public byte sOff; public uint fOff; public byte mOff; }}
    static Dictionary<string, KI> km = new Dictionary<string, KI>();
    static Dictionary<string, TG> tg = new Dictionary<string, TG>();
    static HashSet<string> ht = new HashSet<string>();
    static Dictionary<string, bool> ts = new Dictionary<string, bool>();
    static Dictionary<string, string> tm = new Dictionary<string, string>();
    static Dictionary<string, string> ca = new Dictionary<string, string>();
    static Dictionary<string, string> imgOff = new Dictionary<string, string>();
    static Dictionary<string, string> imgOn = new Dictionary<string, string>();
    static ClientWebSocket ws;
    static string logPath;
    static HashSet<string> rp = new HashSet<string>();
    static Dictionary<string, int> rg = new Dictionary<string, int>();
    static int repeatMs = 120;
    static int repeatLv = 1;
    static string[] repeatNm = {{"Langsam", "Mittel", "Schnell"}};
    static int[] repeatSp = {{250, 120, 50}};
    static string repeatCtx = null;
    static bool showTitles = true;
    static string titleCtx = null;
    static Dictionary<string, string> ac = new Dictionary<string, string>();

    static void Log(string msg)
    {{
        try {{ File.AppendAllText(logPath, DateTime.Now.ToString("HH:mm:ss.fff") + " " + msg + "\\n"); }}
        catch {{ }}
    }}

    static int Main(string[] args)
    {{
        try
        {{
            logPath = Path.Combine(Path.GetDirectoryName(
                System.Reflection.Assembly.GetExecutingAssembly().Location),
                "plugin.log");
            Log("=== Plugin gestartet ===");
            Log("Args: " + string.Join(" ", args));
            Run(args).GetAwaiter().GetResult();
            return 0;
        }}
        catch (Exception ex)
        {{
            try {{ Log("FATAL: " + ex.ToString()); }} catch {{ }}
            return 1;
        }}
    }}

    static async Task Run(string[] args)
    {{
        string port = "", uuid = "", reg = "";
        for (int i = 0; i < args.Length - 1; i++)
        {{
            if (args[i] == "-port") port = args[i + 1];
            else if (args[i] == "-pluginUUID") uuid = args[i + 1];
            else if (args[i] == "-registerEvent") reg = args[i + 1];
        }}

        Log("Port=" + port + " UUID=" + uuid + " Reg=" + reg);
        Init();
        var dir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
        var actDir = Path.Combine(dir, "imgs", "actions");
        if (Directory.Exists(actDir))
        {{
            foreach (var rideDir in Directory.GetDirectories(actDir))
            {{
                string ride = Path.GetFileName(rideDir);
                foreach (var f in Directory.GetFiles(rideDir, "*.png"))
                {{
                    string fn = Path.GetFileNameWithoutExtension(f);
                    string b64 = "data:image/png;base64," + Convert.ToBase64String(File.ReadAllBytes(f));
                    string prefix = ride + "_";
                    if (!fn.StartsWith(prefix)) continue;
                    string rest = fn.Substring(prefix.Length);
                    int li = rest.LastIndexOf('_');
                    if (li < 0) continue;
                    string actId = rest.Substring(0, li);
                    string state = rest.Substring(li + 1);
                    string auid = "{PLUGIN_ID}." + ride + "." + actId;
                    if (state == "idle" || state == "off")
                        imgOff[auid] = b64;
                    else
                        imgOn[auid] = b64;
                }}
            }}
        }}
        Log("Init done, " + km.Count + " actions, " + tg.Count + " toggles, " + rp.Count + " repeats, " + tm.Count + " titles, " + imgOff.Count + "/" + imgOn.Count + " icons loaded");

        ws = new ClientWebSocket();
        Log("Connecting to ws://localhost:" + port);
        await ws.ConnectAsync(new Uri("ws://localhost:" + port), CancellationToken.None);
        Log("Connected!");

        var enc = Encoding.UTF8;
        var regMsg = "{{\\"event\\":\\"" + reg + "\\",\\"uuid\\":\\"" + uuid + "\\"}}";
        Log("Sending registration: " + regMsg);
        await ws.SendAsync(
            new ArraySegment<byte>(enc.GetBytes(regMsg)),
            WebSocketMessageType.Text, true, CancellationToken.None);
        Log("Registration sent!");

        var ut = new Thread(() => CU(dir));
        ut.IsBackground = true;
        ut.Start();

        var buf = new byte[65536];
        while (ws.State == WebSocketState.Open)
        {{
            try
            {{
                var r = await ws.ReceiveAsync(new ArraySegment<byte>(buf), CancellationToken.None);
                if (r.MessageType == WebSocketMessageType.Close) {{ Log("WS closed"); break; }}
                var msg = enc.GetString(buf, 0, r.Count);
                Msg(msg);
            }}
            catch (Exception ex) {{ Log("Receive error: " + ex.Message); break; }}
        }}
        Log("Plugin beendet");
    }}

    static string V(string j, string k)
    {{
        int i = j.IndexOf("\\"" + k + "\\":\\"");
        if (i < 0) return null;
        i += k.Length + 4;
        int e = j.IndexOf('"', i);
        return e < 0 ? null : j.Substring(i, e - i);
    }}

    static void SetImg(string context, bool isOn)
    {{
        if (context == null) return;
        string act;
        if (!ca.TryGetValue(context, out act)) return;
        var d = isOn ? imgOn : imgOff;
        string img;
        if (!d.TryGetValue(act, out img)) return;
        var si = "{{\\"event\\":\\"setImage\\",\\"context\\":\\"" + context +
            "\\",\\"payload\\":{{\\"image\\":\\"" + img + "\\",\\"target\\":0}}}}";
        Send(si);
    }}

    static void SetTtl(string context, string title)
    {{
        if (context == null || title == null) return;
        var sb = new System.Text.StringBuilder();
        sb.Append("{{\\"event\\":\\"setTitle\\",\\"context\\":\\"");
        sb.Append(context);
        sb.Append("\\",\\"payload\\":{{\\"title\\":\\"");
        foreach (char c in title)
        {{
            if (c == '\\\\') sb.Append("\\\\\\\\");
            else if (c == '"') sb.Append("\\\\\\"");
            else if (c == '\\n') sb.Append("\\\\n");
            else sb.Append(c);
        }}
        sb.Append("\\",\\"target\\":0}}}}");
        Send(sb.ToString());
    }}

    static void Send(string msg)
    {{
        try
        {{
            var bytes = Encoding.UTF8.GetBytes(msg);
            ws.SendAsync(new ArraySegment<byte>(bytes),
                WebSocketMessageType.Text, true, CancellationToken.None)
                .GetAwaiter().GetResult();
        }}
        catch (Exception ex) {{ Log("Send error: " + ex.Message); }}
    }}

    static void Msg(string j)
    {{
        string ev = V(j, "event");
        string action = V(j, "action");
        string context = V(j, "context");

        if (ev == "willAppear" && action != null && context != null)
        {{
            ca[context] = action;
            Log("willAppear: " + action + " hasTm=" + tm.ContainsKey(action) + " isTg=" + tg.ContainsKey(action));
            if (action == "{PLUGIN_ID}.settings.repeatspeed")
            {{
                repeatCtx = context;
                SetImg(context, false);
                SetTtl(context, "Repeat\\n" + repeatNm[repeatLv]);
            }}
            else if (action == "{PLUGIN_ID}.settings.showtitle")
            {{
                titleCtx = context;
                SetImg(context, false);
                SetTtl(context, "Schrift\\n" + (showTitles ? "[ AN ]" : "[ AUS ]"));
            }}
            else if (action == "{PLUGIN_ID}.settings.credits")
            {{
                SetImg(context, false);
                SetTtl(context, "Unofficial\\nby BlackMautz");
            }}
            else if (tg.ContainsKey(action))
            {{
                bool isOn = ts.ContainsKey(action) && ts[action];
                SetImg(context, isOn);
                if (showTitles)
                {{
                    var title = tm.ContainsKey(action) ? tm[action] : action;
                    var fullTitle = title + "\\n" + (isOn ? "[ AN ]" : "[ AUS ]");
                    SetTtl(context, fullTitle);
                    Log("Title(tg): " + fullTitle.Replace("\\n", "|"));
                }}
                else
                    SetTtl(context, "");
                ac[context] = action;
            }}
            else
            {{
                SetImg(context, false);
                if (showTitles && tm.ContainsKey(action))
                {{
                    SetTtl(context, tm[action]);
                    Log("Title(btn): " + tm[action].Replace("\\n", "|"));
                }}
                else
                    SetTtl(context, "");
                ac[context] = action;
            }}
        }}
        else if (ev == "keyDown" && action != null && tg.ContainsKey(action) && context != null)
        {{
            var ti = tg[action];
            bool isOn = ts.ContainsKey(action) && ts[action];
            bool newState = !isOn;
            ts[action] = newState;
            if (ht.Contains(action))
            {{
                if (newState)
                {{
                    Log("HoldToggle AN: " + action + " scan=0x" + ti.sOn.ToString("X2"));
                    if (ti.mOn > 0) keybd_event(0, ti.mOn, 8u, UIntPtr.Zero);
                    keybd_event(0, ti.sOn, ti.fOn, UIntPtr.Zero);
                }}
                else
                {{
                    Log("HoldToggle AUS: " + action + " scan=0x" + ti.sOff.ToString("X2"));
                    keybd_event(0, ti.sOff, ti.fOff | 2u, UIntPtr.Zero);
                    if (ti.mOff > 0) keybd_event(0, ti.mOff, 8u | 2u, UIntPtr.Zero);
                }}
            }}
            else
            {{
                byte scan = isOn ? ti.sOff : ti.sOn;
                uint flags = isOn ? ti.fOff : ti.fOn;
                byte mod = isOn ? ti.mOff : ti.mOn;
                Log("Toggle: " + action + " -> " + (newState ? "AN" : "AUS") + " scan=0x" + scan.ToString("X2") + (mod > 0 ? " mod=0x" + mod.ToString("X2") : ""));
                if (mod > 0) keybd_event(0, mod, 8u, UIntPtr.Zero);
                keybd_event(0, scan, flags, UIntPtr.Zero);
                Thread.Sleep(300);
                keybd_event(0, scan, flags | 2u, UIntPtr.Zero);
                if (mod > 0) keybd_event(0, mod, 8u | 2u, UIntPtr.Zero);
            }}
            SetImg(context, newState);
            if (showTitles)
            {{
                var title = tm.ContainsKey(action) ? tm[action] : action;
                SetTtl(context, title + "\\n" + (newState ? "[ AN ]" : "[ AUS ]"));
            }}
        }}
        else if (ev == "keyDown" && action == "{PLUGIN_ID}.settings.showtitle" && context != null)
        {{
            showTitles = !showTitles;
            SetTtl(context, "Schrift\\n" + (showTitles ? "[ AN ]" : "[ AUS ]"));
            Log("ShowTitles: " + showTitles);
            foreach (var kv in ac)
            {{
                var ctx = kv.Key;
                var act = kv.Value;
                if (tg.ContainsKey(act))
                {{
                    if (showTitles)
                    {{
                        bool on2 = ts.ContainsKey(act) && ts[act];
                        var t2 = tm.ContainsKey(act) ? tm[act] : act;
                        SetTtl(ctx, t2 + "\\n" + (on2 ? "[ AN ]" : "[ AUS ]"));
                    }}
                    else SetTtl(ctx, "");
                }}
                else
                {{
                    if (showTitles && tm.ContainsKey(act)) SetTtl(ctx, tm[act]);
                    else SetTtl(ctx, "");
                }}
            }}
        }}
        else if (ev == "keyDown" && action == "{PLUGIN_ID}.settings.repeatspeed" && context != null)
        {{
            repeatLv = (repeatLv + 1) % 3;
            repeatMs = repeatSp[repeatLv];
            SetTtl(context, "Repeat\\n" + repeatNm[repeatLv]);
            Log("RepeatSpeed: " + repeatNm[repeatLv] + " " + repeatMs + "ms");
        }}
        else if (ev == "keyDown" && action != null && km.ContainsKey(action))
        {{
            var ki = km[action];
            if (rp.Contains(action))
            {{
                if (!rg.ContainsKey(action)) rg[action] = 0;
                int gen = ++rg[action];
                var a = action;
                var ki2 = ki;
                var t = new Thread(() => {{
                    if (ki2.m > 0) keybd_event(0, ki2.m, 8u, UIntPtr.Zero);
                    keybd_event(0, ki2.s, ki2.f, UIntPtr.Zero);
                    keybd_event(0, ki2.s, ki2.f | 2u, UIntPtr.Zero);
                    for (int d = 0; d < 500 && rg[a] == gen; d += 10) Thread.Sleep(10);
                    int delay = 500;
                    while (rg[a] == gen)
                    {{
                        keybd_event(0, ki2.s, ki2.f, UIntPtr.Zero);
                        keybd_event(0, ki2.s, ki2.f | 2u, UIntPtr.Zero);
                        for (int w = 0; w < delay && rg[a] == gen; w += 10) Thread.Sleep(10);
                        if (delay > 100) delay -= 50;
                    }}
                    if (ki2.m > 0) keybd_event(0, ki2.m, 8u | 2u, UIntPtr.Zero);
                }});
                t.IsBackground = true;
                t.Start();
                Log("Repeat accel start: " + action);
            }}
            else
            {{
                Log("KeyDown: " + action + " scan=0x" + ki.s.ToString("X2") + (ki.m > 0 ? " mod=0x" + ki.m.ToString("X2") : ""));
                if (ki.m > 0) keybd_event(0, ki.m, 8u, UIntPtr.Zero);
                keybd_event(0, ki.s, ki.f, UIntPtr.Zero);
                if (!ki.h)
                {{
                    Thread.Sleep(50);
                    keybd_event(0, ki.s, ki.f | 2u, UIntPtr.Zero);
                    if (ki.m > 0) keybd_event(0, ki.m, 8u | 2u, UIntPtr.Zero);
                }}
            }}
        }}
        else if (ev == "keyUp" && action != null && km.ContainsKey(action))
        {{
            var ki = km[action];
            if (rp.Contains(action))
            {{
                if (rg.ContainsKey(action)) rg[action]++;
                Log("Repeat stop: " + action);
            }}
            else if (ki.h)
            {{
                Log("KeyUp: " + action);
                keybd_event(0, ki.s, ki.f | 2u, UIntPtr.Zero);
                if (ki.m > 0) keybd_event(0, ki.m, 8u | 2u, UIntPtr.Zero);
            }}
        }}
    }}

    static void CU(string dir)
    {{
        try
        {{
            Thread.Sleep(15000);
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072;
            string vf = Path.Combine(dir, "VERSION");
            string lv = File.Exists(vf) ? File.ReadAllText(vf).Trim() : "0";
            using (var wc = new WebClient())
            {{
                wc.Headers.Add("User-Agent", "FairgroundOnline-StreamDeck");
                string rv = wc.DownloadString("https://raw.githubusercontent.com/BlackMautz/FairgroundOnline-StreamDeck/master/VERSION").Trim();
                Log("Version: lokal=" + lv + " remote=" + rv);
                if (rv == lv) {{ Log("Plugin aktuell v" + lv); return; }}
                Log("Update " + lv + " -> " + rv);
                string tmp = Path.Combine(Path.GetTempPath(), "Fairground_Online.streamDeckPlugin");
                wc.DownloadFile("https://github.com/BlackMautz/FairgroundOnline-StreamDeck/releases/latest/download/Fairground_Online.streamDeckPlugin", tmp);
                if (new FileInfo(tmp).Length < 10000) {{ Log("Update: Download zu klein, abgebrochen"); File.Delete(tmp); return; }}
                Log("Update heruntergeladen, starte Installation...");
                Process.Start(tmp);
            }}
        }}
        catch (Exception ex) {{ Log("Update: " + ex.Message); }}
    }}

    static void Init()
    {{
{map_entries}
{title_entries}
    }}
}}
'''


def generate_manifest():
    """Generiert die manifest.json fuer das Plugin."""
    # Reihenfolge: Fahrgeschaefte zuerst, Sound/Mic ganz unten
    MANIFEST_ORDER = [
        "breakdance", "starlight", "xplosion", "funhouse", "rotator", "turaka",
        "lighteffect", "movingheads", "sound","jingles", "standard", "settings",
    ]
    rides_by_id = {r[0]: r for r in RIDES}
    ordered_rides = [rides_by_id[rid] for rid in MANIFEST_ORDER if rid in rides_by_id]
    # Fuer Rides die nicht in MANIFEST_ORDER sind, am Ende anfuegen
    for r in RIDES:
        if r[0] not in MANIFEST_ORDER:
            ordered_rides.append(r)

    actions = []
    for ride_id, ride_name, _, action_list in ordered_rides:
        # Separator/Header fuer jede Kategorie
        cat_icon = f"imgs/categories/{ride_id}"
        actions.append({
            "Icon": cat_icon,
            "Name": f"\u2501\u2501\u2501 {ride_name} \u2501\u2501\u2501",
            "States": [{"Image": cat_icon, "ShowTitle": True, "TitleAlignment": "bottom"}],
            "Tooltip": f"Kategorie: {ride_name}",
            "UUID": f"{PLUGIN_ID}.sep.{ride_id}",
        })
        for action in action_list:
            action_id, label, _, mode = action
            # Bestimme idle-Bildname basierend auf Modus
            if mode == "toggle":
                idle_name = f"{ride_id}_{action_id}_off"
            else:
                idle_name = f"{ride_id}_{action_id}_idle"
            icon_path = f"imgs/actions/{ride_id}/{idle_name}"
            actions.append({
                "Icon": icon_path,
                "Name": f"    {label}",
                "States": [{"Image": icon_path, "ShowTitle": True, "TitleAlignment": "bottom"}],
                "Tooltip": f"{ride_name} - {label}",
                "UUID": f"{PLUGIN_ID}.{ride_id}.{action_id}",
            })

    manifest = {
        "Actions": actions,
        "Author": PLUGIN_AUTHOR,
        "Category": PLUGIN_NAME,
        "CategoryIcon": "imgs/category",
        "CodePath": "plugin.exe",
        "Description": PLUGIN_DESC,
        "Icon": "imgs/plugin",
        "Name": PLUGIN_NAME,
        "Version": PLUGIN_VERSION,
        "SDKVersion": 2,
        "OS": [{"Platform": "windows", "MinimumVersion": "10"}],
        "Software": {"MinimumVersion": "5.0"},
        "Profiles": [{
            "Name": "Fairground Online",
            "DeviceType": 2,  # Stream Deck XL = 2
            "DontAutoSwitchWhenInstalled": True,
            "ReadOnly": False,
        }],
    }
    return manifest


def generate_profile():
    """Generiert das eingebettete Profil (Profiles/Fairground Online.sdProfile/)."""
    profile_dir = os.path.join(SDPLUGIN_DIR, "Profiles", "Fairground Online.sdProfile")
    profiles_sub = os.path.join(profile_dir, "Profiles")
    os.makedirs(os.path.join(profile_dir, "Images"), exist_ok=True)
    os.makedirs(profiles_sub, exist_ok=True)

    page_guids = []
    for page_def in PAGES:
        page_guid = str(uuid_mod.uuid4())
        page_guids.append(page_guid)

        page_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=31)) + 'Z'
        page_dir = os.path.join(profiles_sub, page_id)
        os.makedirs(os.path.join(page_dir, "Images"), exist_ok=True)

        page_manifest = {
            "Controllers": [{
                "Actions": page_def["buttons"],
                "Type": "Keypad",
            }],
            "Icon": "",
            "Name": page_def["name"],
        }
        with open(os.path.join(page_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(page_manifest, f, ensure_ascii=False)

    profile_manifest = {
        "AppIdentifier": "",
        "Device": {
            "Model": DEVICE_MODEL,
            "UUID": DEVICE_UUID,
        },
        "Name": "Fairground Online",
        "Pages": {
            "Current": page_guids[0],
            "Default": page_guids[0],
            "Pages": page_guids,
        },
        "Version": "2.0",
    }
    with open(os.path.join(profile_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(profile_manifest, f, ensure_ascii=False)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# HAUPTPROGRAMM
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
if __name__ == "__main__":
    print("=== Fairground Online Stream Deck Plugin Builder ===\n")

    # ZUERST: Alle Tasten loslassen und Plugin-Prozess beenden
    # (verhindert Game-Crashes durch haengende Tasten beim Rebuild)
    import ctypes
    print("[0] Alle Tasten loslassen...")
    for sc in [0x2A, 0x36, 0x1D, 0x38, 0xE038, 0xE01D]:
        ext = 1 if sc > 0xFF else 0
        scan = sc & 0xFF
        ctypes.windll.user32.keybd_event(0, scan, 0x0008 | 0x0002 | ext, 0)
    # Alle Scan-Codes aus SCAN-Tabelle releasen
    for key_name, sc_val in SCAN.items():
        ext = 1 if key_name in EXTENDED_KEYS else 0
        ctypes.windll.user32.keybd_event(0, sc_val, 0x0008 | 0x0002 | ext, 0)
    import time
    time.sleep(0.2)
    # StreamDeck und Plugin beenden (Tasten sind bereits losgelassen)
    print("[0] StreamDeck und Plugin beenden...")
    subprocess.run(["taskkill", "/f", "/im", "StreamDeck.exe"], capture_output=True)
    subprocess.run(["taskkill", "/f", "/im", "plugin.exe"], capture_output=True)
    time.sleep(3)

    # AufrÃ¤umen
    if os.path.exists(SDPLUGIN_DIR):
        shutil.rmtree(SDPLUGIN_DIR)
    os.makedirs(SDPLUGIN_DIR, exist_ok=True)

    # 1) C# Quellcode generieren
    print("[1/6] C# Quellcode generieren...")
    cs_path = os.path.join(SDPLUGIN_DIR, "plugin.cs")
    with open(cs_path, "w", encoding="utf-8") as f:
        f.write(generate_cs())
    
    # Anzahl der Aktionen zaehlen
    total_actions = sum(len(a) for _, _, _, a in RIDES)
    print(f"      {total_actions} Aktionen definiert")

    # 2) Kompilieren
    print("[2/6] Kompilieren mit csc.exe...")
    exe_path = os.path.join(SDPLUGIN_DIR, "plugin.exe")
    result = subprocess.run(
        [CSC_PATH, f"/out:{exe_path}", "/target:exe",
         "/reference:System.dll", "/reference:System.Core.dll",
         cs_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("FEHLER bei Kompilierung:")
        print(result.stderr)
        print(result.stdout)
        exit(1)
    print(f"      plugin.exe erstellt ({os.path.getsize(exe_path)} Bytes)")

    # C# Source behalten (fuer Debugging)
    # os.remove(cs_path)

    # 3) manifest.json
    print("[3/6] manifest.json generieren...")
    manifest = generate_manifest()
    with open(os.path.join(SDPLUGIN_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"      {len(manifest['Actions'])} Aktionen im Manifest")

    # VERSION Datei schreiben
    with open(os.path.join(SDPLUGIN_DIR, "VERSION"), "w") as f:
        f.write(PLUGIN_VERSION)

    # 4) Icons erstellen
    print("[4/6] Icons erstellen...")
    imgs_dir = os.path.join(SDPLUGIN_DIR, "imgs")
    os.makedirs(imgs_dir, exist_ok=True)

    # Plugin-Icon + Kategorie-Icon aus Githubreadmybild.png
    from PIL import Image
    main_img_path = r"C:\Users\mrbla\Desktop\streamdeck_kirmes_icons_v2\Neuer Ordner\Githubreadmybild.png"
    if os.path.exists(main_img_path):
        img = Image.open(main_img_path)
        for name, size in [("plugin.png", 72), ("plugin@2x.png", 144)]:
            resized = img.resize((size, size), Image.LANCZOS)
            resized.save(os.path.join(imgs_dir, name))
        for name, size in [("category.png", 28), ("category@2x.png", 56)]:
            resized = img.resize((size, size), Image.LANCZOS)
            resized.save(os.path.join(imgs_dir, name))
    else:
        # Fallback: dunkelgruenes Quadrat
        for name, size in [("plugin.png", 72), ("plugin@2x.png", 144)]:
            with open(os.path.join(imgs_dir, name), "wb") as f:
                f.write(create_png(size, size, 30, 80, 60))
        for name, size in [("category.png", 28), ("category@2x.png", 56)]:
            with open(os.path.join(imgs_dir, name), "wb") as f:
                f.write(create_png(size, size, 30, 80, 60))

    # Action-Icon (fÃ¼r die Aktionsliste)
    for name, size in [("action.png", 20), ("action@2x.png", 40)]:
        with open(os.path.join(imgs_dir, name), "wb") as f:
            f.write(create_png(size, size, 50, 50, 50))

    # Key-Image (auf dem Button angezeigt)
    for name, size in [("key.png", 72), ("key@2x.png", 144)]:
        with open(os.path.join(imgs_dir, name), "wb") as f:
            f.write(create_png(size, size, 35, 35, 40))

    # Kategorie-Icons kopieren
    import shutil
    cat_icons_src = r"C:\Users\mrbla\Desktop\streamdeck_kirmes_icons_v2\Neuer Ordner"
    cat_dir = os.path.join(imgs_dir, "categories")
    os.makedirs(cat_dir, exist_ok=True)
    if os.path.exists(cat_icons_src):
        for png in os.listdir(cat_icons_src):
            if png.endswith(".png") and png != "Githubreadmybild.png":
                ride_id = png.replace(".png", "")
                shutil.copy2(os.path.join(cat_icons_src, png), os.path.join(cat_dir, f"{ride_id}.png"))

    # Per-Action Icons kopieren
    icons_src = r"C:\Users\mrbla\Desktop\streamdeck_kirmes_icons_v2"
    actions_dir = os.path.join(imgs_dir, "actions")
    icon_count = 0
    if os.path.exists(icons_src):
        for ride_dir in os.listdir(icons_src):
            ride_path = os.path.join(icons_src, ride_dir)
            if not os.path.isdir(ride_path):
                continue
            dest_dir = os.path.join(actions_dir, ride_dir)
            os.makedirs(dest_dir, exist_ok=True)
            for png in os.listdir(ride_path):
                if png.endswith(".png"):
                    shutil.copy2(os.path.join(ride_path, png), os.path.join(dest_dir, png))
                    icon_count += 1

    print(f"      8 Icon-Dateien + {icon_count} Action-Icons kopiert")

    # 5) Eingebettetes Profil
    print("[5/6] Eingebettetes Profil erstellen...")
    generate_profile()
    total_buttons = sum(len(p["buttons"]) for p in PAGES)
    print(f"      {len(PAGES)} Seiten, {total_buttons} Buttons")

    # 6) Als .streamDeckPlugin verpacken (ZIP)
    print("[6/6] Als .streamDeckPlugin verpacken...")
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SDPLUGIN_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                # Pfad relativ zum Elternverzeichnis (Plugin-Ordner einschliessen)
                arc_name = os.path.relpath(full_path, BASE_DIR)
                zf.write(full_path, arc_name)

    plugin_size = os.path.getsize(OUTPUT_FILE)

    # 7) Direkt in den installierten Plugin-Ordner kopieren
    installed_dir = os.path.join(
        os.environ["APPDATA"], "Elgato", "StreamDeck", "Plugins",
        f"{PLUGIN_ID}.sdPlugin"
    )
    if os.path.exists(installed_dir):
        print("[7/7] Direkt in installierten Plugin-Ordner kopieren...")
        # plugin.exe kopieren
        shutil.copy2(exe_path, os.path.join(installed_dir, "plugin.exe"))
        # manifest.json aktualisieren (DeviceType fix)
        shutil.copy2(
            os.path.join(SDPLUGIN_DIR, "manifest.json"),
            os.path.join(installed_dir, "manifest.json")
        )
        # Bilder kopieren (inkl. actions/ Unterordner)
        inst_imgs = os.path.join(installed_dir, "imgs")
        if os.path.exists(inst_imgs):
            shutil.rmtree(inst_imgs)
        shutil.copytree(imgs_dir, inst_imgs)
        # VERSION kopieren
        shutil.copy2(os.path.join(SDPLUGIN_DIR, "VERSION"), os.path.join(installed_dir, "VERSION"))
        print(f"      plugin.exe + manifest + imgs + VERSION kopiert nach {installed_dir}")
        # Stream Deck neustarten (Tasten wurden bereits am Anfang losgelassen)
        print("      Stream Deck wird neugestartet...")
        subprocess.run(["taskkill", "/f", "/im", "StreamDeck.exe"],
                       capture_output=True)
        time.sleep(2)
        sd_exe = os.path.join(
            os.environ["PROGRAMFILES"], "Elgato", "StreamDeck",
            "StreamDeck.exe"
        )
        if not os.path.exists(sd_exe):
            sd_exe = os.path.join(
                os.environ.get("PROGRAMFILES(X86)", ""),
                "Elgato", "StreamDeck", "StreamDeck.exe"
            )
        if os.path.exists(sd_exe):
            subprocess.Popen([sd_exe], close_fds=True)
            print(f"      Stream Deck gestartet!")
        else:
            print(f"      Stream Deck manuell starten!")
    else:
        print("[WARNUNG] Plugin noch nicht installiert!")
        print(f"          Doppelklick auf: {OUTPUT_FILE}")

    print(f"\n{'='*55}")
    print(f"FERTIG! Plugin erstellt:")
    print(f"  Datei: {OUTPUT_FILE}")
    print(f"  Groesse: {plugin_size:,} Bytes")
    print(f"  Aktionen: {total_actions}")
    print(f"  Seiten: {len(PAGES)}")
    print(f"  Buttons: {total_buttons}")
    print(f"\nInstallation:")
    print(f"  Doppelklick auf 'Fairground_Online.streamDeckPlugin'")
    print(f"  Stream Deck App installiert die Erweiterung automatisch!")
    print(f"{'='*55}")
