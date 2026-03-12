#!/usr/bin/env python3
"""
Erstellt ein Stream Deck Plugin (.streamDeckPlugin) für Fairground Online.
Das Plugin sendet Tastenkürzel (Scan-Codes) an das Spiel.

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

# === Konfiguration ===================================================
PLUGIN_ID = "com.blackmautz.fairground"
PLUGIN_NAME = "Fairground Online"
PLUGIN_AUTHOR = "BlackMautz"
PLUGIN_DESC = "Steuerung für Fairground Online Fahrgeschäfte"
PLUGIN_VERSION = "2.0.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SDPLUGIN_DIR = os.path.join(BASE_DIR, f"{PLUGIN_ID}.sdPlugin")
OUTPUT_FILE = os.path.join(BASE_DIR, "Fairground_Online.streamDeckPlugin")

CSC_PATH = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"



# === Scan Codes (AT-Tastatur, positionsbasiert) =======================
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

# === Fahrgeschaeft-Definitionen ======================================
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
        ("plattetippen", "Platte Tip", "v", True),
        ("kreuzspeeddown", "Kreuz -", "g", "repeat"),
        ("kreuzspeedup", "Kreuz +", "t", "repeat"),
        ("kreuz", "Kreuz", ("h", "j"), "toggle"),
        ("kreuztippen", "Kreuz Tip", "b", True),
        ("pktippen", "P+K Tip", None, "system"),
        ("gondelbremse", "Gondelbremse", "n", True),
        ("autoshow", "AUTO\\nSHOW", None, "autoshow"),
        ("autoshow_drive", "AUTO\\nDRIVE", None, "autoshow"),
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
        ("parkcar1", "Park Gondel 1", "g", False),
        ("parkcar2", "Park Gondel 2", "b", False),
        ("autoshow", "AUTO\\nSHOW", None, "autoshow_turaka"),
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
    ("timer", "Timer", (180, 80, 80), [
        ("startstop", "Timer", None, "system"),
    ]),
    ("settings", "Settings", (60, 60, 60), [
        ("menu", "Menue", "escape", False),
        ("speedup", "Speed Hoch", "rightArrow", False),
        ("speeddown", "Speed Runter", "leftArrow", False),
        ("repeatspeed", "Repeat Speed", None, "system"),
        ("showtitle", "Schrift AN/AUS", None, "system"),
        ("s2l", "Sound2Light", None, "system"),
        ("s2l_licht", "S2L Licht", None, "system"),
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

# Hilfsfunktionen
# =====================================================================

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
    """Generiert C# Dictionary-Einträge für alle Aktionen."""
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
            elif mode in ("system", "autoshow", "autoshow_turaka"):
                pass
            else:
                scan = SCAN[key_data]
                ext = key_data in EXTENDED_KEYS
                flags = 8 | (1 if ext else 0)
                hold = "true" if mode else "false"
                lines.append(f'        km["{uuid}"]=new KI{{s=0x{scan:02X},f={flags},h={hold}}};')
    return '\n'.join(lines)


def generate_title_entries():
    """Generiert C# Dictionary-Einträge für Button-Titel aus RIDES."""
    lines = []
    for ride_id, ride_name, _, actions in RIDES:
        for action in actions:
            action_id, label, _, mode = action
            uuid = f"{PLUGIN_ID}.{ride_id}.{action_id}"
            safe_label = label.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            lines.append(f'        tm["{uuid}"]="{safe_label}";')
    return '\n'.join(lines)


def generate_cs():
    """Generiert den C# Quellcode für das Plugin."""
    map_entries = generate_map_entries()
    title_entries = generate_title_entries()
    return f'''using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Net;
using System.Net.WebSockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

class P
{{
    [DllImport("user32.dll", EntryPoint = "keybd_event")]
    static extern void keybd_event_raw(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

    static void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo)
    {{
        try
        {{
            string dir = (dwFlags & 2u) != 0 ? "UP" : "DOWN";
            Log("TRACE KEY " + dir + " vk=0x" + bVk.ToString("X2") + " scan=0x" + bScan.ToString("X2") + "(" + ScanName(bScan) + ") flags=" + dwFlags + " driveOnly=" + autoShowDriveOnly + " running=" + showRunning);
        }}
        catch {{ }}
        keybd_event_raw(bVk, bScan, dwFlags, dwExtraInfo);
    }}

    [DllImport("ole32.dll")]
    static extern int CoCreateInstance(ref Guid clsid, IntPtr outer, uint ctx, ref Guid iid, out IntPtr obj);

    [DllImport("ole32.dll")]
    static extern int CoInitializeEx(IntPtr reserved, uint flags);

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
    static readonly object wsSendLock = new object();
    static string logPath;
    static string s2lSettingsPath;
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

    // Timer
    static int timerDuration = 180; // Startdauer in Sekunden (3 Min)
    static int timerRemaining = 180;
    static bool timerRunning = false;
    static bool timerPaused = false;
    static string timerCtx = null;
    static Thread timerThread = null;
    static int timerGen = 0;
    static DateTime timerKeyDown = DateTime.MinValue;

    // AutoShow
    static bool showRunning = false;
    static int showGen = 0;
    static string showCtx = null;
    static string showCtxDrive = null;
    static bool autoShowDriveOnly = false;
    static DateTime showKeyDown = DateTime.MinValue;
    static Thread showThread = null;
    static int selectedTour = 0;
    static bool nightMode = false;
    static bool autoLoop = false;
    static int loopPause = 60;
    static string showPhaseText = "";
    static int showCountdownSec = 330;
    static string showCtxTK = null;
    static int lastRandomBD = -1;
    static int lastRandomMD = -1;
    static int drivePlatteEst = 0;
    static int driveKreuzEst = 0;
    const int driveMinEst = 8;
    const int driveMaxEst = 24;
    const int driveSoftMinEst = 14;
    const int driveSoftMaxEst = 23;
    const int driveAxisGapEst = 8;
    static DateTime driveNextDynamicPulse = DateTime.MinValue;
    static DateTime driveLastBrake = DateTime.MinValue;
    static bool driveAutoStopping = false;
    static bool driveDynamicPulseEnabled = false;
    static int drivePartyMin = 14;   // aktiver Floor im Drive-Modus (58%=14/24)
    static int drivePartyGap = 8;    // aktiver Gap-Limit; Schraege: 20
    static readonly string telemetryDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "AppData", "LocalLow", "CoasterGalaxyWorld", "Fairground Online");
    static readonly string breakdanceStatePath = Path.Combine(telemetryDir, "breakdance_state.csv");
    static DateTime driveTelemetryLastRead = DateTime.MinValue;
    static DateTime driveTelemetryLastWrite = DateTime.MinValue;
    static bool driveTelemetryAvailable = false;
    static float driveRealPlate = 0f;
    static float driveRealCross = 0f;
    static bool driveRealPlateOn = false;
    static bool driveRealCrossOn = false;
    static bool driveRealBrakeOn = false;
    static bool driveRealEStop = false;

    // Sound2Light
    static bool s2lRunning = false;
    static int s2lGen = 0;
    static string s2lCtx = null;
    static Thread s2lThread = null;
    static int s2lMode = 0;  // 0=Alles (Fahrt+Licht), 1=Nur Licht (keine Fahrt-Steuerung!)
    static string s2lLichtCtx = null;  // Context für S2L Licht Button

    // P+K Tip Toggle
    static bool pkTipActive = false;  // Platte+Kreuz Tip gleichzeitig gehalten?
    static bool pkTipWasActive = false; // War P+K Tip vor der Fahrt an? (fuer Restore)
    static string pkTipCtx = null;    // Context des P+K Tip Buttons (fuer Auto-Update)
    static int s2lSensitivity = 50;   // 0-100
    static int s2lPresetLow = 1;      // Preset bei leiser Musik
    static int s2lPresetHigh = 9;     // Preset bei lauter Musik (MAX)
    static bool s2lStrobo = true;     // Strobo-Effekt bei Peaks
    static bool s2lFog = true;        // Nebel bei Musik
    static bool s2lFlame = true;      // Flamme bei Bass-Peaks
    static bool s2lLED = true;        // LED-Strobo (0x0C)
    static bool s2lLight1 = true;     // Gondel Rückwand (Taste 1)
    static bool s2lLight2 = true;     // Kasse Logo (Taste 2)
    static bool s2lLight3 = true;     // Front (Taste 3)
    static bool s2lLight4 = true;     // (Taste 4)
    static bool s2lLight5 = true;     // (Taste 5)
    static bool s2lLight6 = true;     // (Taste 6)
    static bool s2lLight7 = true;     // (Taste 7)
    static bool s2lLight8 = true;     // (Taste 8)
    static bool s2lLight9 = true;     // (Taste 9)
    static bool s2lColorStrobe = true;  // Farbstroboskop
    static bool s2lSpot = true;       // Spot-Effekte
    static bool s2lAllEffects = true; // Master "Alles AN" Toggle
    static bool s2lNightMode = false; // Nacht-Modus (Effekte seltener)
    static bool s2lLoop = false;      // Endlos-Schleife
    static bool s2lKreuzMotorPauseEnabled = false;  // Automatische Gondel-Pausen während Fahrt
    static int s2lLoopPause = 60;     // Pause zwischen Loops (Sekunden)
    static int s2lDuration = 180;     // Show-Dauer in Sekunden (3 Minuten)
    static DateTime s2lShowStart = DateTime.MinValue;
    static int s2lNumFahrten = 0;      // Anzahl Fahrten (0=Deaktiviert, 1-5=aktiviert)
    static int s2lCurrentFahrt = 1;    // Aktuelle Fahrt (1-5)
    static int s2lPauseDuration = 60;  // Pause zwischen Fahrten in Sekunden
    static bool s2lInPause = false;    // Gerade in Pause?
    static DateTime s2lPauseStart = DateTime.MinValue;
    static int s2lLastPreset = -1;
    static DateTime s2lLastRandomPreset = DateTime.MinValue;  // Cooldown für Zufalls-Preset
    static int s2lPresetSurpriseCount = 0;  // Zählt Frames bis zurück zum Energy-Preset
    static DateTime s2lLastStrobo = DateTime.MinValue;
    static DateTime s2lLastLEDStrobe = DateTime.MinValue;
    static DateTime s2lLastNebel = DateTime.MinValue;
    static DateTime s2lLastFlamme = DateTime.MinValue;
    static DateTime s2lLastBubble = DateTime.MinValue;
    static DateTime s2lLastPresetChange = DateTime.MinValue;
    static DateTime s2lLastSpotColor = DateTime.MinValue;
    static DateTime s2lLastFarbstrob = DateTime.MinValue;
    static DateTime s2lLastFX = DateTime.MinValue;
    static DateTime s2lLastGobo = DateTime.MinValue;
    static DateTime s2lLastSpeedChange = DateTime.MinValue;
    static DateTime s2lLastDeckTitleUpdate = DateTime.MinValue;
    static DateTime s2lNextKreuzMotorPause = DateTime.MinValue;  // Nächste geplante Gondel-Pause
    static DateTime s2lKreuzMotorPausedUntil = DateTime.MinValue;  // Wie lange Motor pausiert
    static bool s2lGondelPauseLogged = false;  // Verhindert Log-Spam während Gondel-Pause
    static Random s2lRandom = new Random();  // Globaler Random Generator (WICHTIG: nicht neu erzeugen!)
    static float s2lSmoothedBass = 0f;
    static float s2lSmoothedMid = 0f;
    static float s2lSmoothedHigh = 0f;
    static int s2lFrameCount = 0;     // Counter für Status-Logging
    static float s2lSmoothedEnergy = 0f;
    static float s2lPeakEnergy = 0.001f;
    static float s2lAvgPeak = 0.5f;    // Durchschnitt der Peak-Energies (für adaptive Schwellen)
    static float s2lAvgBass = 0.5f;    // Durchschnitt der Bass-Frequenzen
    static float s2lAvgMid = 0.5f;     // Durchschnitt der Mid-Frequenzen
    static float s2lAvgHigh = 0.5f;    // Durchschnitt der High-Frequenzen
    static float s2lAvgEnergy = 0.5f;  // Durchschnitt der Gesamt-Energie
    static Queue<float> s2lPeakHistory = new Queue<float>(); // Letzte 100 Peaks für Durchschnitt
    static Queue<float> s2lBassHistory = new Queue<float>(); // Letzte 100 Bass-Werte
    static Queue<float> s2lMidHistory = new Queue<float>();  // Letzte 100 Mid-Werte
    static Queue<float> s2lHighHistory = new Queue<float>(); // Letzte 100 High-Werte
    static Queue<float> s2lEnergyHistory = new Queue<float>(); // Letzte 100 Energy-Werte
    
    // === DELTA-TRACKING für transient-basierte Effekte ===
    static float s2lLastBass = 0f, s2lLastMid = 0f, s2lLastHigh = 0f, s2lLastEnergy = 0f;
    static float s2lDeltaBass = 0f, s2lDeltaMid = 0f, s2lDeltaHigh = 0f, s2lDeltaEnergy = 0f;

    // === SONG-WECHSEL ERKENNUNG ===
    // Erkennt Stille zwischen Songs und resettet Averages damit lautere/leisere Songs nicht falsch triggern
    static int s2lSilenceFrames = 0;     // Zählt aufeinanderfolgende stille Frames
    static bool s2lSongTransition = false;  // Sind wir gerade in einem Songwechsel?
    static int s2lTransitionFrames = 0;    // Frames nach Songwechsel (für schnellen Avg-Aufbau)

    // === SONG-STIMMUNG (Chill vs Party) ===
    // Langzeitdurchschnitt (~500 Frames = ~25s) erkennt ob Song entspannt oder heavy ist
    static Queue<float> s2lLongBassHistory = new Queue<float>();   // Lange Bass-History (500 Frames)
    static Queue<float> s2lLongEnergyHistory = new Queue<float>(); // Lange Energy-History (500 Frames)
    static float s2lLongAvgBass = 0f;     // 25s Bass-Durchschnitt
    static float s2lLongAvgEnergy = 0f;   // 25s Energy-Durchschnitt
    static int s2lMood = 1;  // 0=Chill, 1=Normal, 2=Party/Heavy
    static DateTime s2lLastMoodLog = DateTime.MinValue;

    // === AUTOSHOW-FEATURES FÜR S2L ===
    // Schrägfahrt: Eine Seite bremst ab während andere weiterfährt (wie im AutoShow!)
    static bool s2lSchraegActive = false;     // Gerade in Schrägfahrt?
    static DateTime s2lLastSchraeg = DateTime.MinValue;  // Cooldown
    // Gondelbremse: Physische Bremse (0x31) für Drama
    static DateTime s2lLastGondelbremse = DateTime.MinValue;
    // ALLES AN: Strobo+Nebel+Flamme gleichzeitig (Mega-Moment!)
    static DateTime s2lLastAllesAn = DateTime.MinValue;
    // Doppel-Flamme: Zwei schnelle Flammen hintereinander
    static DateTime s2lLastDoppelFlamme = DateTime.MinValue;
    // MH Programm + Farbe: Visuelle Abwechslung (wie im AutoShow)
    static DateTime s2lLastMHProgramm = DateTime.MinValue;
    static DateTime s2lLastMHFarbe = DateTime.MinValue;
    // MH ColorStrobe (Shift+V) + Scheinwerfer (Shift+Q)
    static DateTime s2lLastMHColorStrobe = DateTime.MinValue;
    static DateTime s2lLastScheinwerfer = DateTime.MinValue;
    // Spot AN/AUS Toggle (Shift+Q) - dramatischer Blackout/Flash
    static DateTime s2lLastSpotToggle = DateTime.MinValue;
    static bool s2lSpotsOn = true;  // Spots an nach Start
    // MH Light Sync (Shift+C) - gelegentlich aktivieren
    static DateTime s2lLastLightSync = DateTime.MinValue;
    // LED-Welleneffekt: Cycling statt alle gleichzeitig
    static int s2lLedPattern = 0;  // 0=alle, 1=ungerade(1,3,5,7,9), 2=gerade(2,4,6,8), 3=chase
    // Speed-Tracking als Klassenebene (für Schrägfahrt-Thread)
    static int s2lPlattePos = 4;
    static int s2lKreuzPos = 20;
    static int s2lSpeedLevel = 24;

    static void Log(string msg)
    {{
        try {{ File.AppendAllText(logPath, DateTime.Now.ToString("HH:mm:ss.fff") + " " + msg + "\\n"); }}
        catch {{ }}
    }}

    static void SaveS2LSettings()
    {{
        try {{
            var settings = new string[] {{
                "sensitivity=" + s2lSensitivity.ToString(),
                "presetlow=" + s2lPresetLow.ToString(),
                "presethigh=" + s2lPresetHigh.ToString(),
                "strobo=" + (s2lStrobo ? "true" : "false"),
                "fog=" + (s2lFog ? "true" : "false"),
                "flame=" + (s2lFlame ? "true" : "false"),
                "led=" + (s2lLED ? "true" : "false"),
                "light1=" + (s2lLight1 ? "true" : "false"),
                "light2=" + (s2lLight2 ? "true" : "false"),
                "light3=" + (s2lLight3 ? "true" : "false"),
                "light4=" + (s2lLight4 ? "true" : "false"),
                "light5=" + (s2lLight5 ? "true" : "false"),
                "light6=" + (s2lLight6 ? "true" : "false"),
                "light7=" + (s2lLight7 ? "true" : "false"),
                "light8=" + (s2lLight8 ? "true" : "false"),
                "light9=" + (s2lLight9 ? "true" : "false"),
                "colorstrobe=" + (s2lColorStrobe ? "true" : "false"),
                "spot=" + (s2lSpot ? "true" : "false"),
                "alles=" + (s2lAllEffects ? "true" : "false"),
                "night=" + (s2lNightMode ? "true" : "false"),
                "loop=" + (s2lLoop ? "true" : "false"),
                "gondelpause=" + (s2lKreuzMotorPauseEnabled ? "true" : "false"),
                "pause=" + s2lLoopPause.ToString(),
                "duration=" + s2lDuration.ToString(),
                "numfahrten=" + s2lNumFahrten.ToString(),
                "pauseduration=" + s2lPauseDuration.ToString()
            }};
            File.WriteAllLines(s2lSettingsPath, settings);
            Log("S2L Settings saved: duration=" + s2lDuration);
        }}
        catch (Exception ex) {{ Log("ERROR SaveS2LSettings: " + ex.Message); }}
    }}

    static void LoadS2LSettings()
    {{
        try {{
            if (!File.Exists(s2lSettingsPath)) {{ Log("S2L Settings file not found, using defaults"); return; }}
            var lines = File.ReadAllLines(s2lSettingsPath);
            foreach (var line in lines) {{
                var parts = line.Split('=');
                if (parts.Length != 2) continue;
                string key = parts[0].Trim();
                string val = parts[1].Trim();
                if (key == "sensitivity") {{ int si; if (int.TryParse(val, out si) && si >= 0 && si <= 100) s2lSensitivity = si; }}
                else if (key == "presetlow") {{ int pi; if (int.TryParse(val, out pi) && pi >= 1 && pi <= 9) s2lPresetLow = pi; }}
                else if (key == "presethigh") {{ int pi; if (int.TryParse(val, out pi) && pi >= 1 && pi <= 9) s2lPresetHigh = pi; }}
                else if (key == "strobo") s2lStrobo = val == "true";
                else if (key == "fog") s2lFog = val == "true";
                else if (key == "flame") s2lFlame = val == "true";
                else if (key == "led") s2lLED = val == "true";
                else if (key == "light1") s2lLight1 = val == "true";
                else if (key == "light2") s2lLight2 = val == "true";
                else if (key == "light3") s2lLight3 = val == "true";
                else if (key == "light4") s2lLight4 = val == "true";
                else if (key == "light5") s2lLight5 = val == "true";
                else if (key == "light6") s2lLight6 = val == "true";
                else if (key == "light7") s2lLight7 = val == "true";
                else if (key == "light8") s2lLight8 = val == "true";
                else if (key == "light9") s2lLight9 = val == "true";
                else if (key == "colorstrobe") s2lColorStrobe = val == "true";
                else if (key == "spot") s2lSpot = val == "true";
                else if (key == "alles") s2lAllEffects = val == "true";
                else if (key == "night") s2lNightMode = val == "true";
                else if (key == "loop") s2lLoop = val == "true";
                else if (key == "gondelpause") s2lKreuzMotorPauseEnabled = val == "true";
                else if (key == "pause") {{ int ps; if (int.TryParse(val, out ps) && ps >= 10 && ps <= 300) s2lLoopPause = ps; }}
                else if (key == "duration") {{ int di; if (int.TryParse(val, out di) && di >= 0 && di <= 3600) s2lDuration = di; }}
                else if (key == "numfahrten") {{ int nf; if (int.TryParse(val, out nf) && nf >= 0 && nf <= 5) s2lNumFahrten = nf; }}
                else if (key == "pauseduration") {{ int pd; if (int.TryParse(val, out pd) && pd >= 30 && pd <= 300) s2lPauseDuration = pd; }}
            }}
            Log("S2L Settings loaded: duration=" + s2lDuration + "s");
        }}
        catch (Exception ex) {{ Log("ERROR LoadS2LSettings: " + ex.Message); }}
    }}

    static int Main(string[] args)
    {{
        try
        {{
            logPath = Path.Combine(Path.GetDirectoryName(
                System.Reflection.Assembly.GetExecutingAssembly().Location),
                "plugin.log");
            s2lSettingsPath = Path.Combine(Path.GetDirectoryName(
                System.Reflection.Assembly.GetExecutingAssembly().Location),
                "s2l_settings.json");
            LoadS2LSettings();
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

    static void SetSettings(string context, Dictionary<string, string> settings)
    {{
        if (context == null || settings == null) return;
        var settingsObj = new System.Text.StringBuilder();
        settingsObj.Append("{{");
        bool first = true;
        foreach (var kv in settings) {{
            if (!first) settingsObj.Append(",");
            settingsObj.Append("\\"" + kv.Key + "\\":\\"" + kv.Value + "\\"");
            first = false;
        }}
        settingsObj.Append("}}");
        var msg = "{{\\"event\\":\\"setSettings\\",\\"context\\":\\"" + context + "\\",\\"payload\\":{{\\"settings\\":" + settingsObj.ToString() + "}}}}";
        Send(msg);
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
            if (ws == null || ws.State != WebSocketState.Open) return;
            lock (wsSendLock)
            {{
                if (ws == null || ws.State != WebSocketState.Open) return;
                var bytes = Encoding.UTF8.GetBytes(msg);
                ws.SendAsync(new ArraySegment<byte>(bytes),
                    WebSocketMessageType.Text, true, CancellationToken.None)
                    .GetAwaiter().GetResult();
            }}
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
            else if (action == "{PLUGIN_ID}.timer.startstop")
            {{
                timerCtx = context;
                SetImg(context, false);
                string dv = V(j, "duration");
                if (dv != null) {{ int pd; if (int.TryParse(dv, out pd) && pd >= 10) {{ timerDuration = pd; if (!timerRunning) timerRemaining = pd; }} }}
                SetTtl(context, TFmt());
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
            else if (action == "{PLUGIN_ID}.settings.s2l_licht")
            {{
                s2lLichtCtx = context;
                SetImg(context, s2lRunning && s2lMode == 1);
                SetTtl(context, (s2lRunning && s2lMode == 1) ? "S2L\u266bLicht\\n[ AN ]" : "S2L\u266bLicht\\n[ AUS ]");
                SetSettings(context, new Dictionary<string, string> {{
                    {{ "sensitivity", s2lSensitivity.ToString() }},
                    {{ "presetlow", s2lPresetLow.ToString() }},
                    {{ "presethigh", s2lPresetHigh.ToString() }},
                    {{ "strobo", s2lStrobo ? "true" : "false" }},
                    {{ "fog", s2lFog ? "true" : "false" }},
                    {{ "flame", s2lFlame ? "true" : "false" }},
                    {{ "led", s2lLED ? "true" : "false" }},
                    {{ "light1", s2lLight1 ? "true" : "false" }},
                    {{ "light2", s2lLight2 ? "true" : "false" }},
                    {{ "light3", s2lLight3 ? "true" : "false" }},
                    {{ "light4", s2lLight4 ? "true" : "false" }},
                    {{ "light5", s2lLight5 ? "true" : "false" }},
                    {{ "light6", s2lLight6 ? "true" : "false" }},
                    {{ "light7", s2lLight7 ? "true" : "false" }},
                    {{ "light8", s2lLight8 ? "true" : "false" }},
                    {{ "light9", s2lLight9 ? "true" : "false" }},
                    {{ "colorstrobe", s2lColorStrobe ? "true" : "false" }},
                    {{ "spot", s2lSpot ? "true" : "false" }},
                    {{ "alles", s2lAllEffects ? "true" : "false" }},
                    {{ "night", s2lNightMode ? "true" : "false" }},
                    {{ "loop", s2lLoop ? "true" : "false" }},
                    {{ "pause", s2lLoopPause.ToString() }},
                    {{ "duration", s2lDuration.ToString() }},
                    {{ "numfahrten", s2lNumFahrten.ToString() }},
                    {{ "pauseduration", s2lPauseDuration.ToString() }}
                }});
                Log("S2L LICHT willAppear: Synced PI with loaded settings (duration=" + s2lDuration + "s)");
            }}
            else if (action == "{PLUGIN_ID}.settings.s2l")
            {{
                s2lCtx = context;
                SetImg(context, s2lRunning);
                SetTtl(context, s2lRunning ? "S2L\\n[ AN ]" : "S2L\\n[ AUS ]");
                // Keine Werte aus j lesen! Die s2lXXX Variablen sind bereits von LoadS2LSettings() gesetzt
                // Stattdessen: PI mit den geladenen Settings synchen
                SetSettings(context, new Dictionary<string, string> {{
                    {{ "sensitivity", s2lSensitivity.ToString() }},
                    {{ "presetlow", s2lPresetLow.ToString() }},
                    {{ "presethigh", s2lPresetHigh.ToString() }},
                    {{ "strobo", s2lStrobo ? "true" : "false" }},
                    {{ "fog", s2lFog ? "true" : "false" }},
                    {{ "flame", s2lFlame ? "true" : "false" }},
                    {{ "led", s2lLED ? "true" : "false" }},
                    {{ "light1", s2lLight1 ? "true" : "false" }},
                    {{ "light2", s2lLight2 ? "true" : "false" }},
                    {{ "light3", s2lLight3 ? "true" : "false" }},
                    {{ "light4", s2lLight4 ? "true" : "false" }},
                    {{ "light5", s2lLight5 ? "true" : "false" }},
                    {{ "light6", s2lLight6 ? "true" : "false" }},
                    {{ "light7", s2lLight7 ? "true" : "false" }},
                    {{ "light8", s2lLight8 ? "true" : "false" }},
                    {{ "light9", s2lLight9 ? "true" : "false" }},
                    {{ "colorstrobe", s2lColorStrobe ? "true" : "false" }},
                    {{ "spot", s2lSpot ? "true" : "false" }},
                    {{ "alles", s2lAllEffects ? "true" : "false" }},
                    {{ "night", s2lNightMode ? "true" : "false" }},
                    {{ "loop", s2lLoop ? "true" : "false" }},
                    {{ "pause", s2lLoopPause.ToString() }},
                    {{ "duration", s2lDuration.ToString() }},
                    {{ "numfahrten", s2lNumFahrten.ToString() }},
                    {{ "pauseduration", s2lPauseDuration.ToString() }}
                }});
                Log("S2L willAppear: Synced PI with loaded settings (duration=" + s2lDuration + "s)");
            }}
            else if (action == "{PLUGIN_ID}.breakdance.pktippen")
            {{
                pkTipCtx = context;
                SetImg(context, pkTipActive);
                SetTtl(context, pkTipActive ? "P+K Tip\\n[ AN ]" : "P+K Tip\\n[ AUS ]");
            }}
            else if (action == "{PLUGIN_ID}.breakdance.autoshow")
            {{
                showCtx = context;
                SetImg(context, false);
                string tv2 = V(j, "tour");
                if (tv2 != null) {{ int pt2; if (int.TryParse(tv2, out pt2) && pt2 >= 0 && pt2 <= 9) selectedTour = pt2; }}
                string nm2 = V(j, "night");
                if (nm2 != null) nightMode = nm2 == "true";
                string lp2 = V(j, "loop");
                if (lp2 != null) autoLoop = lp2 == "true";
                string pp2 = V(j, "pause");
                if (pp2 != null) {{ int ppv; if (int.TryParse(pp2, out ppv) && ppv >= 5) loopPause = ppv; }}
                SetTtl(context, showRunning ? "LAEUFT..." : "AUTO\\nSHOW");
            }}
            else if (action == "{PLUGIN_ID}.breakdance.autoshow_drive")
            {{
                showCtxDrive = context;
                SetImg(context, showRunning && autoShowDriveOnly);
                string tv2 = V(j, "tour");
                if (tv2 != null) {{ int pt2; if (int.TryParse(tv2, out pt2) && pt2 >= 0 && pt2 <= 9) selectedTour = pt2; }}
                string nm2 = V(j, "night");
                if (nm2 != null) nightMode = nm2 == "true";
                string lp2 = V(j, "loop");
                if (lp2 != null) autoLoop = lp2 == "true";
                string pp2 = V(j, "pause");
                if (pp2 != null) {{ int ppv; if (int.TryParse(pp2, out ppv) && ppv >= 5) loopPause = ppv; }}
                SetTtl(context, (showRunning && autoShowDriveOnly) ? "LAEUFT..." : "AUTO\\nDRIVE");
            }}
            else if (action == "{PLUGIN_ID}.turaka.autoshow")
            {{
                showCtxTK = context;
                SetImg(context, false);
                string tv2 = V(j, "tour");
                if (tv2 != null) {{ int pt2; if (int.TryParse(tv2, out pt2) && pt2 >= 0 && pt2 <= 9) selectedTour = pt2; }}
                string nm2 = V(j, "night");
                if (nm2 != null) nightMode = nm2 == "true";
                string lp2 = V(j, "loop");
                if (lp2 != null) autoLoop = lp2 == "true";
                string pp2 = V(j, "pause");
                if (pp2 != null) {{ int ppv; if (int.TryParse(pp2, out ppv) && ppv >= 5) loopPause = ppv; }}
                SetTtl(context, showRunning ? "LAEUFT..." : "AUTO\\nSHOW");
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
        else if (ev == "keyDown" && (action == "{PLUGIN_ID}.settings.s2l" || action == "{PLUGIN_ID}.settings.s2l_licht") && context != null)
        {{
            bool isLichtMode = action.Contains("s2l_licht");
            if (isLichtMode) s2lLichtCtx = context;
            else s2lCtx = context;
            
            if (s2lRunning)
            {{
                s2lGen++;
                s2lRunning = false;  // SOFORT auf false setzen damit Button wieder gedrückt werden kann
                Log("S2L: Stopp angefordert (Mode=" + s2lMode + ")");
                // Safety releases fuer gehaltene Effekte
                keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo
                keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel
                keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse
                keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo
                keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero); // Flamme
                SetImg(context, false);
                if (isLichtMode) SetTtl(context, "S2L\u266bLicht\\n[ AUS ]");
                else SetTtl(context, "S2L\\n[ AUS ]");
                // Anderen Button auch AUS setzen
                if (s2lCtx != null) {{ SetImg(s2lCtx, false); SetTtl(s2lCtx, "S2L\\n[ AUS ]"); }}
                if (s2lLichtCtx != null) {{ SetImg(s2lLichtCtx, false); SetTtl(s2lLichtCtx, "S2L\u266bLicht\\n[ AUS ]"); }}
            }}
            else
            {{
                s2lMode = isLichtMode ? 1 : 0;  // 0=Alles, 1=Nur Licht
                s2lRunning = true;
                int gen = ++s2lGen;
                SetImg(context, true);
                if (isLichtMode) SetTtl(context, "S2L\u266bLicht\\nStart...");
                else SetTtl(context, "S2L\\nStart...");
                s2lSmoothedBass = 0; s2lSmoothedMid = 0; s2lSmoothedHigh = 0;
                s2lSmoothedEnergy = 0; s2lPeakEnergy = 0.001f; s2lLastPreset = -1;
                s2lPeakHistory.Clear(); s2lBassHistory.Clear(); s2lMidHistory.Clear(); s2lHighHistory.Clear(); s2lEnergyHistory.Clear();
                s2lAvgPeak = 0.5f; s2lAvgBass = 0.5f; s2lAvgMid = 0.5f; s2lAvgHigh = 0.5f; s2lAvgEnergy = 0.5f;
                s2lFrameCount = 0;
                s2lLastBass = 0; s2lLastMid = 0; s2lLastHigh = 0; s2lLastEnergy = 0;
                s2lThread = new Thread(() => S2LRun(gen));
                s2lThread.IsBackground = true;
                s2lThread.Start();
                Log("S2L: Eingeschaltet (Mode=" + s2lMode + " " + (isLichtMode ? "NUR LICHT" : "ALLES") + ")");
            }}
        }}
        else if (ev == "didReceiveSettings" && (action == "{PLUGIN_ID}.settings.s2l" || action == "{PLUGIN_ID}.settings.s2l_licht"))
        {{
            string sv = V(j, "sensitivity");
            if (sv != null) {{ int si; if (int.TryParse(sv, out si) && si >= 0 && si <= 100) {{ s2lSensitivity = si; Log("S2L Sensitivity: " + si); }} }}
            string pl = V(j, "presetlow");
            if (pl != null) {{ int pi; if (int.TryParse(pl, out pi) && pi >= 1 && pi <= 9) {{ s2lPresetLow = pi; Log("S2L Preset Low: " + pi); }} }}
            string ph = V(j, "presethigh");
            if (ph != null) {{ int pi; if (int.TryParse(ph, out pi) && pi >= 1 && pi <= 9) {{ s2lPresetHigh = pi; Log("S2L Preset High: " + pi); }} }}
            string st = V(j, "strobo");
            if (st != null) {{ s2lStrobo = st == "true"; Log("S2L Strobo: " + s2lStrobo); }}
            string fg = V(j, "fog");
            if (fg != null) {{ s2lFog = fg == "true"; Log("S2L Fog: " + s2lFog); }}
            string fl = V(j, "flame");
            if (fl != null) {{ s2lFlame = fl == "true"; Log("S2L Flame: " + s2lFlame); }}
            string ld = V(j, "led");
            if (ld != null) {{ s2lLED = ld == "true"; Log("S2L LED: " + s2lLED); }}
            string l1 = V(j, "light1");
            if (l1 != null) {{ s2lLight1 = l1 == "true"; Log("S2L Light1: " + s2lLight1); }}
            string l2 = V(j, "light2");
            if (l2 != null) {{ s2lLight2 = l2 == "true"; Log("S2L Light2: " + s2lLight2); }}
            string l3 = V(j, "light3");
            if (l3 != null) {{ s2lLight3 = l3 == "true"; Log("S2L Light3: " + s2lLight3); }}
            string l4 = V(j, "light4");
            if (l4 != null) {{ s2lLight4 = l4 == "true"; Log("S2L Light4: " + s2lLight4); }}
            string l5 = V(j, "light5");
            if (l5 != null) {{ s2lLight5 = l5 == "true"; Log("S2L Light5: " + s2lLight5); }}
            string l6 = V(j, "light6");
            if (l6 != null) {{ s2lLight6 = l6 == "true"; Log("S2L Light6: " + s2lLight6); }}
            string l7 = V(j, "light7");
            if (l7 != null) {{ s2lLight7 = l7 == "true"; Log("S2L Light7: " + s2lLight7); }}
            string l8 = V(j, "light8");
            if (l8 != null) {{ s2lLight8 = l8 == "true"; Log("S2L Light8: " + s2lLight8); }}
            string l9 = V(j, "light9");
            if (l9 != null) {{ s2lLight9 = l9 == "true"; Log("S2L Light9: " + s2lLight9); }}
            string cs = V(j, "colorstrobe");
            if (cs != null) {{ s2lColorStrobe = cs == "true"; Log("S2L ColorStrobe: " + s2lColorStrobe); }}
            string sp = V(j, "spot");
            if (sp != null) {{ s2lSpot = sp == "true"; Log("S2L Spot: " + s2lSpot); }}
            string al = V(j, "alles");
            if (al != null) {{ s2lAllEffects = al == "true"; Log("S2L All Effects: " + s2lAllEffects); }}
            string nv = V(j, "night");
            if (nv != null) {{ s2lNightMode = nv == "true"; Log("S2L Night: " + s2lNightMode); }}
            string lv = V(j, "loop");
            if (lv != null) {{ s2lLoop = lv == "true"; Log("S2L Loop: " + s2lLoop); }}
            string gp = V(j, "gondelpause");
            if (gp != null) {{ s2lKreuzMotorPauseEnabled = gp == "true"; Log("S2L Gondel-Pausen: " + s2lKreuzMotorPauseEnabled); }}
            string ps = V(j, "pause");
            if (ps != null) {{ int pi; if (int.TryParse(ps, out pi) && pi >= 10 && pi <= 300) {{ s2lLoopPause = pi; Log("S2L Pause: " + pi); }} }}
            string dr = V(j, "duration");
            if (dr != null) {{ int di; if (int.TryParse(dr, out di) && di >= 0 && di <= 3600) {{ s2lDuration = di; Log("S2L Duration: " + di + "s"); }} }}
            string nf = V(j, "numfahrten");
            if (nf != null) {{ int ni; if (int.TryParse(nf, out ni) && ni >= 0 && ni <= 5) {{ s2lNumFahrten = ni; Log("S2L Num Fahrten: " + ni); }} }}
            string pd = V(j, "pauseduration");
            if (pd != null) {{ int pi; if (int.TryParse(pd, out pi) && pi >= 30 && pi <= 300) {{ s2lPauseDuration = pi; Log("S2L Pause Duration: " + pi); }} }}
            SaveS2LSettings();
        }}
        else if (ev == "didReceiveSettings" && action == "{PLUGIN_ID}.breakdance.autoshow")
        {{
            string tv = V(j, "tour");
            if (tv != null) {{ int pt; if (int.TryParse(tv, out pt) && pt >= 0 && pt <= 9) {{ selectedTour = pt; Log("Tour gewaehlt: " + tourNm[pt]); if (showCtx != null && !showRunning) SetTtl(showCtx, tourNm[pt]); }} }}
            string nv = V(j, "night");
            if (nv != null) {{ nightMode = nv == "true"; Log("Nacht-Modus: " + (nightMode ? "AN" : "AUS")); }}
            string lv = V(j, "loop");
            if (lv != null) {{ autoLoop = lv == "true"; Log("AutoLoop: " + (autoLoop ? "AN" : "AUS")); }}
            string pv = V(j, "pause");
            if (pv != null) {{ int ppv; if (int.TryParse(pv, out ppv) && ppv >= 5) {{ loopPause = ppv; Log("Loop-Pause: " + ppv + "s"); }} }}
        }}
        else if (ev == "didReceiveSettings" && action == "{PLUGIN_ID}.breakdance.autoshow_drive")
        {{
            string tv = V(j, "tour");
            if (tv != null) {{ int pt; if (int.TryParse(tv, out pt) && pt >= 0 && pt <= 9) {{ selectedTour = pt; Log("Drive Tour gewaehlt: " + tourNm[pt]); if (showCtxDrive != null && !showRunning) SetTtl(showCtxDrive, tourNm[pt]); }} }}
            string nv = V(j, "night");
            if (nv != null) {{ nightMode = nv == "true"; Log("Drive Nacht-Modus: " + (nightMode ? "AN" : "AUS")); }}
            string lv = V(j, "loop");
            if (lv != null) {{ autoLoop = lv == "true"; Log("Drive AutoLoop: " + (autoLoop ? "AN" : "AUS")); }}
            string pv = V(j, "pause");
            if (pv != null) {{ int ppv; if (int.TryParse(pv, out ppv) && ppv >= 5) {{ loopPause = ppv; Log("Drive Loop-Pause: " + ppv + "s"); }} }}
        }}
        else if (ev == "didReceiveSettings" && action == "{PLUGIN_ID}.turaka.autoshow")
        {{
            string tv = V(j, "tour");
            if (tv != null) {{ int pt; if (int.TryParse(tv, out pt) && pt >= 0 && pt <= 9) {{ selectedTour = pt; Log("TK Tour gewaehlt: " + tourNm[pt]); if (showCtxTK != null && !showRunning) SetTtl(showCtxTK, tourNm[pt]); }} }}
            string nv = V(j, "night");
            if (nv != null) {{ nightMode = nv == "true"; Log("TK Nacht-Modus: " + (nightMode ? "AN" : "AUS")); }}
            string lv = V(j, "loop");
            if (lv != null) {{ autoLoop = lv == "true"; Log("TK AutoLoop: " + (autoLoop ? "AN" : "AUS")); }}
            string pv = V(j, "pause");
            if (pv != null) {{ int ppv; if (int.TryParse(pv, out ppv) && ppv >= 5) {{ loopPause = ppv; Log("TK Loop-Pause: " + ppv + "s"); }} }}
        }}
        else if (ev == "didReceiveSettings" && action == "{PLUGIN_ID}.timer.startstop")
        {{
            string dv = V(j, "duration");
            if (dv != null) {{ int pd; if (int.TryParse(dv, out pd) && pd >= 10) {{ timerDuration = pd; if (!timerRunning) timerRemaining = pd; Log("Timer Dauer gesetzt: " + pd + "s"); if (timerCtx != null) SetTtl(timerCtx, TFmt()); }} }}
        }}
        else if (ev == "keyDown" && action == "{PLUGIN_ID}.timer.startstop" && context != null)
        {{
            timerKeyDown = DateTime.Now;
        }}
        else if (ev == "keyUp" && action == "{PLUGIN_ID}.timer.startstop" && context != null)
        {{
            double held = (DateTime.Now - timerKeyDown).TotalMilliseconds;
            if (held > 800)
            {{
                timerGen++;
                timerRunning = false;
                timerPaused = false;
                timerRemaining = timerDuration;
                if (timerCtx != null) SetTtl(timerCtx, TFmt());
                Log("Timer Reset (hold): " + timerDuration + "s");
            }}
            else if (!timerRunning)
            {{
                timerRunning = true;
                timerPaused = false;
                int gen = ++timerGen;
                timerThread = new Thread(() => TRun(gen));
                timerThread.IsBackground = true;
                timerThread.Start();
                Log("Timer gestartet: " + timerRemaining + "s");
                if (timerCtx != null) SetTtl(timerCtx, TFmt());
            }}
            else
            {{
                timerPaused = !timerPaused;
                Log("Timer " + (timerPaused ? "pausiert" : "fortgesetzt") + ": " + timerRemaining + "s");
                if (timerCtx != null) SetTtl(timerCtx, TFmt());
            }}
        }}
        else if (ev == "keyDown" && action == "{PLUGIN_ID}.breakdance.pktippen" && context != null)
        {{
            pkTipActive = !pkTipActive;
            if (pkTipActive)
            {{
                keybd_event(0, 0x2F, 8u, UIntPtr.Zero);
                keybd_event(0, 0x30, 8u, UIntPtr.Zero);
                SetImg(context, true);
                SetTtl(context, "P+K Tip\\n[ AN ]");
                Log("P+K Tip: AN");
            }}
            else
            {{
                keybd_event(0, 0x2F, 8u | 2u, UIntPtr.Zero);
                keybd_event(0, 0x30, 8u | 2u, UIntPtr.Zero);
                SetImg(context, false);
                SetTtl(context, "P+K Tip\\n[ AUS ]");
                Log("P+K Tip: AUS");
            }}
        }}
        else if (ev == "keyDown" && action == "{PLUGIN_ID}.breakdance.autoshow" && context != null)
        {{
            showKeyDown = DateTime.Now;
        }}
        else if (ev == "keyDown" && action == "{PLUGIN_ID}.breakdance.autoshow_drive" && context != null)
        {{
            showKeyDown = DateTime.Now;
        }}
        else if (ev == "keyUp" && action == "{PLUGIN_ID}.breakdance.autoshow" && context != null)
        {{
            double held = (DateTime.Now - showKeyDown).TotalMilliseconds;
            showCtx = context; // BD-Context sicherstellen!
            if (showRunning)
            {{
                showGen++;
                showRunning = false;
                autoShowDriveOnly = false;
                // Safety release aller Hold-Tasten bei Abbruch (NUR wenn S2L nicht laeuft!)
                if (!s2lRunning)
                {{
                    keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo
                    keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel
                    keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo
                    keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero); // Flamme
                }}
                keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse
                Log("AutoShow: Abgebrochen (held=" + held + "ms)");
                SHTitle("ABBRUCH!");
                SetImg(showCtx, false);
                var ct = new Thread(() => {{ Thread.Sleep(3000); if (!showRunning) SHTitle("AUTO\\nSHOW"); }});
                ct.IsBackground = true;
                ct.Start();
            }}
            else
            {{
                showRunning = true;
                autoShowDriveOnly = false;
                showPhaseText = "";
                int gen = ++showGen;
                showCountdownSec = EstimateShowCountdownSec(selectedTour, nightMode);
                SetImg(showCtx, true);
                if (showCtxDrive != null) SetImg(showCtxDrive, false);
                showThread = new Thread(() => {{
                    if (selectedTour >= 6) RunMDShow(gen);
                    else RunBDShow(gen);
                }});
                showThread.IsBackground = true;
                showThread.Start();
                var stt = new Thread(SHTimerRun);
                stt.IsBackground = true;
                stt.Start();
                Log("AutoShow: BreakDance gestartet");
            }}
        }}
        else if (ev == "keyUp" && action == "{PLUGIN_ID}.breakdance.autoshow_drive" && context != null)
        {{
            double held = (DateTime.Now - showKeyDown).TotalMilliseconds;
            showCtxDrive = context;
            showCtx = context;
            if (showRunning)
            {{
                showGen++;
                showRunning = false;
                autoShowDriveOnly = false;
                EmergencyDriveStop();
                Log("AutoShow Drive: Abgebrochen (held=" + held + "ms)");
                SHTitle("ABBRUCH!");
                SetImg(showCtxDrive, false);
                var ct = new Thread(() => {{ Thread.Sleep(3000); if (!showRunning && showCtxDrive != null) SetTtl(showCtxDrive, "AUTO\\nDRIVE"); }});
                ct.IsBackground = true;
                ct.Start();
            }}
            else
            {{
                showRunning = true;
                autoShowDriveOnly = true;
                ResetDriveAxisEstimator();
                showPhaseText = "";
                int gen = ++showGen;
                showCountdownSec = EstimateShowCountdownSec(selectedTour, nightMode);
                SetImg(showCtxDrive, true);
                if (showCtx != null && showCtx != showCtxDrive) SetImg(showCtx, false);
                showThread = new Thread(() => {{
                    if (selectedTour >= 6) RunMDShow(gen);
                    else RunBDShow(gen);
                }});
                showThread.IsBackground = true;
                showThread.Start();
                var stt = new Thread(SHTimerRun);
                stt.IsBackground = true;
                stt.Start();
                Log("AutoShow: Drive gestartet (ohne Licht/FX)");
            }}
        }}
        else if (ev == "keyDown" && action == "{PLUGIN_ID}.turaka.autoshow" && context != null)
        {{
            showKeyDown = DateTime.Now;
        }}
        else if (ev == "keyUp" && action == "{PLUGIN_ID}.turaka.autoshow" && context != null)
        {{
            double held = (DateTime.Now - showKeyDown).TotalMilliseconds;
            showCtx = showCtxTK;
            if (showRunning)
            {{
                showGen++;
                showRunning = false;
                autoShowDriveOnly = false;
                // Safety release aller Hold-Tasten bei Abbruch (NUR wenn S2L nicht laeuft!)
                if (!s2lRunning)
                {{
                    keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo
                    keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel
                    keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo
                    keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero); // Flamme
                }}
                keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse
                Log("AutoShow TK: Abgebrochen (held=" + held + "ms)");
                SHTitle("ABBRUCH!");
                SetImg(showCtx, false);
                var ct = new Thread(() => {{ Thread.Sleep(3000); if (!showRunning) {{ if (showCtxTK != null) SetTtl(showCtxTK, "AUTO\\nSHOW"); }} }});
                ct.IsBackground = true;
                ct.Start();
            }}
            else
            {{
                showRunning = true;
                autoShowDriveOnly = false;
                showPhaseText = "";
                int gen = ++showGen;
                showCountdownSec = nightMode ? 230 : 375;
                SetImg(showCtx, true);
                showThread = new Thread(() => {{
                    RunTKShow(gen);
                }});
                showThread.IsBackground = true;
                showThread.Start();
                var stt = new Thread(SHTimerRun);
                stt.IsBackground = true;
                stt.Start();
                Log("AutoShow: Turaka gestartet");
            }}
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
                    int minD = repeatMs;
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
                        if (delay > minD) delay = Math.Max(delay - 50, minD);
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

    static string TFmt()
    {{
        int m = timerRemaining / 60;
        int s = timerRemaining % 60;
        string status = timerRunning ? (timerPaused ? "PAUSE" : ">>>") : "STOP";
        return m.ToString() + ":" + s.ToString("D2") + "\\n" + status;
    }}

    static void TRun(int gen)
    {{
        while (timerRemaining > 0 && timerGen == gen)
        {{
            if (!timerPaused)
            {{
                Thread.Sleep(1000);
                if (timerGen != gen) break;
                if (!timerPaused) timerRemaining--;
                if (timerCtx != null) SetTtl(timerCtx, TFmt());
            }}
            else
                Thread.Sleep(100);
        }}
        if (timerGen == gen && timerRemaining <= 0)
        {{
            Log("Timer ABGELAUFEN!");
            timerRunning = false;
            // 5x blinken
            for (int i = 0; i < 5 && timerGen == gen; i++)
            {{
                if (timerCtx != null) SetTtl(timerCtx, "0:00\\nFERTIG!");
                Thread.Sleep(500);
                if (timerCtx != null) SetTtl(timerCtx, "");
                Thread.Sleep(500);
            }}
            timerRemaining = timerDuration;
            if (timerCtx != null) SetTtl(timerCtx, TFmt());
        }}
    }}

    static bool IsDriveOnlyFxBlocked(byte scan, byte mod)
    {{
        // Intentionally thread-agnostic: MD programs still emit some raw keybd_event
        // calls, and drive-only must suppress FX/light keys regardless of caller thread.
        if (!(autoShowDriveOnly && showRunning))
            return false;

        if (scan >= 0x4F && scan <= 0x51) return true; // Numpad 1-3 (Presets)
        if (scan >= 0x47 && scan <= 0x4D) return true; // Numpad 4-9 (Presets)
        if (scan >= 0x02 && scan <= 0x0B) return true; // Light 1-9 + all off
        if (scan == 0x39 || scan == 0x20 || scan == 0x2E || scan == 0x0C) return true; // strobo/fog/flame/led
        if (mod == 0x2A) return true; // Shift-based light controls (MH, spots, color strobe)
        if (mod == 0x1D && scan == 0x2E) return true; // Ctrl+C bubbles
        return false;
    }}

    static bool IsDriveOnlyInfoTitleBlocked(string t)
    {{
        if (!(autoShowDriveOnly && showRunning)) return false;
        string u = (t ?? "").ToUpperInvariant();
        return u.Contains("NEBEL") || u.Contains("FLAMME") || u.Contains("SEIFENBLASEN") || u.Contains("STROBO") || u.Contains("ALLES");
    }}

    static void EmergencyDriveStop()
    {{
        Log("AutoShow Drive: Not-Stopp gestartet");
        driveDynamicPulseEnabled = false;
        driveAutoStopping = true;

        // Safety release fuer moeglich aktive Hold-Keys (NUR wenn S2L nicht laeuft!)
        if (!s2lRunning)
        {{
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo
            keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero); // Flamme
        }}
        keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse (immer releasen)

        // Hart auf 0 runterbremsen.
        for (int i = 0; i < 18; i++)
        {{
            keybd_event(0, 0x22, 8u, UIntPtr.Zero); Thread.Sleep(35); keybd_event(0, 0x22, 8u | 2u, UIntPtr.Zero); Thread.Sleep(35); // Kreuz-
            keybd_event(0, 0x21, 8u, UIntPtr.Zero); Thread.Sleep(35); keybd_event(0, 0x21, 8u | 2u, UIntPtr.Zero); Thread.Sleep(35); // Platte-
        }}

        // Motoren GLEICHZEITIG aus.
        keybd_event(0, 0x24, 8u, UIntPtr.Zero); // Kreuz OFF runter
        keybd_event(0, 0x16, 8u, UIntPtr.Zero); // Platte OFF runter
        Thread.Sleep(120);
        keybd_event(0, 0x24, 8u | 2u, UIntPtr.Zero); // Kreuz OFF hoch
        keybd_event(0, 0x16, 8u | 2u, UIntPtr.Zero); // Platte OFF hoch
        Thread.Sleep(200);
        if (pkTipWasActive) SetPkTip(true); // P+K Tip wiederherstellen (war vorher AN)

        drivePlatteEst = 0;
        driveKreuzEst = 0;
        driveLastBrake = DateTime.Now;
        driveAutoStopping = false;
        Log("AutoShow Drive: Not-Stopp beendet (0% + Kreuz/Platte AUS)");
    }}

    static void ResetDriveAxisEstimator()
    {{
        drivePlatteEst = 0;
        driveKreuzEst = 0;
        driveNextDynamicPulse = DateTime.Now.AddMilliseconds(3500);
        driveLastBrake = DateTime.MinValue;
        driveAutoStopping = false;
        drivePartyMin = 18;
        drivePartyGap = 8;
        driveTelemetryLastRead = DateTime.MinValue;
        driveTelemetryLastWrite = DateTime.MinValue;
        driveTelemetryAvailable = false;
        driveDynamicPulseEnabled = true;
    }}

    // P+K Tip zentral ein-/ausschalten (fuer Auto-Drive Steuerung).
    static void SetPkTip(bool on)
    {{
        if (pkTipActive == on) return; // bereits im gewuenschten Zustand
        pkTipActive = on;
        if (on)
        {{
            keybd_event(0, 0x2F, 8u, UIntPtr.Zero);
            keybd_event(0, 0x30, 8u, UIntPtr.Zero);
        }}
        else
        {{
            keybd_event(0, 0x2F, 8u | 2u, UIntPtr.Zero);
            keybd_event(0, 0x30, 8u | 2u, UIntPtr.Zero);
        }}
        if (pkTipCtx != null)
        {{
            SetImg(pkTipCtx, on);
            SetTtl(pkTipCtx, on ? "P+K Tip\\n[ AN ]" : "P+K Tip\\n[ AUS ]");
        }}
        Log("P+K Tip AUTO: " + (on ? "AN" : "AUS"));
    }}

    static float ParseTelemetryFloat(string raw)
    {{
        float value;
        if (float.TryParse((raw ?? "").Trim().Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out value))
            return value;
        return 0f;
    }}

    static void TryReadBreakdanceTelemetry(bool force)
    {{
        if (!(autoShowDriveOnly && showRunning)) return;

        var now = DateTime.Now;
        if (!force && (now - driveTelemetryLastRead).TotalMilliseconds < 200)
            return;
        driveTelemetryLastRead = now;

        try
        {{
            if (!File.Exists(breakdanceStatePath))
            {{
                driveTelemetryAvailable = false;
                return;
            }}

            DateTime lastWrite = File.GetLastWriteTimeUtc(breakdanceStatePath);
            if (!force && lastWrite == driveTelemetryLastWrite)
                return;
            driveTelemetryLastWrite = lastWrite;

            string line = File.ReadAllText(breakdanceStatePath).Trim();
            if (line.Length == 0)
                return;

            var parts = line.Split(';');
            var values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < parts.Length; i++)
            {{
                var kv = parts[i].Split(new char[] {{ '=' }}, 2);
                if (kv.Length == 2)
                    values[kv[0].Trim()] = kv[1].Trim();
            }}

            driveRealPlate = values.ContainsKey("plate") ? ParseTelemetryFloat(values["plate"]) : 0f;
            driveRealCross = values.ContainsKey("cross") ? ParseTelemetryFloat(values["cross"]) : 0f;
            driveRealPlateOn = values.ContainsKey("plateOn") && values["plateOn"].Equals("True", StringComparison.OrdinalIgnoreCase);
            driveRealCrossOn = values.ContainsKey("crossOn") && values["crossOn"].Equals("True", StringComparison.OrdinalIgnoreCase);
            driveRealBrakeOn = values.ContainsKey("brakeOn") && values["brakeOn"].Equals("True", StringComparison.OrdinalIgnoreCase);
            driveRealEStop = values.ContainsKey("eStop") && values["eStop"].Equals("True", StringComparison.OrdinalIgnoreCase);

            drivePlatteEst = driveRealPlateOn ? Math.Max(0, Math.Min(driveMaxEst, (int)Math.Round(Math.Abs(driveRealPlate) * driveMaxEst))) : 0;
            driveKreuzEst = driveRealCrossOn ? Math.Max(0, Math.Min(driveMaxEst, (int)Math.Round(Math.Abs(driveRealCross) * driveMaxEst))) : 0;
            driveTelemetryAvailable = true;
        }}
        catch (Exception ex)
        {{
            if (driveTelemetryAvailable)
                Log("Telemetry read failed: " + ex.Message);
            driveTelemetryAvailable = false;
        }}
    }}

    static bool InDriveShowThread()
    {{
        return autoShowDriveOnly && showRunning && driveDynamicPulseEnabled && showThread != null && Thread.CurrentThread.ManagedThreadId == showThread.ManagedThreadId;
    }}

    static bool IsDriveAxisScan(byte scan)
    {{
        return scan == 0x13 || scan == 0x14 || scan == 0x21 || scan == 0x22;
    }}

    static int GetDriveAxisEst(byte scan)
    {{
        return (scan == 0x13 || scan == 0x21) ? drivePlatteEst : driveKreuzEst;
    }}

    static int GetDriveAxisStep(byte scan)
    {{
        int est = GetDriveAxisEst(scan);
        bool positive = scan == 0x13 || scan == 0x14;
        int step = 2;

        if ((positive && est <= driveSoftMinEst) || (!positive && est >= driveSoftMaxEst))
            step = 4;
        else if (Math.Abs(est - 12) >= 4)
            step = 3;

        return step;
    }}

    static int GetDriveAxisHoldMs(byte scan, byte mod)
    {{
        if (!(autoShowDriveOnly && showRunning && mod == 0 && IsDriveAxisScan(scan))) return 150;

        int est = GetDriveAxisEst(scan);
        bool positive = scan == 0x13 || scan == 0x14;
        int bias = positive ? Math.Max(0, 12 - est) : Math.Max(0, est - 12);
        int holdMs = 220 + bias * 35;

        if ((positive && est <= driveSoftMinEst) || (!positive && est >= driveSoftMaxEst))
            holdMs += 180;

        if (holdMs < 180) holdMs = 180;
        if (holdMs > 900) holdMs = 900;
        return holdMs;
    }}

    static void ApplyDriveDynamicPulse(int gen)
    {{
        if (!InDriveShowThread() || showGen != gen || driveAutoStopping) return;

        bool pulsed = false;
        if (drivePlatteEst <= driveSoftMinEst)
        {{
            Log("TRACE DRIVE PULSE Platte+ est=" + drivePlatteEst);
            SHTap(0x13, 8, 0);
            // Doppel-Pulse wenn est sehr niedrig (unter 10 = 42%)
            if (drivePlatteEst <= 10 && showGen == gen)
            {{
                Thread.Sleep(200);
                SHTap(0x13, 8, 0);
                Log("TRACE DRIVE PULSE Platte+ EXTRA est=" + drivePlatteEst);
            }}
            pulsed = true;
        }}

        if (showGen != gen) return;

        if (driveKreuzEst <= driveSoftMinEst)
        {{
            Log("TRACE DRIVE PULSE Kreuz+ est=" + driveKreuzEst);
            SHTap(0x14, 8, 0);
            if (driveKreuzEst <= 10 && showGen == gen)
            {{
                Thread.Sleep(200);
                SHTap(0x14, 8, 0);
                Log("TRACE DRIVE PULSE Kreuz+ EXTRA est=" + driveKreuzEst);
            }}
            pulsed = true;
        }}

        driveNextDynamicPulse = DateTime.Now.AddMilliseconds(pulsed ? 1200 : 3500);
    }}

    static byte RewriteDriveAxisTap(byte scan, byte mod)
    {{
        if (!(autoShowDriveOnly && showRunning && mod == 0)) return scan;

        TryReadBreakdanceTelemetry(false);

        if (driveAutoStopping)
        {{
            switch (scan)
            {{
                case 0x21:
                    drivePlatteEst = Math.Max(0, drivePlatteEst - GetDriveAxisStep(scan));
                    return scan;
                case 0x22:
                    driveKreuzEst = Math.Max(0, driveKreuzEst - GetDriveAxisStep(scan));
                    return scan;
                case 0x16:
                    drivePlatteEst = 0;
                    return scan;
                case 0x24:
                    driveKreuzEst = 0;
                    return scan;
            }}
        }}

        int step = GetDriveAxisStep(scan);

        switch (scan)
        {{
            case 0x13: // Platte+
                if (drivePlatteEst >= driveMaxEst || drivePlatteEst - driveKreuzEst >= drivePartyGap)
                {{
                    drivePlatteEst = Math.Max(drivePartyMin, drivePlatteEst - step);
                    Log("TRACE TAP REWRITE Platte+ -> Platte- est=" + drivePlatteEst);
                    return 0x21;
                }}
                drivePlatteEst = Math.Min(driveMaxEst, drivePlatteEst + step);
                return scan;
            case 0x14: // Kreuz+
                if (driveKreuzEst >= driveMaxEst || driveKreuzEst - drivePlatteEst >= drivePartyGap)
                {{
                    driveKreuzEst = Math.Max(drivePartyMin, driveKreuzEst - step);
                    Log("TRACE TAP REWRITE Kreuz+ -> Kreuz- est=" + driveKreuzEst);
                    return 0x22;
                }}
                driveKreuzEst = Math.Min(driveMaxEst, driveKreuzEst + step);
                return scan;
            case 0x21: // Platte-
                if (drivePlatteEst <= drivePartyMin || driveKreuzEst - drivePlatteEst >= drivePartyGap + 2)
                {{
                    drivePlatteEst = Math.Min(driveMaxEst, drivePlatteEst + step);
                    Log("TRACE TAP REWRITE Platte- -> Platte+ est=" + drivePlatteEst);
                    return 0x13;
                }}
                drivePlatteEst = Math.Max(drivePartyMin, drivePlatteEst - step);
                return scan;
            case 0x22: // Kreuz-
                if (driveKreuzEst <= drivePartyMin || drivePlatteEst - driveKreuzEst >= drivePartyGap + 2)
                {{
                    driveKreuzEst = Math.Min(driveMaxEst, driveKreuzEst + step);
                    Log("TRACE TAP REWRITE Kreuz- -> Kreuz+ est=" + driveKreuzEst);
                    return 0x14;
                }}
                driveKreuzEst = Math.Max(drivePartyMin, driveKreuzEst - step);
                return scan;
            case 0x15:
                drivePlatteEst = 0;
                return scan;
            case 0x16:
                drivePlatteEst = 0;
                return scan;
            case 0x23:
                driveKreuzEst = 0;
                return scan;
            case 0x24:
                driveKreuzEst = 0;
                return scan;
            default:
                return scan;
        }}
    }}

    static bool GracefulDriveAutoStop(int gen)
    {{
        Log("AutoShow Drive: Auto-Stopp gestartet");
        driveDynamicPulseEnabled = false;
        driveAutoStopping = true;

        SHTitle("Runter-\\nfahren");
        for (int i = 0; i < 6; i++)
        {{
            SHTap(0x22, 8, 0); Thread.Sleep(150); SHTap(0x21, 8, 0);
            if (!SHWait(400, gen)) {{ driveAutoStopping = false; return false; }}
        }}

        SHTitle("Stopp");
        for (int i = 0; i < 6; i++)
        {{
            SHTap(0x22, 8, 0); Thread.Sleep(120); SHTap(0x21, 8, 0);
            if (!SHWait(300, gen)) {{ driveAutoStopping = false; return false; }}
        }}

        if (!SHWait(300, gen)) {{ driveAutoStopping = false; return false; }}

        SHTitle("Stopp");
        // Kreuz + Platte GLEICHZEITIG aus (damit Spiel Tip-Keys nicht einzeln resettet)
        keybd_event(0, 0x24, 8u, UIntPtr.Zero); // Kreuz OFF runter
        keybd_event(0, 0x16, 8u, UIntPtr.Zero); // Platte OFF runter
        Thread.Sleep(400);
        keybd_event(0, 0x24, 8u | 2u, UIntPtr.Zero); // Kreuz OFF hoch
        keybd_event(0, 0x16, 8u | 2u, UIntPtr.Zero); // Platte OFF hoch
        if (showGen != gen) {{ driveAutoStopping = false; return false; }}
        Thread.Sleep(300);
        if (pkTipWasActive) SetPkTip(true); // P+K Tip wiederherstellen (war vorher AN)

        drivePlatteEst = 0;
        driveKreuzEst = 0;
        driveLastBrake = DateTime.Now;
        driveAutoStopping = false;
        Log("AutoShow Drive: Auto-Stopp beendet (0% + Kreuz/Platte AUS)");
        return true;
    }}

    static string ScanName(byte scan)
    {{
        switch (scan)
        {{
            case 0x11: return "SpotColor";
            case 0x12: return "SpotGobo";
            case 0x13: return "Platte+";
            case 0x14: return "Kreuz+";
            case 0x15: return "Platte ON";
            case 0x16: return "Platte OFF";
            case 0x20: return "Nebel";
            case 0x21: return "Platte-";
            case 0x22: return "Kreuz-";
            case 0x23: return "Kreuz ON";
            case 0x24: return "Kreuz OFF";
            case 0x2C: return "Hupe/MH";
            case 0x2D: return "MH Licht";
            case 0x2E: return "Flamme";
            case 0x31: return "Gondelbremse";
            case 0x39: return "Strobo";
            case 0x0C: return "LED-Strobo";
            case 0x47: return "Preset7";
            case 0x48: return "Preset8";
            case 0x49: return "Preset9";
            case 0x4B: return "Preset4";
            case 0x4C: return "Preset5";
            case 0x4D: return "Preset6";
            case 0x4F: return "Preset1";
            case 0x50: return "Preset2";
            case 0x51: return "Preset3";
            default: return "?";
        }}
    }}

    static string ScansToString(byte[] scans)
    {{
        string s = "";
        for (int i = 0; i < scans.Length; i++)
        {{
            if (i > 0) s += ",";
            s += "0x" + scans[i].ToString("X2") + "(" + ScanName(scans[i]) + ")";
        }}
        return s;
    }}

    static void SHTap(byte scan, uint flags, byte mod)
    {{
        scan = RewriteDriveAxisTap(scan, mod);
        int holdMs = GetDriveAxisHoldMs(scan, mod);
        if (IsDriveOnlyFxBlocked(scan, mod))
        {{
            Log("TRACE TAP BLOCKED scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") mod=0x" + mod.ToString("X2") + " driveOnly=" + autoShowDriveOnly);
            return;
        }}
        Log("TRACE TAP scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") mod=0x" + mod.ToString("X2") + " flags=" + flags + " hold=" + holdMs + "ms driveOnly=" + autoShowDriveOnly);
        if (mod > 0) keybd_event(0, mod, 8u, UIntPtr.Zero);
        keybd_event(0, scan, flags, UIntPtr.Zero);
        Thread.Sleep(holdMs);
        keybd_event(0, scan, flags | 2u, UIntPtr.Zero);
        if (mod > 0) keybd_event(0, mod, 8u | 2u, UIntPtr.Zero);
    }}

    static bool SHWait(int ms, int gen)
    {{
        for (int i = 0; i < ms && showGen == gen; i += 50)
        {{
            TryReadBreakdanceTelemetry(false);
            if (InDriveShowThread() && DateTime.Now >= driveNextDynamicPulse)
                ApplyDriveDynamicPulse(gen);
            Thread.Sleep(50);
        }}
        return showGen == gen;
    }}

    static void SHRepeat(byte scan, uint flags, int durationMs, int intervalMs, int gen)
    {{
        Log("TRACE REPEAT START scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") duration=" + durationMs + "ms interval=" + intervalMs + "ms gen=" + gen);
        int elapsed = 0;
        while (elapsed < durationMs && showGen == gen)
        {{
            Log("TRACE REPEAT TAP scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") t=" + elapsed + "ms gen=" + gen);
            keybd_event(0, scan, flags, UIntPtr.Zero);
            Thread.Sleep(30);
            keybd_event(0, scan, flags | 2u, UIntPtr.Zero);
            int w = intervalMs - 30;
            if (w > 0) Thread.Sleep(w);
            elapsed += intervalMs;
        }}
        Log("TRACE REPEAT END scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") elapsed=" + elapsed + "ms gen=" + gen + " showGen=" + showGen);
    }}

    // Taste gehalten fuer durationMs (fuer Effekte: Nebel, Strobo, Flamme, Gondelbremse, Hupe)
    static void SHHold(byte scan, uint flags, int durationMs, int gen)
    {{
        int originalDurationMs = durationMs;
        // AUTO DRIVE: Gondelbremse fuer Drama-Effekt.
        // Haltedauer auf max 3500ms begrenzen, Cooldown 8s.
        if (autoShowDriveOnly && scan == 0x31)
        {{
            if (driveLastBrake != DateTime.MinValue && (DateTime.Now - driveLastBrake).TotalMilliseconds < 8000)
            {{
                Log("TRACE HOLD SKIP scan=0x31(Gondelbremse) cooldown active original=" + originalDurationMs + "ms");
                SHWait(Math.Min(durationMs, 250), gen);
                return;
            }}

            if (durationMs > 3500)
                durationMs = 3500;

            driveLastBrake = DateTime.Now;
        }}

        if (IsDriveOnlyFxBlocked(scan, 0))
        {{
            Log("TRACE HOLD BLOCKED scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") duration=" + durationMs + "ms original=" + originalDurationMs + "ms gen=" + gen + " driveOnly=" + autoShowDriveOnly);
            SHWait(durationMs, gen);
            return;
        }}
        Log("TRACE HOLD scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") duration=" + durationMs + "ms original=" + originalDurationMs + "ms gen=" + gen + " driveOnly=" + autoShowDriveOnly);
        keybd_event(0, scan, flags, UIntPtr.Zero);
        SHWait(durationMs, gen);
        keybd_event(0, scan, flags | 2u, UIntPtr.Zero);
        // P+K Tip Schutz: Falls pkTipActive und dieser Scan einer der Tip-Tasten ist,
        // sofort wieder druecken damit der Tip-Hold nicht unterbrochen wird.
        if (pkTipActive && (scan == 0x2F || scan == 0x30))
        {{
            keybd_event(0, scan, flags, UIntPtr.Zero);
            Log("TRACE HOLD P+K-TIP-RESTORE scan=0x" + scan.ToString("X2"));
        }}
    }}

    // Mehrere Tasten GLEICHZEITIG gehalten! (z.B. Nebel+Flamme+Strobo)
    static void SHHoldMulti(byte[] scans, uint flags, int durationMs, int gen)
    {{
        Log("TRACE HOLD-MULTI START scans=" + ScansToString(scans) + " duration=" + durationMs + "ms gen=" + gen + " driveOnly=" + autoShowDriveOnly);
        List<byte> active = new List<byte>();
        foreach (byte s in scans)
        {{
            if (!IsDriveOnlyFxBlocked(s, 0))
            {{
                active.Add(s);
                keybd_event(0, s, flags, UIntPtr.Zero);
            }}
            else
            {{
                Log("TRACE HOLD-MULTI BLOCKED scan=0x" + s.ToString("X2") + "(" + ScanName(s) + ") gen=" + gen);
            }}
        }}
        if (active.Count == 0)
        {{
            Log("TRACE HOLD-MULTI ALL-BLOCKED duration=" + durationMs + "ms gen=" + gen);
            SHWait(durationMs, gen);
            return;
        }}
        SHWait(durationMs, gen);
        foreach (byte s in active) keybd_event(0, s, flags | 2u, UIntPtr.Zero);
        // P+K Tip Schutz: Tip-Tasten sofort wieder druecken falls pkTipActive.
        if (pkTipActive)
        {{
            foreach (byte s in active)
            {{
                if (s == 0x2F || s == 0x30)
                {{
                    keybd_event(0, s, flags, UIntPtr.Zero);
                    Log("TRACE HOLD-MULTI P+K-TIP-RESTORE scan=0x" + s.ToString("X2"));
                }}
            }}
        }}
        Log("TRACE HOLD-MULTI END active=" + ScansToString(active.ToArray()) + " duration=" + durationMs + "ms gen=" + gen);
    }}

    // Modifier+Taste gehalten (fuer Seifenblasen = Ctrl+C)
    static void SHModHold(byte mod, byte scan, uint flags, int durationMs, int gen)
    {{
        if (IsDriveOnlyFxBlocked(scan, mod))
        {{
            Log("TRACE MOD-HOLD BLOCKED mod=0x" + mod.ToString("X2") + " scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") duration=" + durationMs + "ms gen=" + gen + " driveOnly=" + autoShowDriveOnly);
            SHWait(durationMs, gen);
            return;
        }}
        Log("TRACE MOD-HOLD mod=0x" + mod.ToString("X2") + " scan=0x" + scan.ToString("X2") + "(" + ScanName(scan) + ") duration=" + durationMs + "ms gen=" + gen + " driveOnly=" + autoShowDriveOnly);
        keybd_event(0, mod, 8u, UIntPtr.Zero);
        keybd_event(0, scan, flags, UIntPtr.Zero);
        SHWait(durationMs, gen);
        keybd_event(0, scan, flags | 2u, UIntPtr.Zero);
        keybd_event(0, mod, 8u | 2u, UIntPtr.Zero);
    }}

    static void SHTitle(string t)
    {{
        if (IsDriveOnlyInfoTitleBlocked(t))
            t = "AUTO\\nDRIVE";
        showPhaseText = t;
        if (showCtx != null && !showRunning) SetTtl(showCtx, t);
    }}

    static void SHTimerRun()
    {{
        int remaining = showCountdownSec;
        var lastTick = DateTime.Now;
        while (showRunning)
        {{
            try
            {{
                var now = DateTime.Now;
                if ((now - lastTick).TotalMilliseconds >= 1000)
                {{
                    if (remaining > 0) remaining--;
                    lastTick = now;
                }}
                int m = remaining / 60;
                int s = remaining % 60;
                string display = m + ":" + s.ToString("D2") + "\\n" + showPhaseText;
                if (showCtx != null)
                    SetTtl(showCtx, display);
            }}
            catch {{ }}
            Thread.Sleep(500);
        }}
    }}

    // === SOUND2LIGHT ENGINE ===
    // WASAPI COM GUIDs
    static Guid CLSID_MMDeviceEnumerator = new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E");
    static Guid IID_IMMDeviceEnumerator = new Guid("A95664D2-9614-4F35-A746-DE8DB63617E6");
    static Guid IID_IAudioClient = new Guid("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2");
    static Guid IID_IAudioCaptureClient = new Guid("C8ADBD64-E71E-48A0-A4DE-185C395CD317");

    // Preset Scan-Codes (Numpad 1-9)
    static byte[] presetScans = {{ 0x4F, 0x50, 0x51, 0x4B, 0x4C, 0x4D, 0x47, 0x48, 0x49 }};

    static void S2LSetPreset(int preset)
    {{
        if (preset < 1 || preset > 9 || preset == s2lLastPreset) return;
        if ((DateTime.Now - s2lLastPresetChange).TotalMilliseconds < 8000) return;  // Nicht öfter als alle 8s wechseln
        SHTap(presetScans[preset - 1], 8, 0);
        s2lLastPreset = preset;
        s2lLastPresetChange = DateTime.Now;
        Log("S2L: Preset " + preset);
    }}

    static void S2LDoEffect(byte scan, uint flags, int holdMs, ref DateTime lastTime, int cooldownMs, string name)
    {{
        if ((DateTime.Now - lastTime).TotalMilliseconds < cooldownMs) return;
        lastTime = DateTime.Now;
        Log("S2L: " + name);
        ThreadPool.QueueUserWorkItem(_ => {{
            keybd_event(0, scan, flags, UIntPtr.Zero);
            Thread.Sleep(holdMs);
            keybd_event(0, scan, flags | 2u, UIntPtr.Zero);
        }});
    }}

    static void S2LDoMultiEffect(byte[] scans, int holdMs, ref DateTime lastTime, int cooldownMs, string name, int gen)
    {{
        if ((DateTime.Now - lastTime).TotalMilliseconds < cooldownMs) return;
        lastTime = DateTime.Now;
        Log("S2L: " + name);
        ThreadPool.QueueUserWorkItem(_ => {{
            foreach (byte s in scans) keybd_event(0, s, 8u, UIntPtr.Zero);
            for (int w = 0; w < holdMs; w += 50) Thread.Sleep(50);
            foreach (byte s in scans) keybd_event(0, s, 8u | 2u, UIntPtr.Zero);
        }});
    }}

    static void S2LRun(int gen)
    {{
        Log("S2L: Thread gestartet");
        try
        {{
            CoInitializeEx(IntPtr.Zero, 0);
            IntPtr pEnum;
            int hr = CoCreateInstance(ref CLSID_MMDeviceEnumerator, IntPtr.Zero, 1,
                ref IID_IMMDeviceEnumerator, out pEnum);
            if (hr != 0) {{ Log("S2L: CoCreateInstance fehlgeschlagen: 0x" + hr.ToString("X8")); return; }}
            Log("S2L: MMDeviceEnumerator erstellt");

            // IMMDeviceEnumerator::GetDefaultAudioEndpoint(eRender=0, eMultimedia=1)
            IntPtr ppDevice;
            var enumVtbl = Marshal.ReadIntPtr(pEnum);
            var getDefault = Marshal.GetDelegateForFunctionPointer<GetDefaultAudioEndpointDelegate>(
                Marshal.ReadIntPtr(enumVtbl, 4 * IntPtr.Size));
            hr = getDefault(pEnum, 0, 1, out ppDevice);
            if (hr != 0) {{ Log("S2L: GetDefaultAudioEndpoint fehlgeschlagen: 0x" + hr.ToString("X8")); return; }}
            Log("S2L: Default Audio Device erhalten");

            // IMMDevice::Activate(IAudioClient)
            IntPtr pAudioClient;
            var devVtbl = Marshal.ReadIntPtr(ppDevice);
            var activate = Marshal.GetDelegateForFunctionPointer<ActivateDelegate>(
                Marshal.ReadIntPtr(devVtbl, 3 * IntPtr.Size));
            hr = activate(ppDevice, ref IID_IAudioClient, 0x17, IntPtr.Zero, out pAudioClient);
            if (hr != 0) {{ Log("S2L: Activate IAudioClient fehlgeschlagen: 0x" + hr.ToString("X8")); return; }}
            Log("S2L: AudioClient erstellt");

            // IAudioClient::GetMixFormat
            IntPtr pFormat;
            var acVtbl = Marshal.ReadIntPtr(pAudioClient);
            var getMixFmt = Marshal.GetDelegateForFunctionPointer<GetMixFormatDelegate>(
                Marshal.ReadIntPtr(acVtbl, 8 * IntPtr.Size));
            hr = getMixFmt(pAudioClient, out pFormat);
            if (hr != 0) {{ Log("S2L: GetMixFormat fehlgeschlagen"); return; }}

            int wFormatTag = Marshal.ReadInt16(pFormat, 0);
            int nChannels = Marshal.ReadInt16(pFormat, 2);
            int nSamplesPerSec = Marshal.ReadInt32(pFormat, 4);
            int nBlockAlign = Marshal.ReadInt16(pFormat, 12);
            int wBitsPerSample = Marshal.ReadInt16(pFormat, 14);
            int cbSize = Marshal.ReadInt16(pFormat, 16);
            Log("S2L: Format tag=" + wFormatTag + " ch=" + nChannels + " rate=" + nSamplesPerSec +
                " bits=" + wBitsPerSample + " cbSize=" + cbSize);

            // Check for WAVEFORMATEXTENSIBLE (tag=0xFFFE)
            int actualTag = wFormatTag;
            if (wFormatTag == -2 || wFormatTag == 0xFFFE || (wFormatTag & 0xFFFF) == 0xFFFE)
            {{
                if (cbSize >= 22)
                {{
                    byte[] subFmt = new byte[16];
                    Marshal.Copy(pFormat + 24, subFmt, 0, 16);
                    Guid subGuid = new Guid(subFmt);
                    Guid floatGuid = new Guid("00000003-0000-0010-8000-00aa00389b71");
                    Guid pcmGuid = new Guid("00000001-0000-0010-8000-00aa00389b71");
                    if (subGuid == floatGuid) actualTag = 3;
                    else if (subGuid == pcmGuid) actualTag = 1;
                    Log("S2L: Extensible SubFormat=" + subGuid + " -> tag=" + actualTag);
                }}
            }}

            // IAudioClient::Initialize (AUDCLNT_SHAREMODE_SHARED=0, AUDCLNT_STREAMFLAGS_LOOPBACK=0x00020000)
            long bufDuration = 500000; // 50ms in 100ns units
            var initAC = Marshal.GetDelegateForFunctionPointer<InitializeDelegate>(
                Marshal.ReadIntPtr(acVtbl, 3 * IntPtr.Size));
            hr = initAC(pAudioClient, 0, 0x00020000, bufDuration, 0, pFormat, IntPtr.Zero);
            if (hr != 0) {{ Log("S2L: Initialize fehlgeschlagen: 0x" + hr.ToString("X8")); return; }}
            Log("S2L: AudioClient initialisiert (Loopback)");

            // IAudioClient::GetService(IAudioCaptureClient)
            IntPtr pCapture;
            var getSvc = Marshal.GetDelegateForFunctionPointer<GetServiceDelegate>(
                Marshal.ReadIntPtr(acVtbl, 14 * IntPtr.Size));
            hr = getSvc(pAudioClient, ref IID_IAudioCaptureClient, out pCapture);
            if (hr != 0) {{ Log("S2L: GetService fehlgeschlagen: 0x" + hr.ToString("X8")); return; }}
            Log("S2L: CaptureClient erhalten");

            // IAudioClient::Start
            var startAC = Marshal.GetDelegateForFunctionPointer<StartStopDelegate>(
                Marshal.ReadIntPtr(acVtbl, 10 * IntPtr.Size));
            hr = startAC(pAudioClient);
            if (hr != 0) {{ Log("S2L: Start fehlgeschlagen: 0x" + hr.ToString("X8")); return; }}
            Log("S2L: Audio Capture gestartet!");

            var capVtbl = Marshal.ReadIntPtr(pCapture);
            var getBuffer = Marshal.GetDelegateForFunctionPointer<GetBufferDelegate>(
                Marshal.ReadIntPtr(capVtbl, 3 * IntPtr.Size));
            var releaseBuffer = Marshal.GetDelegateForFunctionPointer<ReleaseBufferDelegate>(
                Marshal.ReadIntPtr(capVtbl, 4 * IntPtr.Size));

            float[] fftBuf = new float[2048];
            bool isFloat = (actualTag == 3);
            bool is16bit = (actualTag == 1 && wBitsPerSample == 16);
            bool is32bit = (actualTag == 1 && wBitsPerSample == 32);
            Log("S2L: Capture bereit (isFloat=" + isFloat + " is16bit=" + is16bit + " is32bit=" + is32bit + ")");

            // Nacht-Modus: Cooldowns verdoppeln
            int nightMul = s2lNightMode ? 2 : 1;
            if (s2lNightMode) Log("S2L: NACHT-MODUS aktiv");

            bool doLoop = true;
            while (doLoop && s2lGen == gen)
            {{
                doLoop = false;

                // ============ PRE-RIDE ============
                if (s2lMode == 0)
                {{
                    // KOMPLETT-MODUS: Hupe, MH, Motoren starten, Hochfahren
                    if (s2lCtx != null) SetTtl(s2lCtx, "S2L\\nHUPE!");
                    keybd_event(0, 0x2C, 8u, UIntPtr.Zero); // Hupe down
                    Thread.Sleep(1000);
                    keybd_event(0, 0x2C, 8u | 2u, UIntPtr.Zero); // Hupe up
                    if (s2lGen != gen) break;

                    SHTap(0x2C, 8, 0x2A); Thread.Sleep(200); // MH AN (Shift+Z)
                    SHTap(0x2D, 8, 0x2A); Thread.Sleep(200); // MH Licht (Shift+X)
                    Thread.Sleep(800);
                    if (s2lGen != gen) break;

                    if (s2lCtx != null) SetTtl(s2lCtx, "S2L\\nStart!");
                    keybd_event(0, 0x15, 8u, UIntPtr.Zero); Thread.Sleep(400); // Teller AN
                    keybd_event(0, 0x15, 8u | 2u, UIntPtr.Zero);
                    Thread.Sleep(800);
                    if (s2lGen != gen) break;

                    keybd_event(0, 0x23, 8u, UIntPtr.Zero); Thread.Sleep(400); // Kreuz AN
                    keybd_event(0, 0x23, 8u | 2u, UIntPtr.Zero);
                    Thread.Sleep(300);
                    if (s2lGen != gen) break;
                    pkTipWasActive = pkTipActive; // Zustand merken
                    SetPkTip(false); // P+K Tip AUS - Fahrt laeuft
                    Thread.Sleep(200);
                    if (s2lGen != gen) break;

                    SHTap(0x4F, 8, 0); // Preset 1
                    Thread.Sleep(500);
                    if (s2lGen != gen) break;

                    // ============ Hochfahren: Platte 4x (~20%) + Kreuz 20x (MAX) ============
                    if (s2lCtx != null) SetTtl(s2lCtx, "S2L\\nHochfahren");
                    for (int i = 0; i < 4; i++)
                    {{
                        SHTap(0x13, 8, 0); Thread.Sleep(200); // Platte+
                        SHTap(0x14, 8, 0);
                        Thread.Sleep(500); // Warten vor nächstem Paar
                        if (s2lGen != gen) break;
                    }}
                    // Die restlichen 16 Kreuz+ (insgesamt 20)
                    for (int i = 0; i < 16 && s2lGen == gen; i++)
                    {{
                        SHTap(0x14, 8, 0); // Kreuz+
                        Thread.Sleep(150);
                    }}
                    SHTap(0x50, 8, 0); // Preset 2
                    Thread.Sleep(500);
                    if (s2lGen != gen) break;

                    Log("S2L: PRE-RIDE + Hochfahren fertig (P=4 K=20)");
                }}
                else
                {{
                    // NUR-LICHT-MODUS: Kein Hupen, keine Motoren, nur Audio + Licht starten
                    Log("S2L LICHT: Starte NUR Lichteffekte (keine Fahrt-Steuerung!)");
                    // Moving Heads + Licht aktivieren (fuer MH-Effekte)
                    SHTap(0x2C, 8, 0x2A); Thread.Sleep(200); // MH AN (Shift+Z)
                    SHTap(0x2D, 8, 0x2A); Thread.Sleep(200); // MH Licht (Shift+X)
                    SHTap(0x10, 8, 0x2A); Thread.Sleep(200); // Spot AN (Shift+Q)
                    s2lSpotsOn = true;
                    if (s2lGen != gen) break;
                    SHTap(0x4F, 8, 0); // Preset 1
                    Thread.Sleep(300);
                    Log("S2L LICHT: MH + Spots aktiviert, Preset 1 gesetzt");
                }}

                string activeCtx = s2lMode == 1 ? s2lLichtCtx : s2lCtx;
                string modeLabel = s2lMode == 1 ? "S2L\u266bLicht" : "S2L";
                if (activeCtx != null) SetTtl(activeCtx, modeLabel + "\\n[ AN ]");
                s2lShowStart = DateTime.Now;

                // ============ AUDIO-REACTIVE LOOP ============
                int fftPos = 0;
                s2lSpeedLevel = 24; // Nach PRE-RIDE: 4 Platte + 20 Kreuz = 24 Stufen
                s2lPlattePos = 4;  // PRE-RIDE drückt 4x Platte+ = Position 4
                s2lKreuzPos = 20; // Nur Kreuz variiert
                s2lSchraegActive = false; // Schrägfahrt-Reset
                s2lSpotsOn = true; // Spots nach Start an
                while (s2lGen == gen)
                {{
                    // Countdown pruefen
                    if (s2lDuration > 0)
                    {{
                        int elapsed = (int)(DateTime.Now - s2lShowStart).TotalSeconds;
                        if (elapsed >= s2lDuration) {{ Log("S2L: Show-Zeit abgelaufen (" + s2lDuration + "s)"); break; }}
                    }}
                    Thread.Sleep(20);
                    IntPtr pData; int numFrames; uint dwFlags; long devPos, qpcPos;
                    hr = getBuffer(pCapture, out pData, out numFrames, out dwFlags, out devPos, out qpcPos);
                    if (hr != 0 || numFrames == 0) continue;

                    for (int i = 0; i < numFrames && fftPos < 2048; i++)
                    {{
                        float sample = 0;
                        if (isFloat)
                        {{
                            sample = BitConverter.ToSingle(
                                new byte[] {{
                                    Marshal.ReadByte(pData, i * nBlockAlign),
                                    Marshal.ReadByte(pData, i * nBlockAlign + 1),
                                    Marshal.ReadByte(pData, i * nBlockAlign + 2),
                                    Marshal.ReadByte(pData, i * nBlockAlign + 3)
                                }}, 0);
                        }}
                        else if (is16bit)
                        {{
                            short s16 = (short)(Marshal.ReadByte(pData, i * nBlockAlign) |
                                       (Marshal.ReadByte(pData, i * nBlockAlign + 1) << 8));
                            sample = s16 / 32768f;
                        }}
                        else if (is32bit)
                        {{
                            int s32 = Marshal.ReadInt32(pData, i * nBlockAlign);
                            sample = s32 / 2147483648f;
                        }}
                        fftBuf[fftPos++] = sample;
                    }}

                    releaseBuffer(pCapture, numFrames);

                    if (fftPos >= 2048)
                    {{
                        fftPos = 0;

                        float[] re = new float[2048];
                        float[] im = new float[2048];
                        for (int i = 0; i < 2048; i++)
                        {{
                            float w = 0.5f - 0.5f * (float)Math.Cos(2.0 * Math.PI * i / 2047);
                            re[i] = fftBuf[i] * w;
                            im[i] = 0;
                        }}
                        FFT(re, im, 2048);

                        float binHz = (float)nSamplesPerSec / 2048f;
                        float bass = 0, mid = 0, high = 0, total = 0;
                        int bassN = 0, midN = 0, highN = 0;
                        for (int i = 1; i < 1024; i++)
                        {{
                            float mag = (float)Math.Sqrt(re[i] * re[i] + im[i] * im[i]);
                            float freq = i * binHz;
                            if (freq < 200) {{ bass += mag; bassN++; }}
                            else if (freq < 2000) {{ mid += mag; midN++; }}
                            else {{ high += mag; highN++; }}
                            total += mag;
                        }}
                        if (bassN > 0) bass /= bassN;
                        if (midN > 0) mid /= midN;
                        if (highN > 0) high /= highN;
                        total /= 1023;

                        float alpha = 0.35f; // Balance: schnell genug für Beats, glatt genug gegen Rauschen
                        s2lSmoothedBass = s2lSmoothedBass * (1 - alpha) + bass * alpha;
                        s2lSmoothedMid = s2lSmoothedMid * (1 - alpha) + mid * alpha;
                        s2lSmoothedHigh = s2lSmoothedHigh * (1 - alpha) + high * alpha;
                        s2lSmoothedEnergy = s2lSmoothedEnergy * (1 - alpha) + total * alpha;

                        // === SONG-WECHSEL ERKENNUNG ===
                        // Stille erkennen (z.B. Pause zwischen Songs)
                        if (s2lSmoothedEnergy < 0.005f)
                        {{
                            s2lSilenceFrames++;
                            if (s2lSilenceFrames >= 15 && !s2lSongTransition)  // ~0.75s Stille = Song-Wechsel
                            {{
                                s2lSongTransition = true;
                                Log("S2L: SONG-WECHSEL erkannt (Stille seit " + s2lSilenceFrames + " Frames)");
                            }}
                        }}
                        else
                        {{
                            if (s2lSongTransition)
                            {{
                                // Neuer Song beginnt! History komplett resetten für saubere Normalisierung
                                s2lSongTransition = false;
                                s2lTransitionFrames = 0;
                                s2lPeakHistory.Clear();
                                s2lBassHistory.Clear();
                                s2lMidHistory.Clear();
                                s2lHighHistory.Clear();
                                s2lEnergyHistory.Clear();
                                // Averages sofort auf aktuelle Werte setzen (kein Verzögerung!)
                                s2lAvgBass = s2lSmoothedBass;
                                s2lAvgMid = s2lSmoothedMid;
                                s2lAvgHigh = s2lSmoothedHigh;
                                s2lAvgEnergy = s2lSmoothedEnergy;
                                s2lAvgPeak = s2lSmoothedEnergy;
                                s2lPeakEnergy = s2lSmoothedEnergy;
                                Log("S2L: NEUER SONG! Averages resettet auf aktuelle Werte (E=" + s2lSmoothedEnergy.ToString("F4") + " B=" + s2lSmoothedBass.ToString("F4") + ")");
                            }}
                            s2lSilenceFrames = 0;
                            if (s2lTransitionFrames < 60) s2lTransitionFrames++;  // Zähle erste 3s nach Songwechsel
                        }}

                        if (s2lSmoothedEnergy > s2lPeakEnergy)
                            s2lPeakEnergy = s2lSmoothedEnergy;
                        else
                            s2lPeakEnergy = s2lPeakEnergy * 0.93f;

                        // === ADAPTIVE SCHWELLEN-ANPASSUNG ===
                        // Kurzzeit-History (100 Frames = ~5s) für Beat-Detection
                        s2lPeakHistory.Enqueue(s2lPeakEnergy);
                        if (s2lPeakHistory.Count > 100) s2lPeakHistory.Dequeue();
                        if (s2lPeakHistory.Count > 0)
                        {{ float sum = 0; foreach (float p in s2lPeakHistory) sum += p; s2lAvgPeak = sum / s2lPeakHistory.Count; }}
                        else s2lAvgPeak = 0.5f;
                        
                        s2lBassHistory.Enqueue(s2lSmoothedBass);
                        if (s2lBassHistory.Count > 100) s2lBassHistory.Dequeue();
                        if (s2lBassHistory.Count > 0)
                        {{ float sum = 0; foreach (float b in s2lBassHistory) sum += b; s2lAvgBass = sum / s2lBassHistory.Count; }}
                        else s2lAvgBass = 0.5f;
                        
                        s2lMidHistory.Enqueue(s2lSmoothedMid);
                        if (s2lMidHistory.Count > 100) s2lMidHistory.Dequeue();
                        if (s2lMidHistory.Count > 0)
                        {{ float sum = 0; foreach (float m in s2lMidHistory) sum += m; s2lAvgMid = sum / s2lMidHistory.Count; }}
                        else s2lAvgMid = 0.5f;
                        
                        s2lHighHistory.Enqueue(s2lSmoothedHigh);
                        if (s2lHighHistory.Count > 100) s2lHighHistory.Dequeue();
                        if (s2lHighHistory.Count > 0)
                        {{ float sum = 0; foreach (float h in s2lHighHistory) sum += h; s2lAvgHigh = sum / s2lHighHistory.Count; }}
                        else s2lAvgHigh = 0.5f;
                        
                        s2lEnergyHistory.Enqueue(s2lSmoothedEnergy);
                        if (s2lEnergyHistory.Count > 100) s2lEnergyHistory.Dequeue();
                        if (s2lEnergyHistory.Count > 0)
                        {{ float sum = 0; foreach (float e in s2lEnergyHistory) sum += e; s2lAvgEnergy = sum / s2lEnergyHistory.Count; }}
                        else s2lAvgEnergy = 0.5f;

                        // === LANGZEIT-HISTORY für Stimmungs-Erkennung (~25s) ===
                        s2lLongBassHistory.Enqueue(s2lSmoothedBass);
                        if (s2lLongBassHistory.Count > 500) s2lLongBassHistory.Dequeue();
                        if (s2lLongBassHistory.Count > 20)
                        {{ float sum = 0; foreach (float b in s2lLongBassHistory) sum += b; s2lLongAvgBass = sum / s2lLongBassHistory.Count; }}
                        
                        s2lLongEnergyHistory.Enqueue(s2lSmoothedEnergy);
                        if (s2lLongEnergyHistory.Count > 500) s2lLongEnergyHistory.Dequeue();
                        if (s2lLongEnergyHistory.Count > 20)
                        {{ float sum = 0; foreach (float e in s2lLongEnergyHistory) sum += e; s2lLongAvgEnergy = sum / s2lLongEnergyHistory.Count; }}

                        // === STIMMUNGS-ERKENNUNG ===
                        // Bass-Ratio = wie viel vom gesamten Signal ist Bass?
                        float bassRatio = (s2lAvgEnergy > 0.001f) ? s2lLongAvgBass / s2lLongAvgEnergy : 0f;
                        int prevMood = s2lMood;
                        if (s2lLongAvgEnergy < 0.01f || bassRatio < 0.3f)
                            s2lMood = 0;  // CHILL: Wenig Gesamtenergie ODER wenig Bass-Anteil
                        else if (bassRatio > 0.6f && s2lLongAvgEnergy > 0.03f)
                            s2lMood = 2;  // PARTY: Hoher Bass-Anteil + viel Energie
                        else
                            s2lMood = 1;  // NORMAL
                        if (prevMood != s2lMood)
                            Log("S2L MOOD: " + (s2lMood == 0 ? "CHILL" : s2lMood == 1 ? "NORMAL" : "PARTY") + " (bassRatio=" + bassRatio.ToString("F2") + " longE=" + s2lLongAvgEnergy.ToString("F4") + ")");
                        
                        float sensScale = s2lSensitivity / 50f;
                        
                        // === PER-BAND NORMALISIERUNG ===
                        float normBass = Math.Min(1f, (s2lSmoothedBass / Math.Max(0.05f, s2lAvgBass * 1.3f)) * sensScale);
                        float normMid = Math.Min(1f, (s2lSmoothedMid / Math.Max(0.05f, s2lAvgMid * 1.3f)) * sensScale);
                        float normHigh = Math.Min(1f, (s2lSmoothedHigh / Math.Max(0.05f, s2lAvgHigh * 1.3f)) * sensScale);
                        float normEnergy = Math.Min(1f, (s2lSmoothedEnergy / Math.Max(0.05f, s2lAvgEnergy * 1.3f)) * sensScale);
                        
                        // === MOOD-ABHÄNGIGE SCHWELLEN ===
                        // CHILL: höhere Schwellen → weniger Effekte, mehr Seifenblasen/Spots
                        // PARTY: niedrigere Schwellen → mehr Feuer, Strobo, Nebel
                        float nebelThresh_bass, nebelThresh_energy, flammeThresh;
                        if (s2lMood == 0) // CHILL
                        {{
                            nebelThresh_bass = 0.80f;    // Nebel nur bei extremem Bass
                            nebelThresh_energy = 0.65f;
                            flammeThresh = 0.75f;        // Flamme fast nie
                        }}
                        else if (s2lMood == 2) // PARTY
                        {{
                            nebelThresh_bass = 0.55f;    // Nebel häufiger
                            nebelThresh_energy = 0.40f;
                            flammeThresh = 0.45f;        // Flamme häufiger
                        }}
                        else // NORMAL
                        {{
                            nebelThresh_bass = 0.65f;
                            nebelThresh_energy = 0.50f;
                            flammeThresh = 0.55f;
                        }}

                        // Status logging every 10 FFT frames (~500ms)
                        if (s2lFrameCount++ % 10 == 0)
                        {{
                            string moodStr = s2lMood == 0 ? "CHILL" : s2lMood == 1 ? "NORM" : "PARTY";
                            Log("S2L STATUS: B=" + normBass.ToString("F2") + " M=" + normMid.ToString("F2") + " H=" + normHigh.ToString("F2") + " E=" + normEnergy.ToString("F2") + " | avgB=" + s2lAvgBass.ToString("F2") + " avgE=" + s2lAvgEnergy.ToString("F2") + " | MOOD=" + moodStr + " bR=" + bassRatio.ToString("F2"));
                        }}

                        // === EFFEKT-ENTSCHEIDUNGEN ===

                        // === DELTA-BERECHNUNG für bessere Transient-Detection ===
                        s2lDeltaBass = normBass - s2lLastBass;
                        s2lDeltaMid = normMid - s2lLastMid;
                        s2lDeltaHigh = normHigh - s2lLastHigh;
                        s2lDeltaEnergy = normEnergy - s2lLastEnergy;
                        // Speichere aktuelle Werte für nächste Frame
                        s2lLastBass = normBass;
                        s2lLastMid = normMid;
                        s2lLastHigh = normHigh;
                        s2lLastEnergy = normEnergy;

                        // KEIN Preset-System mehr! Presets überschreiben die einzelnen Effekte.
                        // Preset 1 wird nur beim Start + Stop gesetzt, alles andere bauen wir selbst.

                        // 2) Titel-Anzeige auf Stream Deck (Countdown + Level)
                        string level = "";
                        if (normEnergy < 0.2f) level = "\\u2581";
                        else if (normEnergy < 0.4f) level = "\\u2582\\u2583";
                        else if (normEnergy < 0.6f) level = "\\u2584\\u2585";
                        else if (normEnergy < 0.8f) level = "\\u2586\\u2587";
                        else level = "\\u2588\\u2588";
                        if (s2lCtx != null || s2lLichtCtx != null)
                        {{
                            string dCtx = s2lMode == 1 ? s2lLichtCtx : s2lCtx;
                            string dLbl = s2lMode == 1 ? "S2L\u266b" : "S2L";
                            if (dCtx != null)
                            {{
                                if ((DateTime.Now - s2lLastDeckTitleUpdate).TotalMilliseconds >= 250)
                                {{
                                    s2lLastDeckTitleUpdate = DateTime.Now;
                                    if (s2lDuration > 0)
                                    {{
                                        int rem = s2lDuration - (int)(DateTime.Now - s2lShowStart).TotalSeconds;
                                        if (rem < 0) rem = 0;
                                        int rm = rem / 60; int rs = rem % 60;
                                        SetTtl(dCtx, dLbl + "\\n" + rm + ":" + rs.ToString("D2") + "\\n" + level);
                                    }}
                                    else
                                        SetTtl(dCtx, dLbl + "\\n" + level);
                                }}
                            }}
                        }}

                        if (s2lStrobo || s2lFog || s2lFlame || s2lLED || s2lLight1 || s2lLight2 || s2lLight3 || s2lLight4 || s2lLight5 || s2lLight6 || s2lLight7 || s2lLight8 || s2lLight9 || s2lColorStrobe || s2lSpot)
                        {{
                            // 1+2) BASS -> STROBO + ALLE Lichter (KOMBINIERT um Race Conditions zu vermeiden!)
                            // Starker Bass-Peak = kurzer Flash (150ms), Sustained Bass = langer Hold (1200ms)
                            // MOOD: PARTY = kürzerer Cooldown (1800ms), CHILL = längerer (3500ms)
                            int stroboCooldown = s2lMood == 2 ? 1800 : s2lMood == 0 ? 3500 : 2500;
                            bool bassPeak = (normBass > 0.70f || (normBass > 0.55f && s2lDeltaBass > 0.05f)) && bass > s2lSmoothedBass * 1.3f;
                            bool bassFest = normBass > 0.75f && normEnergy > 0.55f;
                            if ((bassPeak || bassFest) && (DateTime.Now - s2lLastStrobo).TotalMilliseconds > stroboCooldown * nightMul)
                            {{
                                int holdMs = bassFest ? 1200 : 150;  // Sustained Bass = langer Hold (Priorität!), Peak-only = kurzer Flash
                                string trigName = bassFest ? "BASS FEST" : "BASS PEAK";
                                int pat = s2lLedPattern;
                                s2lLedPattern = (s2lLedPattern + 1) % 4;  // Nächstes Pattern für nächsten Trigger
                                Log("S2L TRIGGER " + trigName + ": normBass=" + normBass.ToString("F2") + " normEnergy=" + normEnergy.ToString("F2") + " hold=" + holdMs + "ms pat=" + pat);
                                s2lLastStrobo = DateTime.Now;
                                s2lLastFX = DateTime.Now;
                                int fg2 = gen;
                                // LED Arrays für Welleneffekte
                                byte[] oddLeds = {{ 0x02, 0x04, 0x06, 0x08, 0x0A }};  // 1,3,5,7,9
                                byte[] evenLeds = {{ 0x03, 0x05, 0x07, 0x09 }};        // 2,4,6,8
                                byte[] allLeds = {{ 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A }};
                                bool[] lightEnabled = {{ s2lLight1, s2lLight2, s2lLight3, s2lLight4, s2lLight5, s2lLight6, s2lLight7, s2lLight8, s2lLight9 }};
                                int patL = pat; // Capture für Thread
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    if (s2lStrobo) keybd_event(0, 0x39, 8u, UIntPtr.Zero);
                                    if (s2lLED) keybd_event(0, 0x0C, 8u, UIntPtr.Zero);
                                    if (patL == 0 || bassFest)  // ALLE gleichzeitig (bei Bass Fest IMMER alle!)
                                    {{
                                        for (int li = 0; li < 9; li++) {{ if (lightEnabled[li]) keybd_event(0, allLeds[li], 8u, UIntPtr.Zero); }}
                                        for (int w = 0; w < holdMs && s2lGen == fg2; w += 50) Thread.Sleep(50);
                                        for (int li = 0; li < 9; li++) {{ if (lightEnabled[li]) keybd_event(0, allLeds[li], 8u | 2u, UIntPtr.Zero); }}
                                    }}
                                    else if (patL == 1)  // UNGERADE: 1,3,5,7,9
                                    {{
                                        foreach (byte led in oddLeds) keybd_event(0, led, 8u, UIntPtr.Zero);
                                        for (int w = 0; w < holdMs && s2lGen == fg2; w += 50) Thread.Sleep(50);
                                        foreach (byte led in oddLeds) keybd_event(0, led, 8u | 2u, UIntPtr.Zero);
                                    }}
                                    else if (patL == 2)  // GERADE: 2,4,6,8
                                    {{
                                        foreach (byte led in evenLeds) keybd_event(0, led, 8u, UIntPtr.Zero);
                                        for (int w = 0; w < holdMs && s2lGen == fg2; w += 50) Thread.Sleep(50);
                                        foreach (byte led in evenLeds) keybd_event(0, led, 8u | 2u, UIntPtr.Zero);
                                    }}
                                    else  // CHASE: Sequentiell 1→9 (schnell)
                                    {{
                                        int chaseMs = Math.Max(40, holdMs / 9);  // Aufteilen auf 9 LEDs
                                        for (int li = 0; li < 9 && s2lGen == fg2; li++)
                                        {{
                                            if (lightEnabled[li])
                                            {{
                                                keybd_event(0, allLeds[li], 8u, UIntPtr.Zero);
                                                Thread.Sleep(chaseMs);
                                                keybd_event(0, allLeds[li], 8u | 2u, UIntPtr.Zero);
                                            }}
                                        }}
                                    }}
                                    if (s2lStrobo) keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero);
                                    if (s2lLED) keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero);
                                }});
                            }}

                            // 3) BASS EXTREM HOCH -> NEBEL - nur bei echten Peaks über Durchschnitt
                            if (normBass > nebelThresh_bass && normEnergy > nebelThresh_energy && (DateTime.Now - s2lLastNebel).TotalMilliseconds > 8000)
                            {{
                                Log("S2L TRIGGER NEBEL: normBass=" + normBass.ToString("F2") + " normEnergy=" + normEnergy.ToString("F2") + " (thresh=" + nebelThresh_bass.ToString("F2") + ", avgPeak=" + s2lAvgPeak.ToString("F2") + ")");
                                if (s2lFog) 
                                {{
                                    S2LDoEffect(0x20, 8, 2000, ref s2lLastNebel, 8000, "Nebel");  // 2s Hold, 8s Cooldown
                                }}
                            }}

                            // 4) ENERGY SEHR HOCH -> FLAMME (mit kleineren Delta-Werten!) - AUTOMATISIERT mit meheren Trigger-Optionen - OPTIMIERT
                            if (s2lFlame && !s2lNightMode && normEnergy > flammeThresh && normBass > 0.50f && (DateTime.Now - s2lLastFlamme).TotalMilliseconds > 8000)
                            {{
                                Log("S2L TRIGGER FLAMME: normEnergy=" + normEnergy.ToString("F2") + " (thresh=" + flammeThresh.ToString("F2") + ", avgPeak=" + s2lAvgPeak.ToString("F2") + ")");
                                S2LDoEffect(0x2E, 8, 2500, ref s2lLastFlamme, 8000, "Flamme");  // 2.5s Hold, 8s Cooldown
                            }}

                            // 6) HIGH PEAK + ENERGY -> FARBSTROBOSKOP
                            if (s2lColorStrobe && normHigh > 0.60f && normEnergy > 0.35f)
                            {{
                                if ((DateTime.Now - s2lLastFarbstrob).TotalMilliseconds > 3000 * nightMul)
                                {{
                                    s2lLastFarbstrob = DateTime.Now;
                                    Log("S2L: Farbstroboskop (normHigh=" + normHigh.ToString("F2") + ")");
                                    int fg = gen;
                                    ThreadPool.QueueUserWorkItem(_ => {{
                                        SHTap(0x1E, 8, 0x2A);
                                        Thread.Sleep(150);
                                        for (int w = 0; w < 2000 && s2lGen == fg; w += 50) Thread.Sleep(50);
                                        SHTap(0x1E, 8, 0x2A);
                                    }});
                                }}
                            }}

                            // 6b) HIGH PEAK -> LED STROBE EXTRA - NUR wenn Strobo-Block nicht gerade aktiv!
                            if (s2lLED && normHigh > 0.65f && (DateTime.Now - s2lLastLEDStrobe).TotalMilliseconds > 2000 && (DateTime.Now - s2lLastStrobo).TotalMilliseconds > 2500)
                            {{
                                s2lLastLEDStrobe = DateTime.Now;
                                Log("S2L: LED-Strobe (normHigh=" + normHigh.ToString("F2") + ")");
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    keybd_event(0, 0x0C, 8u, UIntPtr.Zero);
                                    Thread.Sleep(400);
                                    keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero);
                                }});
                            }}

                            // 7) RUHIGE PASSAGES -> SEIFENBLASEN (quiet moments)
                            // MOOD: CHILL = häufiger (5s), PARTY = seltener (12s)
                            int bubbleCooldown = s2lMood == 0 ? 5000 : s2lMood == 2 ? 12000 : 8000;
                            if (normEnergy < 0.3f)
                            {{
                                if ((DateTime.Now - s2lLastBubble).TotalMilliseconds > bubbleCooldown * nightMul)
                                {{
                                    Log("S2L TRIGGER SEIFENBLASEN: normEnergy=" + normEnergy.ToString("F2"));
                                    s2lLastBubble = DateTime.Now;
                                    int bg = gen;
                                    ThreadPool.QueueUserWorkItem(_ => {{
                                        keybd_event(0, 0x1D, 8u, UIntPtr.Zero);
                                        keybd_event(0, 0x2E, 8u, UIntPtr.Zero);
                                        Thread.Sleep(200);
                                        keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero);
                                        keybd_event(0, 0x1D, 8u | 2u, UIntPtr.Zero);
                                        Thread.Sleep(2500);
                                        if (s2lGen != bg) return;
                                        keybd_event(0, 0x1D, 8u, UIntPtr.Zero);
                                        keybd_event(0, 0x2E, 8u, UIntPtr.Zero);
                                        Thread.Sleep(200);
                                        keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero);
                                        keybd_event(0, 0x1D, 8u | 2u, UIntPtr.Zero);
                                    }});
                                }}
                            }}

                            // === AUTOSHOW-FEATURES (aus AutoShow portiert!) ===
                            // NUR im Komplett-Modus (nicht im Licht-Modus!)
                            if (s2lMode == 0)
                            {{

                            // 10) SCHRÄGFAHRT - NUR KREUZ bremst! (Platte bleibt IMMER!)
                            // Max 3 Stufen, kurze Zeiten, Sicherheits-Clamp!
                            if (!s2lSchraegActive && normEnergy > 0.75f && normBass > 0.60f 
                                && (DateTime.Now - s2lLastSchraeg).TotalMilliseconds > 45000 
                                && s2lKreuzPos >= 16)
                            {{
                                s2lSchraegActive = true;
                                s2lLastSchraeg = DateTime.Now;
                                int brakeSteps = Math.Min(3, s2lKreuzPos - 12);  // NIE unter Kreuz=12! Max 3 Stufen!
                                if (brakeSteps < 2) brakeSteps = 2;
                                Log("S2L: SCHRÄGFAHRT START! Kreuz bremst " + brakeSteps + " Stufen (Pos " + s2lKreuzPos + " -> " + (s2lKreuzPos - brakeSteps) + ")");
                                int sg = gen;
                                int bs = brakeSteps;
                                int startKreuz = s2lKreuzPos;
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    try {{
                                        // Phase 1: Kreuz abbremsen (SCHNELL - 800ms pro Stufe)
                                        for (int i = 0; i < bs && s2lGen == sg; i++)
                                        {{
                                            if (s2lKreuzPos <= 12) break;  // SICHERHEIT: nie unter 12!
                                            SHTap(0x22, 8, 0);  // Kreuz-
                                            s2lKreuzPos--;
                                            s2lSpeedLevel--;
                                            Thread.Sleep(800);
                                        }}
                                        Log("S2L: SCHRÄGFAHRT GAP! Kreuz=" + s2lKreuzPos + " Platte=" + s2lPlattePos);
                                        
                                        // Phase 2: Gap halten (NUR 2-3 Sekunden!)
                                        int gapMs = 2000 + s2lRandom.Next(1001);
                                        for (int w = 0; w < gapMs && s2lGen == sg; w += 100) Thread.Sleep(100);
                                        if (s2lGen != sg) {{ s2lSchraegActive = false; return; }}
                                        
                                        // Phase 3: Kreuz zurück (SCHNELL - 600ms pro Stufe)
                                        Log("S2L: SCHRÄGFAHRT ZURÜCK!");
                                        int stepsBack = startKreuz - s2lKreuzPos;  // Exakt so viele wie runter
                                        for (int i = 0; i < stepsBack && s2lGen == sg; i++)
                                        {{
                                            if (s2lKreuzPos >= 20) break;  // SICHERHEIT: nie über 20!
                                            SHTap(0x14, 8, 0);  // Kreuz+
                                            s2lKreuzPos++;
                                            s2lSpeedLevel++;
                                            Thread.Sleep(600);
                                        }}
                                        Log("S2L: SCHRÄGFAHRT ENDE - Kreuz=" + s2lKreuzPos);
                                    }}
                                    catch {{ }}
                                    s2lSchraegActive = false;
                                }});
                            }}

                            // 11) GONDELBREMSE - Physische Bremse (0x31) für dramatischen Effekt!
                            // Häufiger als andere Spezial-Effekte! Cooldown 10s, niedrigere Schwelle
                            if (normBass > 0.65f && normEnergy > 0.50f && !s2lSchraegActive
                                && (DateTime.Now - s2lLastGondelbremse).TotalMilliseconds > 10000 * nightMul
                                && s2lKreuzPos >= 12)
                            {{
                                int brakeMs = 2000 + s2lRandom.Next(3001);  // 2-5 Sekunden
                                Log("S2L: GONDELBREMSE! " + brakeMs + "ms Hold");
                                s2lLastGondelbremse = DateTime.Now;
                                int bg = gen;
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    keybd_event(0, 0x31, 8u, UIntPtr.Zero);  // Gondelbremse AN
                                    for (int w = 0; w < brakeMs && s2lGen == bg; w += 50) Thread.Sleep(50);
                                    keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero);  // Gondelbremse AUS
                                }});
                            }}

                        }} // Ende s2lMode==0 (AutoShow-Features)
                        }}

                        // === EFFEKTE FÜR BEIDE MODI (Alles + Licht) ===

                        // 12) ALLES AN! - Strobo+Nebel+Flamme GLEICHZEITIG (Mega-Moment!)
                        // Nur bei extremen Peaks, sehr langer Cooldown (30s)
                        if (s2lAllEffects && s2lStrobo && s2lFog && s2lFlame
                            && normEnergy > 0.90f && normBass > 0.80f
                            && (DateTime.Now - s2lLastAllesAn).TotalMilliseconds > 30000
                            && !s2lNightMode)
                        {{
                            int holdMs = 3000 + s2lRandom.Next(2001);  // 3-5 Sekunden
                            Log("S2L: *** ALLES AN! *** Strobo+Nebel+Flamme " + holdMs + "ms");
                            s2lLastAllesAn = DateTime.Now;
                            s2lLastStrobo = DateTime.Now;
                            s2lLastNebel = DateTime.Now;
                            s2lLastFlamme = DateTime.Now;
                            s2lLastFX = DateTime.Now;
                            int ag = gen;
                            ThreadPool.QueueUserWorkItem(_ => {{
                                // Gleichzeitig AN!
                                keybd_event(0, 0x39, 8u, UIntPtr.Zero);  // Strobo
                                keybd_event(0, 0x20, 8u, UIntPtr.Zero);  // Nebel
                                keybd_event(0, 0x2E, 8u, UIntPtr.Zero);  // Flamme
                                for (int w = 0; w < holdMs && s2lGen == ag; w += 50) Thread.Sleep(50);
                                // Gleichzeitig AUS!
                                keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero);
                                keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero);
                                keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero);
                            }});
                        }}

                        // 13) DOPPEL-FLAMME - Zwei schnelle Flammen hintereinander
                        if (s2lFlame && !s2lNightMode && normEnergy > 0.70f && normBass > 0.60f
                            && (DateTime.Now - s2lLastDoppelFlamme).TotalMilliseconds > 15000
                            && (DateTime.Now - s2lLastFlamme).TotalMilliseconds > 8000
                            && (DateTime.Now - s2lLastAllesAn).TotalMilliseconds > 5000)
                        {{
                            Log("S2L: DOPPEL-FLAMME!");
                            s2lLastDoppelFlamme = DateTime.Now;
                            s2lLastFlamme = DateTime.Now;
                            s2lLastFX = DateTime.Now;
                            int dg = gen;
                            ThreadPool.QueueUserWorkItem(_ => {{
                                // Erste Flamme: 1.5s
                                keybd_event(0, 0x2E, 8u, UIntPtr.Zero);
                                for (int w = 0; w < 1500 && s2lGen == dg; w += 50) Thread.Sleep(50);
                                keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero);
                                if (s2lGen != dg) return;
                                Thread.Sleep(1500);  // Pause
                                if (s2lGen != dg) return;
                                // Zweite Flamme: 1.5s
                                keybd_event(0, 0x2E, 8u, UIntPtr.Zero);
                                for (int w = 0; w < 1500 && s2lGen == dg; w += 50) Thread.Sleep(50);
                                keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero);
                            }});
                        }}

                        // 14) MH PROGRAMM wechseln - OFT! Hauptquelle für Lichtvariation
                        // Mood-abhängig: PARTY=8s, NORMAL=12s, CHILL=18s
                        {{
                            int mhProgCooldown = s2lMood == 2 ? 8000 : s2lMood == 0 ? 18000 : 12000;
                            if (normEnergy > 0.30f && (DateTime.Now - s2lLastMHProgramm).TotalMilliseconds > mhProgCooldown)
                            {{
                                s2lLastMHProgramm = DateTime.Now;
                                int taps = 1 + s2lRandom.Next(3);  // 1-3 Programmwechsel
                                Log("S2L: MH Programm x" + taps);
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    for (int j = 0; j < taps; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
                                }});
                            }}
                        }}

                        // 15) MH FARBE wechseln - HAUPTEFFEKT! Reagiert auf Melodie
                        // Mood-abhängig: PARTY=5s, NORMAL=8s, CHILL=12s 
                        {{
                            int mhFarbeCooldown = s2lMood == 2 ? 5000 : s2lMood == 0 ? 12000 : 8000;
                            if (normMid > 0.35f && (DateTime.Now - s2lLastMHFarbe).TotalMilliseconds > mhFarbeCooldown)
                            {{
                                s2lLastMHFarbe = DateTime.Now;
                                int taps = 1 + s2lRandom.Next(4);  // 1-4 Farbwechsel (mehr Variation!)
                                // Zufällig vorwärts oder rückwärts
                                bool fwd = s2lRandom.Next(2) == 0;
                                byte mhColorScan = fwd ? (byte)0x12 : (byte)0x20;  // Shift+E=Color+ / Shift+D=Color-
                                Log("S2L: MH Farbe " + (fwd ? "+" : "-") + " x" + taps);
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    for (int j = 0; j < taps; j++) {{ SHTap(mhColorScan, 8, 0x2A); Thread.Sleep(150); }}
                                }});
                            }}
                        }}

                        // 15b) MH GOBO wechseln - BEIDE MODI! Reagiert auf Mid-Peaks
                        // Bidirektional (Shift+T=Gobo+ / Shift+G=Gobo-)
                        {{
                            int goboCooldown = s2lMood == 2 ? 6000 : s2lMood == 0 ? 15000 : 10000;
                            if ((normMid > 0.45f || (normMid > 0.30f && s2lDeltaMid > 0.15f)) 
                                && (DateTime.Now - s2lLastGobo).TotalMilliseconds > goboCooldown)
                            {{
                                s2lLastGobo = DateTime.Now;
                                int taps = 1 + s2lRandom.Next(3);  // 1-3 Gobo-Wechsel
                                bool goboFwd = s2lRandom.Next(2) == 0;
                                byte goboScan = goboFwd ? (byte)0x14 : (byte)0x22;  // Shift+T=Gobo+ / Shift+G=Gobo-
                                Log("S2L: MH Gobo " + (goboFwd ? "+" : "-") + " x" + taps);
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    for (int j = 0; j < taps; j++) {{ SHTap(goboScan, 8, 0x2A); Thread.Sleep(200); }}
                                }});
                            }}
                        }}

                        // 16) MH FARBSTROBOSKOP - Moving Head ColorStrobe (Shift+V = 0x2F+Shift)
                        // ACHTUNG: 0x2F = Platte Tip scancode! Skip wenn P+K Tip aktiv
                        // Mood-abhängig: PARTY=6s, NORMAL=10s, CHILL=15s
                        {{
                            int colorStrobeCooldown = s2lMood == 2 ? 6000 : s2lMood == 0 ? 15000 : 10000;
                            if (!pkTipActive && normHigh > 0.60f && normEnergy > 0.45f 
                                && (DateTime.Now - s2lLastMHColorStrobe).TotalMilliseconds > colorStrobeCooldown)
                            {{
                                s2lLastMHColorStrobe = DateTime.Now;
                                int holdMs = 2000 + s2lRandom.Next(3001);  // 2-5s halten
                                Log("S2L: MH ColorStrobe " + holdMs + "ms");
                                int csg = gen;
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    SHTap(0x2F, 8, 0x2A);  // Shift+V = MH Color Strobe AN
                                    for (int w = 0; w < holdMs && s2lGen == csg; w += 50) Thread.Sleep(50);
                                    SHTap(0x2F, 8, 0x2A);  // Wieder AUS
                                }});
                            }}
                        }}

                        // 17) SCHEINWERFER / SPOT FARBWECHSEL - HAUPTEFFEKT!
                        // Reagiert auf Melodie UND Energy, Mood-abhängig
                        // PARTY=3s, NORMAL=5s, CHILL=8s
                        {{
                            int spotCooldown = s2lMood == 2 ? 3000 : s2lMood == 0 ? 8000 : 5000;
                            if ((normEnergy > 0.40f || normMid > 0.45f) 
                                && (DateTime.Now - s2lLastScheinwerfer).TotalMilliseconds > spotCooldown)
                            {{
                                s2lLastScheinwerfer = DateTime.Now;
                                int taps = 1 + s2lRandom.Next(3);  // 1-3 Farbwechsel
                                bool forward = s2lRandom.Next(2) == 0;
                                byte spotScan = forward ? (byte)0x11 : (byte)0x1F;  // W=0x11, S=0x1F
                                Log("S2L: Spot Farbe " + (forward ? "+" : "-") + " x" + taps);
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    for (int j = 0; j < taps; j++) {{ SHTap(spotScan, 8, 0x2A); Thread.Sleep(200); }}
                                }});
                            }}
                        }}

                        // 18) SPOT BLACKOUT/FLASH - Spots kurz aus und wieder an (Shift+Q Toggle)
                        // Dramatischer Blackout bei ruhigen Momenten oder Flash bei harten Drops
                        if (s2lSpot && (DateTime.Now - s2lLastSpotToggle).TotalMilliseconds > 8000)
                        {{
                            bool doBlackout = false;
                            int blackoutMs = 0;
                            // Variante A: Ruhiger Moment → Spots kurz AUS für Spannung
                            if (s2lSpotsOn && normEnergy < 0.25f && normBass < 0.20f)
                            {{
                                doBlackout = true;
                                blackoutMs = 2000 + s2lRandom.Next(2001);  // 2-4s dunkel
                                Log("S2L: SPOT BLACKOUT " + blackoutMs + "ms (Ruhemoment)");
                            }}
                            // Variante B: Bass-Drop → blitzschneller Flash (kurz aus, sofort an)
                            else if (s2lSpotsOn && normBass > 0.75f && normEnergy > 0.70f && s2lDeltaBass > 0.25f)
                            {{
                                doBlackout = true;
                                blackoutMs = 300 + s2lRandom.Next(401);  // 300-700ms kurzer Flash
                                Log("S2L: SPOT FLASH " + blackoutMs + "ms (Bass-Drop!)");
                            }}
                            if (doBlackout)
                            {{
                                s2lLastSpotToggle = DateTime.Now;
                                int sg = gen;
                                ThreadPool.QueueUserWorkItem(_ => {{
                                    SHTap(0x10, 8, 0x2A);  // Spots AUS (Shift+Q toggle)
                                    s2lSpotsOn = false;
                                    for (int w = 0; w < blackoutMs && s2lGen == sg; w += 50) Thread.Sleep(50);
                                    if (s2lGen != sg) return;
                                    SHTap(0x10, 8, 0x2A);  // Spots wieder AN
                                    s2lSpotsOn = true;
                                }});
                            }}
                        }}

                        // 18b) MH LIGHT SYNC Toggle - Synchronisiert MH mit Musik (Shift+C)
                        // Gelegentlich für ein paar Sekunden aktivieren
                        if (normEnergy > 0.60f && normBass > 0.50f
                            && (DateTime.Now - s2lLastLightSync).TotalMilliseconds > 20000)
                        {{
                            int syncMs = 3000 + s2lRandom.Next(5001);  // 3-8s halten
                            Log("S2L: MH LightSync " + syncMs + "ms");
                            s2lLastLightSync = DateTime.Now;
                            int lsg = gen;
                            ThreadPool.QueueUserWorkItem(_ => {{
                                SHTap(0x2E, 8, 0x2A);  // Shift+C = MH Light Sync AN
                                for (int w = 0; w < syncMs && s2lGen == lsg; w += 50) Thread.Sleep(50);
                                SHTap(0x2E, 8, 0x2A);  // Wieder AUS
                            }});
                        }}

                        // 9) PLATTE + KREUZ zur Musik (dynamisch statt festgefahren)
                        // NICHT im Licht-Modus! NICHT während Schrägfahrt!
                        if (s2lMode == 0 && !s2lSchraegActive && (DateTime.Now - s2lLastSpeedChange).TotalMilliseconds > 4500)
                        {{
                            // Ziel Platte: STUFIG 2-4
                            int targetPlatte = 2;
                            if (normEnergy > 0.30f) targetPlatte = 3;
                            if (normEnergy > 0.55f) targetPlatte = 4;

                            // Ziel Kreuz: STUFIG 10-14-16-20 - Party-Musik soll 100% erreichen!
                            int targetKreuz = 10;  // MINIMUM: 50% (langsame Fahrt)
                            if (normEnergy > 0.20f) targetKreuz = 14;  // 70% (mittlere Fahrt)
                            if (normEnergy > 0.40f) targetKreuz = 16;  // 80% (schnelle Fahrt)
                            if (normEnergy > 0.55f) targetKreuz = 20;  // 100% (Vollgas!) 
                            
                            // Hysterese: Bleib eine Stufe länger als sonst
                            if (targetKreuz < s2lKreuzPos && (s2lKreuzPos - targetKreuz) <= 2)
                                targetKreuz = s2lKreuzPos;  // Kleine Unterschiede ignorieren

                            // AUTOMATISCHE GONDEL-PAUSEN: Motor kurz stoppen für dramatische Effekt
                            bool kreuzMotorActive = true;
                            if (s2lKreuzMotorPauseEnabled)
                            {{
                                // Prüfe ob Pause zu Ende ist
                                if (DateTime.Now >= s2lKreuzMotorPausedUntil)
                                    s2lKreuzMotorPausedUntil = DateTime.MinValue;
                                
                                // Motor gerade pausiert?
                                if (DateTime.Now < s2lKreuzMotorPausedUntil)
                                {{
                                    kreuzMotorActive = false;
                                    s2lLastSpeedChange = DateTime.Now;  // Verhindert dass dieser Block jeden Frame läuft
                                    if (!s2lGondelPauseLogged)
                                    {{
                                        Log("S2L: GONDEL-PAUSE START (Motor AUS)");
                                        s2lGondelPauseLogged = true;
                                    }}
                                }}
                                // Zufällige neue Pause starten?
                                else if (DateTime.Now >= s2lNextKreuzMotorPause && s2lRandom.Next(100) < 15)  // 15% Chance mit globalem Random!
                                {{
                                    s2lGondelPauseLogged = false;  // Reset für nächste Pause
                                    s2lKreuzMotorPausedUntil = DateTime.Now.AddSeconds(2 + s2lRandom.Next(2));  // 2-3 Sekunden pause
                                    s2lNextKreuzMotorPause = DateTime.Now.AddSeconds(12 + s2lRandom.Next(8));  // Nächste in 12-20 Sekunden
                                    Log("S2L: Gondel-Pause geplant für nächsten Trigger!");
                                }}
                            }}

                            // PLATTE anpassen
                            if (targetPlatte > s2lPlattePos && s2lPlattePos < 4)
                            {{
                                // Platte schneller
                                s2lPlattePos++;
                                s2lSpeedLevel++;
                                s2lLastSpeedChange = DateTime.Now;
                                Log("S2L: Platte+ -> " + s2lPlattePos + " (Kreuz: " + s2lKreuzPos + " | Total " + s2lSpeedLevel + ")");
                                ThreadPool.QueueUserWorkItem(_ => SHTap(0x13, 8, 0));
                            }}
                            else if (targetPlatte < s2lPlattePos && s2lPlattePos > 2)
                            {{
                                // Platte langsamer
                                s2lPlattePos--;
                                s2lSpeedLevel--;
                                s2lLastSpeedChange = DateTime.Now;
                                Log("S2L: Platte- -> " + s2lPlattePos + " (Kreuz: " + s2lKreuzPos + " | Total " + s2lSpeedLevel + ")");
                                ThreadPool.QueueUserWorkItem(_ => SHTap(0x21, 8, 0));
                            }}

                            // KREUZ anpassen (parallel!) - aber NUR wenn Motor aktiv ist
                            if (kreuzMotorActive)
                            {{
                                if (targetKreuz > s2lKreuzPos && s2lKreuzPos < 20)
                                {{
                                    // Kreuz hoch
                                    s2lKreuzPos++;
                                    s2lSpeedLevel++;
                                    s2lLastSpeedChange = DateTime.Now;
                                    Log("S2L: Kreuz+ -> " + s2lKreuzPos + " (Platte: " + s2lPlattePos + " | Total " + s2lSpeedLevel + ")");
                                    ThreadPool.QueueUserWorkItem(_ => SHTap(0x14, 8, 0));
                                }}
                                else if (targetKreuz < s2lKreuzPos && s2lKreuzPos > 10)
                                {{
                                    // Kreuz runter
                                    s2lKreuzPos--;
                                    s2lSpeedLevel--;
                                    s2lLastSpeedChange = DateTime.Now;
                                    Log("S2L: Kreuz- -> " + s2lKreuzPos + " (Platte: " + s2lPlattePos + " | Total " + s2lSpeedLevel + ")");
                                    ThreadPool.QueueUserWorkItem(_ => SHTap(0x22, 8, 0));
                                }}
                            }}
                        }}
                    }}
                }}

                // ============ POST-RIDE ============
                if (s2lMode == 0)
                {{
                    Log("S2L: POST-RIDE");

                    if (s2lCtx != null) SetTtl(s2lCtx, "S2L\\nBremsen!");
                    // Platte runter auf 0 (je nachdem wo sie gerade ist)
                    for (int br = 0; br < s2lPlattePos; br++)
                    {{
                        SHTap(0x21, 8, 0); // Platte- (f)
                        Thread.Sleep(100);
                    }}
                    Thread.Sleep(200);
                    // Nur noch Kreuz-Position runter
                    for (int br = 0; br < s2lKreuzPos; br++)
                    {{
                        SHTap(0x22, 8, 0); // Kreuz- (g)
                        Thread.Sleep(100);
                    }}
                    Thread.Sleep(500);

                    // Stopp - GLEICHZEITIG aus
                    if (s2lCtx != null) SetTtl(s2lCtx, "S2L\\nStopp");
                    keybd_event(0, 0x24, 8u, UIntPtr.Zero); // Kreuz OFF runter
                    keybd_event(0, 0x16, 8u, UIntPtr.Zero); // Teller OFF runter
                    Thread.Sleep(400);
                    keybd_event(0, 0x24, 8u | 2u, UIntPtr.Zero); // Kreuz OFF hoch
                    keybd_event(0, 0x16, 8u | 2u, UIntPtr.Zero); // Teller OFF hoch
                    Thread.Sleep(500);
                    if (pkTipWasActive) SetPkTip(true); // P+K Tip wiederherstellen (war vorher AN)
                    SHTap(0x4F, 8, 0); // Preset 1
                }}
                else
                {{
                    Log("S2L LICHT: Stopp (keine Fahrt-Steuerung)");
                    SHTap(0x4F, 8, 0); // Preset 1 (Reset auf Standard)
                    Thread.Sleep(200);
                }}
                // Safety releases (IMMER!)
                keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo
                keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel
                keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse
                keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo
                keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero); // Flamme
                Log("S2L: POST-RIDE fertig");

                if (activeCtx != null) SetTtl(activeCtx, modeLabel + "\\nFertig!");
                Thread.Sleep(3000);

                // ============ LOOP ============
                if (s2lLoop)
                {{
                    gen = s2lGen; // Aktuellen Gen akzeptieren
                    int rem = s2lLoopPause;
                    while (rem > 0 && s2lGen == gen)
                    {{
                        if (activeCtx != null) SetTtl(activeCtx, modeLabel + " PAUSE\\n" + rem + "s");
                        if (rem > 10) {{ Thread.Sleep(5000); rem -= 5; }}
                        else {{ Thread.Sleep(1000); rem--; }}
                    }}
                    if (s2lGen == gen)
                    {{
                        Log("S2L: Loop - Neustart");
                        s2lSmoothedBass = 0; s2lSmoothedMid = 0;
                        s2lSmoothedHigh = 0; s2lSmoothedEnergy = 0;
                        s2lPeakEnergy = 0.001f; s2lLastPreset = -1;
                        s2lPeakHistory.Clear(); s2lBassHistory.Clear(); s2lMidHistory.Clear(); s2lHighHistory.Clear(); s2lEnergyHistory.Clear();
                        s2lAvgPeak = 0.5f; s2lAvgBass = 0.5f; s2lAvgMid = 0.5f; s2lAvgHigh = 0.5f; s2lAvgEnergy = 0.5f;
                        s2lLastBass = 0; s2lLastMid = 0; s2lLastHigh = 0; s2lLastEnergy = 0;
                        doLoop = true;
                    }}
                }}
            }}

            // Finale Safety (falls PRE-RIDE abgebrochen)
            if (s2lMode == 0)
            {{
                keybd_event(0, 0x24, 8u, UIntPtr.Zero); Thread.Sleep(200);
                keybd_event(0, 0x24, 8u | 2u, UIntPtr.Zero);
                keybd_event(0, 0x16, 8u, UIntPtr.Zero); Thread.Sleep(200);
                keybd_event(0, 0x16, 8u | 2u, UIntPtr.Zero);
            }}
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero);
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero);
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero);
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero);
            keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero);

            // Audio Stop
            var stopAC = Marshal.GetDelegateForFunctionPointer<StartStopDelegate>(
                Marshal.ReadIntPtr(acVtbl, 11 * IntPtr.Size));
            stopAC(pAudioClient);
            Log("S2L: Capture gestoppt");
        }}
        catch (Exception ex) {{ Log("S2L FEHLER: " + ex.ToString()); }}
        finally
        {{
            s2lRunning = false;
            if (s2lCtx != null) {{ SetTtl(s2lCtx, "S2L\\n[ AUS ]"); SetImg(s2lCtx, false); }}
            if (s2lLichtCtx != null) {{ SetTtl(s2lLichtCtx, "S2L\u266bLicht\\n[ AUS ]"); SetImg(s2lLichtCtx, false); }}
            Log("S2L: Thread beendet");
        }}
    }}

    // FFT (Cooley-Tukey Radix-2 DIT)
    static void FFT(float[] re, float[] im, int n)
    {{
        int bits = 0;
        for (int tmp = n; tmp > 1; tmp >>= 1) bits++;
        for (int i = 0; i < n; i++)
        {{
            int j = 0;
            for (int b = 0; b < bits; b++)
                if ((i & (1 << b)) != 0) j |= (1 << (bits - 1 - b));
            if (j > i) {{ float t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; }}
        }}
        for (int size = 2; size <= n; size *= 2)
        {{
            int half = size / 2;
            double angle = -2.0 * Math.PI / size;
            for (int i = 0; i < n; i += size)
            {{
                for (int j = 0; j < half; j++)
                {{
                    float wr = (float)Math.Cos(angle * j);
                    float wi = (float)Math.Sin(angle * j);
                    float tre = wr * re[i + j + half] - wi * im[i + j + half];
                    float tim = wr * im[i + j + half] + wi * re[i + j + half];
                    re[i + j + half] = re[i + j] - tre;
                    im[i + j + half] = im[i + j] - tim;
                    re[i + j] += tre;
                    im[i + j] += tim;
                }}
            }}
        }}
    }}

    // COM Delegates fuer WASAPI
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int GetDefaultAudioEndpointDelegate(IntPtr self, int dataFlow, int role, out IntPtr ppDevice);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int ActivateDelegate(IntPtr self, ref Guid iid, uint clsCtx, IntPtr activationParams, out IntPtr ppInterface);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int GetMixFormatDelegate(IntPtr self, out IntPtr ppFormat);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int InitializeDelegate(IntPtr self, int shareMode, uint flags, long bufferDuration, long periodicity, IntPtr pFormat, IntPtr audioSessionGuid);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int GetServiceDelegate(IntPtr self, ref Guid riid, out IntPtr ppv);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int StartStopDelegate(IntPtr self);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int GetBufferDelegate(IntPtr self, out IntPtr ppData, out int numFrames, out uint dwFlags, out long devPos, out long qpcPos);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    delegate int ReleaseBufferDelegate(IntPtr self, int numFrames);

    // === TOUR KONFIGURATION ===
    // 5 Touren (BD) + 3 MegaDance KI-Programme: Effekte werden per Random aus Pools gewaehlt!
    static string[] tourNm = {{ "Klassisch", "Pirouette", "Nebelwand", "Lichtgewitter", "Inferno", "BD Zufall", "MD Prog.1", "MD Prog.2", "MD Prog.3", "MD Zufall" }};
    static bool[] tourKF = {{ true, false, true, false, true }};   // Kreuz bremst zuerst?
    static bool[] tourSB = {{ true, true, true, false, true }};    // Seifenblasen?

    // Effekt-Pools (Mild=Einzeln/LED, Normal=2er Kombos, Nebel/Strobo=Schwerpunkt, Heavy=Alles max)
    static byte[][] fxMild = {{ new byte[]{{0x2E}}, new byte[]{{0x0C}}, new byte[]{{0x0C, 0x2E}} }};
    static byte[][] fxNormal = {{ new byte[]{{0x39, 0x20}}, new byte[]{{0x2E, 0x20}}, new byte[]{{0x0C, 0x2E}}, new byte[]{{0x39, 0x2E}} }};
    static byte[][] fxNebel = {{ new byte[]{{0x20}}, new byte[]{{0x20, 0x2E}}, new byte[]{{0x39, 0x20}}, new byte[]{{0x39, 0x20, 0x2E}} }};
    static byte[][] fxStrobo = {{ new byte[]{{0x39}}, new byte[]{{0x0C}}, new byte[]{{0x39, 0x0C}}, new byte[]{{0x39, 0x2E}} }};
    static byte[][] fxHeavy = {{ new byte[]{{0x39, 0x20, 0x2E}}, new byte[]{{0x39, 0x20}}, new byte[]{{0x20, 0x2E}}, new byte[]{{0x39, 0x2E}} }};

    // Tour -> Pool: Vollgas-Effekte / Mid-Speed-Effekte
    static byte[][][] tourVP = {{ fxNormal, fxNormal, fxNebel, fxStrobo, fxHeavy }};
    static byte[][][] tourMP = {{ fxMild, fxMild, fxMild, fxStrobo, fxNormal }};

    static string FXName(byte[] fx)
    {{
        if (fx.Length >= 3) return "ALLES\\\\nAN!";
        if (fx.Length == 1)
        {{
            switch(fx[0])
            {{
                case 0x20: return "NEBEL!";
                case 0x2E: return "FLAMME!";
                case 0x39: return "STROBO!";
                case 0x0C: return "LED!";
                default: return "FX!";
            }}
        }}
        string a = "", b = "";
        switch(fx[0]) {{ case 0x20: a="NEBEL"; break; case 0x2E: a="FLAMME"; break; case 0x39: a="STROBO"; break; case 0x0C: a="LED"; break; default: a="FX"; break; }}
        switch(fx[1]) {{ case 0x20: b="NEBEL"; break; case 0x2E: b="FLAMME"; break; case 0x39: b="STROBO"; break; case 0x0C: b="LED"; break; default: b="FX"; break; }}
        return a + "+\\\\n" + b + "!";
    }}

    static void PlayFX(byte[] fx, int ms, int gen)
    {{
        SHTitle(FXName(fx));
        if (fx.Length == 1) SHHold(fx[0], 8, ms, gen);
        else SHHoldMulti(fx, 8, ms, gen);
    }}

    static byte[] PickFX(byte[][] pool, Random rng)
    {{
        return pool[rng.Next(pool.Length)];
    }}

    static int EstimateShowCountdownSec(int tour, bool isNight)
    {{
        if (tour >= 6 && tour <= 8)
        {{
            int[] d = {{ 322, 282, 250 }};
            int v = d[tour - 6];
            return isNight ? v * 3 / 5 : v;
        }}
        if (tour == 9)
        {{
            int avg = (322 + 282 + 250) / 3;
            return isNight ? avg * 3 / 5 : avg;
        }}

        bool sb = true;
        if (tour >= 0 && tour <= 4) sb = tourSB[tour];
        return isNight ? (sb ? 200 : 190) : (sb ? 330 : 315);
    }}

    static void RunBDShow(int gen)
    {{
        Random rng = new Random();
        int t = selectedTour;
        if (t == 5) {{ t = rng.Next(5); while (t == lastRandomBD) t = rng.Next(5); lastRandomBD = t; }}
        if (t < 0 || t > 4) t = 0;

        // Nacht-Modus: kuerzere Show (~3 Min statt ~5 Min)
        bool isNight = nightMode;
        if (isNight) Log("AutoShow: NACHT-MODUS aktiv");

        // Nacht-Helfer: Wartezeiten kuerzen (60% bei Nacht, min 500ms)
        Func<int,int> nw = (ms) => isNight && ms >= 2000 ? ms * 3 / 5 : ms;

        // Tour-abhaengige Asymmetrie
        byte brkA = tourKF[t] ? (byte)0x22 : (byte)0x21;  // Kreuz- oder Platte-
        byte accA = tourKF[t] ? (byte)0x14 : (byte)0x13;  // Kreuz+ oder Platte+
        byte brkB = tourKF[t] ? (byte)0x21 : (byte)0x22;  // andere Seite
        byte accB = tourKF[t] ? (byte)0x13 : (byte)0x14;
        string nmA = tourKF[t] ? "Kreuz" : "Platte";
        string nmB = tourKF[t] ? "Platte" : "Kreuz";
        byte[][] vP = tourVP[t]; // Vollgas-Pool
        byte[][] mP = tourMP[t]; // Mid-Pool
        bool sb = tourSB[t];
        int scTotal = 0; // SpotColor Gesamt-Vorschub tracken (Reset auf 7 am Ende)

        // Geschaetzte Tour-Dauer fuer Countdown-Timer
        showCountdownSec = isNight ? (sb ? 200 : 190) : (sb ? 330 : 315);

        try
        {{
            Log("AutoShow BD [" + tourNm[t] + "]: Start (~" + (isNight ? "3" : "5") + " Min)");
            drivePartyMin = 18; drivePartyGap = 8; // Show-Floor: min 75%

            // ============ PHASE 1: START ============
            SHTitle("HUPE!");
            SHHold(0x2C, 8, 1000, gen);
            if (showGen != gen) return;
            // MH: Moving Heads AN + Licht AN
            SHTap(0x2C, 8, 0x2A); Thread.Sleep(200); // MH AN (Shift+Z)
            SHTap(0x2D, 8, 0x2A); Thread.Sleep(200); // MH Licht (Shift+X)
            if (!SHWait(800, gen)) return;

            SHTitle("Start!");
            SHHold(0x15, 8, 400, gen); // Platte AN
            if (showGen != gen) return;
            if (!SHWait(800, gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(300, gen)) return;
            pkTipWasActive = pkTipActive; // Zustand merken
            SetPkTip(false); // P+K Tip AUS - Fahrt laeuft
            if (!SHWait(200, gen)) return;
            SHTap(0x4F, 8, 0); // Preset 1

            // ============ PHASE 2: HOCHFAHREN P+6 K+6 = ~50% ============
            SHTitle("Hochfahren");
            if (!SHWait(3000, gen)) return;
            for (int i = 0; i < 6; i++)
            {{
                SHTap(0x13, 8, 0); Thread.Sleep(500); SHTap(0x14, 8, 0);
                if (!SHWait(2500, gen)) return;
            }}
            SHTap(0x50, 8, 0); // Preset 2
            if (!SHWait(3000, gen)) return;
            // MH + Spot: Farbe wechseln (random)
            int rc2 = rng.Next(1, 4); for (int j = 0; j < rc2; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs2 = rng.Next(1, 4); for (int j = 0; j < rs2; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs2;

            // Warm-up Flamme
            SHTitle("FLAMME!");
            SHHold(0x2E, 8, 1500, gen);
            if (showGen != gen) return;
            if (!SHWait(nw(5000), gen)) return;

            // ============ PHASE 3: SCHNELLER P+5 K+5 = ~73% ============
            SHTitle("Schneller!");
            for (int i = 0; i < 5; i++)
            {{
                SHTap(0x13, 8, 0); Thread.Sleep(500); SHTap(0x14, 8, 0);
                if (!SHWait(nw(2500), gen)) return;
            }}
            SHTap(0x51, 8, 0); // Preset 3
            if (!SHWait(nw(3000), gen)) return;
            // MH: Programm wechseln (random)
            int rp3 = rng.Next(1, 4); for (int j = 0; j < rp3; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rs3 = rng.Next(1, 3); for (int j = 0; j < rs3; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs3;

            // Gondelbremse bei ~73%
            SHTitle("Bremse!");
            SHHold(0x31, 8, nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            // Mid-Speed Effekt (aus Pool!)
            PlayFX(PickFX(mP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            // ============ PHASE 4: VOLLGAS P+4 K+4 = 100%! ============
            SHTitle("VOLLGAS!");
            for (int i = 0; i < 4; i++)
            {{
                SHTap(0x13, 8, 0); Thread.Sleep(500); SHTap(0x14, 8, 0);
                if (!SHWait(nw(2000), gen)) return;
            }}
            SHTap(0x4B, 8, 0); // Preset 4
            if (!SHWait(nw(3000), gen)) return;
            // MH + Spot: Gobo + Farbe + Farbstroboskop (random)
            int rg4 = rng.Next(1, 4); for (int j = 0; j < rg4; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc4 = rng.Next(1, 4); for (int j = 0; j < rc4; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs4 = rng.Next(1, 3); for (int j = 0; j < rs4; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs4;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AN (Shift+A)

            // Vollgas Effekt! (aus Pool!)
            PlayFX(PickFX(vP, rng), nw(4000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AUS (Shift+A)
            // Seifenblasen AN (tour-abhaengig)
            if (sb) {{ SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(4000), gen)) return; }}

            // Noch ein Vollgas Effekt!
            PlayFX(PickFX(vP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            if (sb) SHTap(0x2E, 8, 0x1D); // Seifenblasen AUS
            SHTap(0x4C, 8, 0); // Preset 5
            if (!SHWait(3000, gen)) return;
            // Vollgas-Haltephase: ~20s bei 100% sicherstellen (bes. Nachtmodus)
            if (!SHWait(isNight ? 7000 : 2000, gen)) return;

            // ============ PHASE 5: SCHRAEG 1 - Side A bremst ============
            SHTitle(nmA + "\\\\nbremst!");
            // MH + Spot: Farbe wechseln (random)
            int rc5 = rng.Next(1, 4); for (int j = 0; j < rc5; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs5 = rng.Next(1, 4); for (int j = 0; j < rs5; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs5;
            drivePartyMin = 7; drivePartyGap = 20; // Schraege: Achse darf bis 30% runter
            for (int i = 0; i < 6; i++) {{ SHTap(brkA, 8, 0); if (!SHWait(nw(2000), gen)) return; }}

            SHTitle("40%\\\\nGAP!");
            if (!SHWait(nw(4000), gen)) return;
            SHTap(0x4D, 8, 0); // Preset 6

            // Mid-Effekt waehrend Schraege
            PlayFX(PickFX(mP, rng), nw(2000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            SHTitle("Bremse!");
            SHHold(0x31, 8, nw(6000), gen); // Gondelbremse 6s
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            PlayFX(PickFX(mP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            // ============ PHASE 6: VOLLGAS - Side A zurueck ============
            SHTitle("VOLLGAS!");
            drivePartyMin = 18; drivePartyGap = 8; // Schraege vorbei: Floor zurueck auf 75%
            for (int i = 0; i < 6; i++) {{ SHTap(accA, 8, 0); if (!SHWait(nw(1500), gen)) return; }}

            SHTap(0x47, 8, 0); // Preset 7
            // MH + Spot: Programm + Gobo wechseln (random)
            int rp6 = rng.Next(1, 4); for (int j = 0; j < rp6; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rg6 = rng.Next(1, 4); for (int j = 0; j < rg6; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rs6 = rng.Next(1, 3); for (int j = 0; j < rs6; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs6;
            if (!SHWait(nw(2000), gen)) return;

            // Vollgas Effekte!
            PlayFX(PickFX(vP, rng), nw(5000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            SHTitle("NEBEL!");
            SHHold(0x20, 8, nw(3000), gen);
            if (showGen != gen) return;

            SHTap(0x48, 8, 0); // Preset 8
            if (!SHWait(nw(3000), gen)) return;

            PlayFX(PickFX(mP, rng), nw(2000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            // ============ PHASE 7: SCHRAEG 2 - Side B bremst ============
            SHTitle(nmB + "\\\\nbremst!");
            // MH + Spot: Farbe wechseln (random)
            int rc7 = rng.Next(1, 4); for (int j = 0; j < rc7; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs7 = rng.Next(1, 4); for (int j = 0; j < rs7; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs7;
            drivePartyMin = 7; drivePartyGap = 20; // Schraege: Achse darf bis 30% runter
            for (int i = 0; i < 6; i++) {{ SHTap(brkB, 8, 0); if (!SHWait(nw(2000), gen)) return; }}

            SHTitle("40%\\\\nGAP!");
            if (!SHWait(nw(4000), gen)) return;
            SHTap(0x49, 8, 0); // Preset 9

            SHTitle("Bremse!");
            SHHold(0x31, 8, nw(5000), gen); // Gondelbremse 5s
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            PlayFX(PickFX(mP, rng), nw(4000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            SHTitle("NEBEL!");
            SHHold(0x20, 8, nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            // ============ PHASE 8: MEGA PARTY - Side B zurueck ============
            SHTitle("MEGA\\\\nPARTY!");
            drivePartyMin = 18; drivePartyGap = 8; // Schraege vorbei: Floor zurueck auf 75%
            // MH + Spot: Programm + Gobo + Farbe (Party-random!)
            int rp8 = rng.Next(2, 5); for (int j = 0; j < rp8; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rg8 = rng.Next(1, 4); for (int j = 0; j < rg8; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc8 = rng.Next(1, 4); for (int j = 0; j < rc8; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs8 = rng.Next(1, 4); for (int j = 0; j < rs8; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs8;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AN (Shift+A)
            for (int i = 0; i < 6; i++) {{ SHTap(accB, 8, 0); if (!SHWait(nw(1500), gen)) return; }}

            SHTap(0x4F, 8, 0); // Preset 1 (Cycle!)
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(3000), gen)) return; }}

            // ALLES AN! (immer bei MEGA PARTY)
            SHTitle("ALLES\\\\nAN!");
            SHHoldMulti(new byte[]{{0x39, 0x20, 0x2E}}, 8, nw(4000), gen);
            if (showGen != gen) return;

            SHTap(0x50, 8, 0); // Preset 2
            if (!SHWait(nw(3000), gen)) return;

            SHTitle("Bremse!");
            SHHold(0x31, 8, nw(5000), gen); // Gondelbremse 5s
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            PlayFX(PickFX(vP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(2000), gen)) return; }} // Seifenblasen AUS

            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AUS (Shift+A)
            // Doppel-Flamme
            SHTitle("FLAMME!");
            SHHold(0x2E, 8, 1500, gen);
            if (showGen != gen) return;
            if (!SHWait(1500, gen)) return;
            SHHold(0x2E, 8, 1500, gen);
            if (showGen != gen) return;

            // ============ PHASE 9: SCHRAEG 3 - Side A nochmal ============
            SHTitle(nmA + "\\\\nbremst!");
            // MH + Spot: Gobo + Farbe wechseln (random)
            int rg9 = rng.Next(1, 4); for (int j = 0; j < rg9; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc9 = rng.Next(1, 4); for (int j = 0; j < rc9; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs9 = rng.Next(1, 3); for (int j = 0; j < rs9; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs9;
            drivePartyMin = 7; drivePartyGap = 20; // Schraege: Achse darf bis 30% runter
            for (int i = 0; i < 6; i++) {{ SHTap(brkA, 8, 0); if (!SHWait(nw(1500), gen)) return; }}

            SHTap(0x51, 8, 0); // Preset 3
            SHTitle("40%\\\\nGAP!");
            if (!SHWait(nw(4000), gen)) return;

            PlayFX(PickFX(mP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            SHTitle("Bremse!");
            SHHold(0x31, 8, nw(6000), gen); // Gondelbremse 6s
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            // ============ PHASE 10: FINALE - Side A zurueck ============
            SHTitle("FINALE!");
            drivePartyMin = 18; drivePartyGap = 8; // Schraege vorbei: Floor zurueck auf 75%
            // MH + Spot: ALLES durchschalten (Finale-random!)
            int rp10 = rng.Next(2, 5); for (int j = 0; j < rp10; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rg10 = rng.Next(2, 5); for (int j = 0; j < rg10; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc10 = rng.Next(2, 5); for (int j = 0; j < rc10; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs10 = rng.Next(2, 4); for (int j = 0; j < rs10; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs10;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AN (Shift+A)
            for (int i = 0; i < 6; i++) {{ SHTap(accA, 8, 0); if (!SHWait(nw(1200), gen)) return; }}

            SHTap(0x4B, 8, 0); // Preset 4
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(2000), gen)) return; }}

            // MEGA ALLES! (immer beim Finale)
            SHTitle("MEGA\\\\nALLES!");
            SHHoldMulti(new byte[]{{0x39, 0x20, 0x2E}}, 8, nw(5000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            // Noch ein Vollgas Effekt
            PlayFX(PickFX(vP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            // Nebel Finale
            SHTitle("NEBEL!");
            SHHold(0x20, 8, nw(4000), gen);
            if (showGen != gen) return;

            SHTap(0x4C, 8, 0); // Preset 5
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(2000), gen)) return; }} // Seifenblasen AUS

            // Gondelbremse letzte
            SHTitle("Bremse!");
            SHHold(0x31, 8, nw(6000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AUS (Shift+A)

            if (!autoShowDriveOnly)
            {{
                // ============ PHASE 11: RUNTERBREMSEN P-15 K-15 = 0% SCHNELL! ============
                SHTitle("Bremsen!");
                for (int i = 0; i < 8; i++)
                {{
                    SHTap(0x22, 8, 0); Thread.Sleep(300); SHTap(0x21, 8, 0);
                    if (!SHWait(600, gen)) return;
                }}
                SHTap(0x4D, 8, 0); // Preset 6

                SHTitle("Auslaufen");
                for (int i = 0; i < 7; i++)
                {{
                    SHTap(0x22, 8, 0); Thread.Sleep(300); SHTap(0x21, 8, 0);
                    if (!SHWait(600, gen)) return;
                }}
                if (!SHWait(3000, gen)) return;

                // ============ PHASE 12: STOPP ============
                SHTitle("Stopp");
                SHHold(0x24, 8, 400, gen); // Kreuz AUS
                if (showGen != gen) return;
                if (!SHWait(500, gen)) return;
                SHHold(0x16, 8, 400, gen); // Platte AUS
                if (showGen != gen) return;
                Thread.Sleep(500);
                SHTap(0x4F, 8, 0); // Preset 1
                // SpotColor + Farbstroboskop auf Position 7 zuruecksetzen
                int scReset = (23 - scTotal % 23) % 23;
                for (int j = 0; j < scReset; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(100); }}
                if (!SHWait(3000, gen)) return;
            }}
            else
            {{
                // AUTO DRIVE endet nach der Tour jetzt mit normalem Auto-Stopp (ohne Not-Aus).
                if (!GracefulDriveAutoStop(gen)) return;
            }}

            SHTitle("Fertig!");
            Log("AutoShow BD [" + tourNm[t] + "]: Beendet");
            if (!SHWait(5000, gen)) return;

            if (autoLoop && showGen == gen)
            {{
                int rem = loopPause;
                while (rem > 0 && showGen == gen)
                {{
                    SHTitle("PAUSE " + rem + "s");
                    if (rem > 10) {{ Thread.Sleep(5000); rem -= 5; }}
                    else {{ Thread.Sleep(1000); rem--; }}
                }}
                if (showGen != gen) return;
                Log("AutoLoop: Naechste Show startet");
                RunBDShow(gen);
                return;
            }}

            showRunning = false;
            SHTitle("AUTO\\\\nSHOW");
            SetImg(showCtx, false);
        }}
        catch (Exception ex)
        {{
            Log("AutoShow error: " + ex.Message);
            showRunning = false;
            SHTitle("FEHLER!");
        }}
    }}

    // === MEGADANCE AUTOSHOW (echte KI-Programme) ===
    static void RunMDShow(int gen)
    {{
        Random rng = new Random();
        int t = selectedTour - 6; // Tour 6=Prog1, 7=Prog2, 8=Prog3, 9=Zufall
        if (t >= 3) {{ t = rng.Next(3); while (t == lastRandomMD) t = rng.Next(3); lastRandomMD = t; }}
        if (t < 0 || t > 2) t = 0;

        bool isNight = nightMode;
        if (isNight) Log("AutoShow MD: NACHT-MODUS aktiv");
        Func<int,int> nw = (ms) => isNight && ms >= 2000 ? ms * 3 / 5 : ms;
        int scTotal = 0;

        int[] durations = {{ 322, 282, 250 }};
        showCountdownSec = isNight ? durations[t] * 3 / 5 : durations[t];

        try
        {{
            string pName = "Programm " + (t + 1);
            Log("AutoShow MD [" + pName + "]: Start");
            SHTitle("MD: " + pName);

            // PRE-RIDE: Hupe + MH Setup
            SHTitle("HUPE!");
            SHHold(0x2C, 8, 1000, gen);
            if (showGen != gen) return;
            SHTap(0x2C, 8, 0x2A); Thread.Sleep(200); // MH AN
            SHTap(0x2D, 8, 0x2A); Thread.Sleep(200); // MH Licht AN
            if (!SHWait(800, gen)) return;

            SHTitle("Start!");
            SHHold(0x15, 8, 400, gen); // Teller ON
            if (showGen != gen) return;
            if (!SHWait(500, gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(300, gen)) return;
            pkTipWasActive = pkTipActive; // Zustand merken
            SetPkTip(false); // P+K Tip AUS - Fahrt laeuft
            if (!SHWait(200, gen)) return;
            SHTap(0x4F, 8, 0); // Preset 1

            if (t == 0) // PROGRAMM 1 (5:22)
            {{
            if (!SHWait(nw(2801), gen)) return;
            for (int i = 0; i < 2; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(735), gen)) return;
            for (int i = 0; i < 2; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(4000), gen)) return;
            SHTitle("FLAMME!"); SHHold(0x2E, 8, nw(2000), gen); if (showGen != gen) return;
            if (!SHWait(nw(5725), gen)) return;
            for (int i = 0; i < 6; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(404), gen)) return;
            SHTap(0x21, 8, 0);
            if (!SHWait(nw(6000), gen)) return;
            SHTitle("NEBEL!"); SHHold(0x20, 8, nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(10214), gen)) return;
            for (int i = 0; i < 2; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(916), gen)) return;
            SHTap(0x13, 8, 0);
            if (!SHWait(nw(358), gen)) return;
            SHTap(0x13, 8, 0);
            if (!SHWait(nw(2503), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(4592), gen)) return;
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            if (!SHWait(nw(3000), gen)) return;
            PlayFX(PickFX(fxNormal, rng), nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;
            SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); // Seifenblasen AN
            if (!SHWait(nw(3000), gen)) return;
            SHTap(0x2E, 8, 0x1D); // Seifenblasen AUS
            if (!SHWait(nw(500), gen)) return;
            SHTitle("FLAMME!"); SHHold(0x2E, 8, nw(2000), gen); if (showGen != gen) return;
            if (!SHWait(nw(10874), gen)) return;
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            if (!SHWait(nw(2378), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1792), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(346), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(966), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(908), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(899), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(444), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1384), gen)) return;
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            if (!SHWait(nw(385), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(478), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1702), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(482), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(2258), gen)) return;
            SHTap(0x0B, 8, 0); // Alles AUS
            if (!SHWait(nw(1264), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(324), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(2270), gen)) return;
            for (int i = 0; i < 9; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(4486), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(648), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(1061), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(786), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(1097), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(731), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(1065), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(947), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(846), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(1049), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(720), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(4789), gen)) return;
            keybd_event(0, 0x0C, 8u, UIntPtr.Zero); // LED-Strobo AN
            if (!SHWait(nw(479), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(3218), gen)) return;
            SHTap(0x0B, 8, 0); // Alles AN
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(1321), gen)) return;
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo AUS
            if (!SHWait(nw(801), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4221), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;
            PlayFX(PickFX(fxNormal, rng), nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(4065), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4072), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(6296), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(2642), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3080), gen)) return;
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            if (!SHWait(nw(1814), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farbstroboskop AN
            SHTitle("ALLES\\nAN!"); SHHoldMulti(new byte[]{{0x39, 0x20, 0x2E}}, 8, nw(3000), gen); if (showGen != gen) return;
            SHTap(0x1E, 8, 0x2A); // Farbstroboskop AUS
            if (!SHWait(nw(4981), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4402), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(8754), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3750), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(7456), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4233), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(8759), gen)) return;
            for (int i = 0; i < 10; i++) {{ SHTap(0x22, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(2274), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x21, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1206), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(515), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(9250), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(9293), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(2703), gen)) return;
            SHTap(0x0B, 8, 0); // Alles AUS
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x0B, 8, 0); // Alles AN
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            if (!SHWait(nw(1320), gen)) return;
            SHTap(0x0B, 8, 0); // Alles AUS
            if (!SHWait(nw(1155), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(576), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(2086), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(646), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(1243), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AN
            if (!SHWait(nw(374), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1034), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(917), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            for (int i = 0; i < 8; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(5223), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(1259), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(646), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(522), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(719), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(322), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(416), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(391), gen)) return;
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            if (!SHWait(nw(709), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(729), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(416), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(875), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(468), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(604), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(540), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(593), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(490), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(681), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(368), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(983), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            if (!SHWait(nw(1508), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(4809), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(8504), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AUS
            SHTap(0x0B, 8, 0); // Alles AN
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            if (!SHWait(nw(1739), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4162), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(7377), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4467), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(10229), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3243), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(867), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(3171), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(3138), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4128), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(547), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(3243), gen)) return;
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            if (!SHWait(nw(1724), gen)) return;
            SHTap(0x4F, 8, 0); // Preset 1 (Lichtprogramm Reset)
            if (!SHWait(nw(3513), gen)) return;
            for (int i = 0; i < 15; i++) {{ SHTap(0x22, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1149), gen)) return;
            for (int i = 0; i < 15; i++) {{ SHTap(0x21, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1025), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(1833), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1743), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(1186), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(2121), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(1198), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1575), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(1054), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1355), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            }}
            else if (t == 1) // PROGRAMM 2 (4:42)
            {{
            if (!SHWait(nw(1151), gen)) return;
            for (int i = 0; i < 2; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(384), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(4000), gen)) return;
            SHTitle("FLAMME!"); SHHold(0x2E, 8, nw(2000), gen); if (showGen != gen) return;
            if (!SHWait(nw(7077), gen)) return;
            for (int i = 0; i < 3; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(2000), gen)) return;
            SHTitle("NEBEL!"); SHHold(0x20, 8, nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(3959), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(304), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(1539), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(714), gen)) return;
            for (int i = 0; i < 3; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(6312), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(3000), gen)) return;
            SHTitle("FLAMME!"); SHHold(0x2E, 8, nw(2000), gen); if (showGen != gen) return;
            if (!SHWait(nw(500), gen)) return;
            SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); // Seifenblasen AN
            if (!SHWait(nw(2500), gen)) return;
            SHTap(0x2E, 8, 0x1D); // Seifenblasen AUS
            if (!SHWait(nw(500), gen)) return;
            SHTitle("NEBEL!"); SHHold(0x20, 8, nw(2000), gen); if (showGen != gen) return;
            if (!SHWait(nw(4043), gen)) return;
            SHTap(0x03, 8, 0); // Licht 2 AUS
            if (!SHWait(nw(556), gen)) return;
            SHTap(0x02, 8, 0); // Licht 1 AUS
            SHTap(0x09, 8, 0); // Licht 8 AUS
            if (!SHWait(nw(466), gen)) return;
            SHTap(0x0B, 8, 0); // Licht 10 AUS
            if (!SHWait(nw(367), gen)) return;
            SHTap(0x06, 8, 0); // Licht 5 AUS
            if (!SHWait(nw(444), gen)) return;
            SHTap(0x05, 8, 0); // Licht 4 AUS
            SHTap(0x07, 8, 0); // Licht 6 AUS
            if (!SHWait(nw(642), gen)) return;
            SHTap(0x04, 8, 0); // Licht 3 AUS
            SHTap(0x08, 8, 0); // Licht 7 AUS
            if (!SHWait(nw(1996), gen)) return;
            // Lichter AUS
            for (int i = 0x02; i <= 0x0A; i++) {{ SHTap((byte)i, 8, 0); Thread.Sleep(50); }}
            if (!SHWait(nw(4523), gen)) return;
            for (int i = 0; i < 9; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1648), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AN
            if (!SHWait(nw(369), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(648), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(378), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(755), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(475), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1352), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(393), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(842), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(310), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1245), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1040), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1385), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1412), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(393), gen)) return;
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            if (!SHWait(nw(946), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            for (int i = 0; i < 9; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(6021), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AUS
            if (!SHWait(nw(633), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AN
            if (!SHWait(nw(760), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AUS
            if (!SHWait(nw(637), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AN
            if (!SHWait(nw(647), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AUS
            if (!SHWait(nw(678), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AN
            if (!SHWait(nw(485), gen)) return;
            keybd_event(0, 0x0C, 8u, UIntPtr.Zero); // LED-Strobo AN
            if (!SHWait(nw(829), gen)) return;
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo AUS
            if (!SHWait(nw(464), gen)) return;
            keybd_event(0, 0x0C, 8u, UIntPtr.Zero); // LED-Strobo AN
            if (!SHWait(nw(777), gen)) return;
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo AUS
            if (!SHWait(nw(548), gen)) return;
            keybd_event(0, 0x0C, 8u, UIntPtr.Zero); // LED-Strobo AN
            if (!SHWait(nw(1018), gen)) return;
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo AUS
            if (!SHWait(nw(567), gen)) return;
            keybd_event(0, 0x0C, 8u, UIntPtr.Zero); // LED-Strobo AN
            if (!SHWait(nw(774), gen)) return;
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo AUS
            if (!SHWait(nw(624), gen)) return;
            keybd_event(0, 0x0C, 8u, UIntPtr.Zero); // LED-Strobo AN
            if (!SHWait(nw(1462), gen)) return;
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo AUS
            if (!SHWait(nw(709), gen)) return;
            keybd_event(0, 0x0C, 8u, UIntPtr.Zero); // LED-Strobo AN
            if (!SHWait(nw(2063), gen)) return;
            // Lichter AN
            for (int i = 0x02; i <= 0x0A; i++) {{ SHTap((byte)i, 8, 0); Thread.Sleep(50); }}
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x1E, 8, 0x2A); // Farb-Strobo AUS
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo AUS
            SHTap(0x02, 8, 0); // Licht 1 AN
            SHTap(0x03, 8, 0); // Licht 2 AN
            SHTap(0x04, 8, 0); // Licht 3 AN
            SHTap(0x05, 8, 0); // Licht 4 AN
            SHTap(0x06, 8, 0); // Licht 5 AN
            SHTap(0x07, 8, 0); // Licht 6 AN
            SHTap(0x08, 8, 0); // Licht 7 AN
            SHTap(0x09, 8, 0); // Licht 8 AN
            SHTap(0x0B, 8, 0); // Licht 10 AN
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            if (!SHWait(nw(1635), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3853), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farbstroboskop AN
            SHTitle("ALLES\\nAN!"); SHHoldMulti(new byte[]{{0x39, 0x20, 0x2E}}, 8, nw(3000), gen); if (showGen != gen) return;
            SHTap(0x1E, 8, 0x2A); // Farbstroboskop AUS
            if (!SHWait(nw(3694), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4191), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(8777), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3739), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(7154), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3042), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(7692), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3768), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(8652), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(1142), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(1978), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1058), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(411), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(680), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(372), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(5478), gen)) return;
            for (int i = 0; i < 13; i++) {{ SHTap(0x22, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(419), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(2931), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(2549), gen)) return;
            for (int i = 0; i < 13; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1142), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1894), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(1472), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(3332), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(1998), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(690), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(866), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(914), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(702), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(1084), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(787), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(1257), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(737), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(1081), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(551), gen)) return;
            keybd_event(0, 0x31, 8u, UIntPtr.Zero); // Gondelbremse AN
            if (!SHWait(nw(1196), gen)) return;
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse AUS
            if (!SHWait(nw(5654), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3561), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(740), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(8023), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3955), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(2148), gen)) return;
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            if (!SHWait(nw(5343), gen)) return;
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            SHTap(0x22, 8, 0x2A); Thread.Sleep(100); // MH Gobo-
            // Lichter AUS
            for (int i = 0x02; i <= 0x0A; i++) {{ SHTap((byte)i, 8, 0); Thread.Sleep(50); }}
            if (!SHWait(nw(1292), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(2999), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1779), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;
            PlayFX(PickFX(fxNormal, rng), nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(3465), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4482), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(1524), gen)) return;
            SHTap(0x4F, 8, 0); // Preset 1 (Lichtprogramm Reset)
            if (!SHWait(nw(7601), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(2426), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(2602), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(1151), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(4183), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(7119), gen)) return;
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            SHTap(0x14, 8, 0x2A); Thread.Sleep(100); // MH Gobo+
            if (!SHWait(nw(1979), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1713), gen)) return;
            for (int i = 0; i < 15; i++) {{ SHTap(0x22, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1371), gen)) return;
            for (int i = 0; i < 15; i++) {{ SHTap(0x21, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(2058), gen)) return;
            // Lichter AN
            for (int i = 0x02; i <= 0x0A; i++) {{ SHTap((byte)i, 8, 0); Thread.Sleep(50); }}
            if (!SHWait(nw(1834), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(1217), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1208), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(1184), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(855), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(798), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1175), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(1099), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(745), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(985), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1133), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            }}
            else // PROGRAMM 3 (4:10)
            {{
            if (!SHWait(nw(1623), gen)) return;
            for (int i = 0; i < 2; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(349), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(2534), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(648), gen)) return;
            SHTap(0x14, 8, 0);
            if (!SHWait(nw(4732), gen)) return;
            for (int i = 0; i < 5; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(4000), gen)) return;
            SHTitle("FLAMME!"); SHHold(0x2E, 8, nw(2000), gen); if (showGen != gen) return;
            if (!SHWait(nw(4848), gen)) return;
            SHTap(0x13, 8, 0);
            if (!SHWait(nw(407), gen)) return;
            SHTap(0x13, 8, 0);
            if (!SHWait(nw(5000), gen)) return;
            SHTitle("NEBEL!"); SHHold(0x20, 8, nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(6410), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1539), gen)) return;
            for (int i = 0; i < 10; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(3718), gen)) return;
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            if (!SHWait(nw(4000), gen)) return;
            PlayFX(PickFX(fxNormal, rng), nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;
            SHTitle("FLAMME!"); SHHold(0x2E, 8, nw(2000), gen); if (showGen != gen) return;
            if (!SHWait(nw(4151), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4291), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(8479), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4409), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(10958), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(8098), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(4000), gen)) return;
            SHTap(0x1E, 8, 0x2A); // Farbstroboskop AN
            SHTitle("ALLES\\nAN!"); SHHoldMulti(new byte[]{{0x39, 0x20, 0x2E}}, 8, nw(3000), gen); if (showGen != gen) return;
            SHTap(0x1E, 8, 0x2A); // Farbstroboskop AUS
            if (!SHWait(nw(8675), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3332), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(7757), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3542), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(7652), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x22, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(906), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x21, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(2030), gen)) return;
            SHTap(0x4F, 8, 0); Thread.Sleep(100); // Preset 1 Reset
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            if (!SHWait(nw(7297), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(6682), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x13, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(941), gen)) return;
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            SHTap(0x11, 8, 0x2A); scTotal++; Thread.Sleep(100); // SpotColor+
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Speed+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            if (!SHWait(nw(1748), gen)) return;
            keybd_event(0, 0x39, 8u, UIntPtr.Zero); // Strobo AN
            if (!SHWait(nw(438), gen)) return;
            keybd_event(0, 0x20, 8u, UIntPtr.Zero); // Nebel AN
            if (!SHWait(nw(1454), gen)) return;
            for (int i = 0; i < 8; i++) {{ SHTap(0x14, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(1126), gen)) return;
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel AUS
            if (!SHWait(nw(3379), gen)) return;
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo AUS
            if (!SHWait(nw(2000), gen)) return;
            PlayFX(PickFX(fxNormal, rng), nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;
            SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); // Seifenblasen AN
            if (!SHWait(nw(2500), gen)) return;
            SHTap(0x2E, 8, 0x1D); // Seifenblasen AUS
            if (!SHWait(nw(2966), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3961), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(9097), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4356), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(9212), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3675), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(7786), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(4088), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(8068), gen)) return;
            SHHold(0x23, 8, 400, gen); // Kreuz AN
            if (showGen != gen) return;
            if (!SHWait(nw(3146), gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS (Richtungswechsel)
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;
            SHTitle("NEBEL!"); SHHold(0x20, 8, nw(3000), gen); if (showGen != gen) return;
            if (!SHWait(nw(5653), gen)) return;
            for (int i = 0; i < 15; i++) {{ SHTap(0x22, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(665), gen)) return;
            for (int i = 0; i < 15; i++) {{ SHTap(0x21, 8, 0); Thread.Sleep(200); }}
            if (!SHWait(nw(668), gen)) return;
            SHTap(0x4F, 8, 0); Thread.Sleep(100); // Preset 1 Reset
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x20, 8, 0x2A); Thread.Sleep(100); // MH Speed-
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            SHTap(0x12, 8, 0x2A); Thread.Sleep(100); // MH Lichtprog+
            if (!SHWait(nw(1904), gen)) return;
            SHTap(0x4F, 8, 0); // Preset 1 (Lichtprogramm Reset)
            if (!SHWait(nw(4608), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1533), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(1352), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1247), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(1114), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1073), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (!SHWait(nw(987), gen)) return;
            SHHold(0x15, 8, 400, gen); // Teller AN
            if (!SHWait(nw(1070), gen)) return;
            SHHold(0x16, 8, 400, gen); // Teller AUS
            }}

            // POST-RIDE
            SHHold(0x16, 8, 400, gen); // Teller AUS
            if (showGen != gen) return;
            if (!SHWait(500, gen)) return;
            SHHold(0x24, 8, 400, gen); // Kreuz AUS
            if (showGen != gen) return;
            Thread.Sleep(500);
            // Safety release aller Hold-Tasten
            keybd_event(0, 0x39, 8u | 2u, UIntPtr.Zero); // Strobo
            keybd_event(0, 0x20, 8u | 2u, UIntPtr.Zero); // Nebel
            keybd_event(0, 0x31, 8u | 2u, UIntPtr.Zero); // Gondelbremse
            keybd_event(0, 0x0C, 8u | 2u, UIntPtr.Zero); // LED-Strobo
            keybd_event(0, 0x2E, 8u | 2u, UIntPtr.Zero); // Flamme
            SHTap(0x4F, 8, 0); // Preset 1

            int scReset = (23 - scTotal % 23) % 23;
            for (int j = 0; j < scReset; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(100); }}
            if (!SHWait(3000, gen)) return;

            SHTitle("Fertig!");
            Log("AutoShow MD [" + (t+1) + "]: Beendet");
            if (!SHWait(5000, gen)) return;

            if (autoLoop && showGen == gen)
            {{
                int rem = loopPause;
                while (rem > 0 && showGen == gen)
                {{
                    SHTitle("PAUSE " + rem + "s");
                    if (rem > 10) {{ Thread.Sleep(5000); rem -= 5; }}
                    else {{ Thread.Sleep(1000); rem--; }}
                }}
                if (showGen != gen) return;
                Log("AutoLoop: Naechste MD Show startet");
                RunMDShow(gen);
                return;
            }}

            showRunning = false;
            SHTitle("AUTO\\\\nSHOW");
            SetImg(showCtx, false);
        }}
        catch (Exception ex)
        {{
            Log("AutoShow MD error: " + ex.Message);
            showRunning = false;
            SHTitle("FEHLER!");
        }}
    }}

            // === TURAKA AUTOSHOW ===
    // Turaka: Bidirektionaler Arm-Slider (Mitte=0%, Speed+ nach rechts, Speed- nach links)
    // Richtungswechsel = Speed- durch 0 hindurch auf andere Seite (kein Direction-Button)
    // Arm muss AUS (0%) sein bevor Gondel geparkt werden kann!
    // Einsteigen/Aussteigen dauert ca 15 Sekunden pro Gondel
    static void RunTKShow(int gen)
    {{
        Random rng = new Random();
        int t = selectedTour;
        if (t == 5) t = rng.Next(5);
        if (t < 0 || t > 4) t = 0;

        bool isNight = nightMode;
        if (isNight) Log("AutoShow TK: NACHT-MODUS aktiv");

        Func<int,int> nw = (ms) => isNight && ms >= 2000 ? ms * 3 / 5 : ms;

        byte[][] vP = tourVP[t];
        byte[][] mP = tourMP[t];
        bool sb = tourSB[t];
        int scTotal = 0;

        // Countdown: Tag ~6:15, Nacht ~3:50 (inkl. Einsteigen/Aussteigen)
        showCountdownSec = isNight ? 230 : 375;

        try
        {{
            Log("AutoShow TK [" + tourNm[t] + "]: Start (~" + (isNight ? "3:50" : "6:15") + " Min)");

            // ============ PHASE 1: HUPE + EINSTEIGEN ============
            SHTitle("HUPE!");
            SHHold(0x2C, 8, 1000, gen); // Hupe (Z)
            if (showGen != gen) return;
            // MH AN + Licht AN
            SHTap(0x2C, 8, 0x2A); Thread.Sleep(200); // MH AN (Shift+Z)
            SHTap(0x2D, 8, 0x2A); Thread.Sleep(200); // MH Licht (Shift+X)
            if (!SHWait(800, gen)) return;

            SHTitle("Gondel 1\\\\nEinsteigen");
            // Gondel 1 ist bereits an der Platte (kein Park noetig - Arm ist aus)
            if (!SHWait(15000, gen)) return;

            // Platte runter, Arm AN, Gondel 2 zur Platte drehen
            SHTitle("Platform\\\\nrunter");
            SHHold(0x15, 8, 500, gen); // Platform RUNTER (Y) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(8000, gen)) return; // Gondel muss runterkommen!
            SHTitle("Arm AN");
            if (!SHWait(1000, gen)) return; // warten bis Spiel On_End registriert
            SHHold(0x23, 8, 1000, gen); // Arm AN (H) - 1s halten!
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHHold(0x23, 8, 1000, gen); // Arm AN nochmal druecken (Sicherheit!)
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHTitle("Gondel 2\\\\nparken");
            SHHold(0x30, 8, 500, gen); // Park Gondel 2 (B) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(18000, gen)) return;

            // Arm AUS, Platte hoch, Einsteigen Gondel 2
            SHTitle("Arm AUS");
            SHHold(0x31, 8, 500, gen); // Arm AUS (N) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHTitle("Platform\\\\nhoch");
            SHHold(0x15, 8, 500, gen); // Platform HOCH (Y) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(4000, gen)) return;

            SHTitle("Gondel 2\\\\nEinsteigen");
            if (!SHWait(15000, gen)) return;

            // Platte runter, Arm AN, losfahren!
            SHTitle("Platform\\\\nrunter");
            SHHold(0x15, 8, 500, gen); // Platform RUNTER (Y) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(8000, gen)) return; // Gondel muss runterkommen!
            SHTitle("Arm AN\\\\nStart!");
            if (!SHWait(1000, gen)) return; // warten bis Spiel On_End registriert
            SHHold(0x23, 8, 1000, gen); // Arm AN (H) - 1s halten!
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHHold(0x23, 8, 1000, gen); // Arm AN nochmal druecken (Sicherheit!)
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHTap(0x4F, 8, 0); // Preset 1

            // ============ PHASE 2: HOCHFAHREN RECHTS Speed+6 = ~40% ============
            SHTitle("Hochfahren");
            if (!SHWait(3000, gen)) return;
            for (int i = 0; i < 6; i++)
            {{
                SHTap(0x13, 8, 0); // Speed+ (R) -> rechts
                if (!SHWait(nw(3000), gen)) return;
            }}
            SHTap(0x50, 8, 0); // Preset 2
            if (!SHWait(3000, gen)) return;
            int rc2t = rng.Next(1, 4); for (int j = 0; j < rc2t; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs2t = rng.Next(1, 4); for (int j = 0; j < rs2t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs2t;

            SHTitle("FLAMME!");
            SHHold(0x2E, 8, 1500, gen);
            if (showGen != gen) return;
            if (!SHWait(nw(5000), gen)) return;

            // ============ PHASE 3: SCHNELLER Speed+5 = ~73% ============
            SHTitle("Schneller!");
            for (int i = 0; i < 5; i++)
            {{
                SHTap(0x13, 8, 0); // Speed+
                if (!SHWait(nw(2500), gen)) return;
            }}
            SHTap(0x51, 8, 0); // Preset 3
            if (!SHWait(nw(3000), gen)) return;
            int rp3t = rng.Next(1, 4); for (int j = 0; j < rp3t; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rs3t = rng.Next(1, 3); for (int j = 0; j < rs3t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs3t;

            PlayFX(PickFX(mP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            // ============ PHASE 4: VOLLGAS RECHTS Speed+4 = 100%! ============
            SHTitle("VOLLGAS!");
            for (int i = 0; i < 4; i++)
            {{
                SHTap(0x13, 8, 0); // Speed+
                if (!SHWait(nw(2000), gen)) return;
            }}
            SHTap(0x4B, 8, 0); // Preset 4
            if (!SHWait(nw(3000), gen)) return;
            int rg4t = rng.Next(1, 4); for (int j = 0; j < rg4t; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc4t = rng.Next(1, 4); for (int j = 0; j < rc4t; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs4t = rng.Next(1, 3); for (int j = 0; j < rs4t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs4t;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AN

            PlayFX(PickFX(vP, rng), nw(4000), gen);

        SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AUS
            if (sb) {{ SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(4000), gen)) return; }}

            PlayFX(PickFX(vP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            if (sb) SHTap(0x2E, 8, 0x1D); // Seifenblasen AUS
            SHTap(0x4C, 8, 0); // Preset 5
            if (!SHWait(3000, gen)) return;

            // ============ PHASE 5: RICHTUNGSWECHSEL 1 (Rechts -> Links) ============
            // Speed- x15 = von +100% zu 0
            SHTitle("Abbremsen!");
            int rc5t = rng.Next(1, 4); for (int j = 0; j < rc5t; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs5t = rng.Next(1, 4); for (int j = 0; j < rs5t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs5t;
            for (int i = 0; i < 15; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(500, gen)) return; }}

            SHTitle("0%\\\\nDrehpunkt!");
            if (!SHWait(nw(2000), gen)) return;
            SHTap(0x4D, 8, 0); // Preset 6

            PlayFX(PickFX(mP, rng), nw(2000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            // Speed- x15 weiter = von 0 zu -100% (LINKS!)
            SHTitle("Andersrum!");
            for (int i = 0; i < 6; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(nw(2000), gen)) return; }}
            SHTitle("Schneller\\\\nLINKS!");
            for (int i = 0; i < 5; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(nw(1500), gen)) return; }}
            for (int i = 0; i < 4; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(nw(1000), gen)) return; }}

            // ============ PHASE 6: VOLLGAS LINKS ============
            SHTitle("VOLLGAS\\\\nLINKS!");
            SHTap(0x47, 8, 0); // Preset 7
            int rp6t = rng.Next(1, 4); for (int j = 0; j < rp6t; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rg6t = rng.Next(1, 4); for (int j = 0; j < rg6t; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rs6t = rng.Next(1, 3); for (int j = 0; j < rs6t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs6t;
            if (!SHWait(nw(2000), gen)) return;

            PlayFX(PickFX(vP, rng), nw(5000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            SHTitle("NEBEL!");
            SHHold(0x20, 8, nw(3000), gen);
            if (showGen != gen) return;

            SHTap(0x48, 8, 0); // Preset 8
            if (!SHWait(nw(3000), gen)) return;

            PlayFX(PickFX(mP, rng), nw(2000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(3000), gen)) return;

            // ============ PHASE 7: RICHTUNGSWECHSEL 2 (Links -> Rechts) ============
            // Speed+ x15 = von -100% zu 0
            SHTitle("Abbremsen!");
            int rc7t = rng.Next(1, 4); for (int j = 0; j < rc7t; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs7t = rng.Next(1, 4); for (int j = 0; j < rs7t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs7t;
            for (int i = 0; i < 15; i++) {{ SHTap(0x13, 8, 0); if (!SHWait(500, gen)) return; }}

            SHTitle("0%\\\\nDrehpunkt!");
            if (!SHWait(nw(2000), gen)) return;
            SHTap(0x49, 8, 0); // Preset 9

            PlayFX(PickFX(mP, rng), nw(4000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            SHTitle("NEBEL!");
            SHHold(0x20, 8, nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            // Speed+ x15 weiter = von 0 zu +100% (RECHTS!)
            SHTitle("Andersrum!");
            for (int i = 0; i < 6; i++) {{ SHTap(0x13, 8, 0); if (!SHWait(nw(2000), gen)) return; }}
            SHTitle("Schneller\\\\nRECHTS!");
            for (int i = 0; i < 5; i++) {{ SHTap(0x13, 8, 0); if (!SHWait(nw(1500), gen)) return; }}
            for (int i = 0; i < 4; i++) {{ SHTap(0x13, 8, 0); if (!SHWait(nw(1000), gen)) return; }}

            // ============ PHASE 8: MEGA PARTY (Rechts 100%) ============
            SHTitle("MEGA\\\\nPARTY!");
            int rp8t = rng.Next(2, 5); for (int j = 0; j < rp8t; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rg8t = rng.Next(1, 4); for (int j = 0; j < rg8t; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc8t = rng.Next(1, 4); for (int j = 0; j < rc8t; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs8t = rng.Next(1, 4); for (int j = 0; j < rs8t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs8t;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AN

            SHTap(0x4F, 8, 0); // Preset 1 (Cycle!)
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(3000), gen)) return; }}

            SHTitle("ALLES\\\\nAN!");
            SHHoldMulti(new byte[]{{0x39, 0x20, 0x2E}}, 8, nw(4000), gen);
            if (showGen != gen) return;

            SHTap(0x50, 8, 0); // Preset 2
            if (!SHWait(nw(3000), gen)) return;

            PlayFX(PickFX(vP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(2000), gen)) return; }}

            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AUS
            SHTitle("FLAMME!");
            SHHold(0x2E, 8, 1500, gen);
            if (showGen != gen) return;
            if (!SHWait(1500, gen)) return;
            SHHold(0x2E, 8, 1500, gen);
            if (showGen != gen) return;

            // ============ PHASE 9: RICHTUNGSWECHSEL 3 (Rechts -> Links) ============
            SHTitle("Abbremsen!");
            int rg9t = rng.Next(1, 4); for (int j = 0; j < rg9t; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc9t = rng.Next(1, 4); for (int j = 0; j < rc9t; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs9t = rng.Next(1, 3); for (int j = 0; j < rs9t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs9t;
            // Speed- x15 von +100% zu 0
            for (int i = 0; i < 15; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(500, gen)) return; }}

            SHTap(0x51, 8, 0); // Preset 3
            SHTitle("0%\\\\nDrehpunkt!");
            if (!SHWait(nw(2000), gen)) return;

            PlayFX(PickFX(mP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            // Speed- x15 weiter = von 0 zu -100% (LINKS!)
            SHTitle("Andersrum!");
            for (int i = 0; i < 6; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(nw(1500), gen)) return; }}
            SHTitle("VOLLGAS\\\\nLINKS!");
            for (int i = 0; i < 5; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(nw(1200), gen)) return; }}
            for (int i = 0; i < 4; i++) {{ SHTap(0x21, 8, 0); if (!SHWait(nw(1000), gen)) return; }}

            // ============ PHASE 10: FINALE (Links 100%) ============
            SHTitle("FINALE!");
            int rp10t = rng.Next(2, 5); for (int j = 0; j < rp10t; j++) {{ SHTap(0x13, 8, 0x2A); Thread.Sleep(150); }}
            int rg10t = rng.Next(2, 5); for (int j = 0; j < rg10t; j++) {{ SHTap(0x14, 8, 0x2A); Thread.Sleep(150); }}
            int rc10t = rng.Next(2, 5); for (int j = 0; j < rc10t; j++) {{ SHTap(0x12, 8, 0x2A); Thread.Sleep(150); }}
            int rs10t = rng.Next(2, 4); for (int j = 0; j < rs10t; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(150); }} scTotal += rs10t;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AN

            SHTap(0x4B, 8, 0); // Preset 4
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTitle("Seifenblasen!"); SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(2000), gen)) return; }}

            SHTitle("MEGA\\\\nALLES!");
            SHHoldMulti(new byte[]{{0x39, 0x20, 0x2E}}, 8, nw(5000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            PlayFX(PickFX(vP, rng), nw(3000), gen);
            if (showGen != gen) return;
            if (!SHWait(nw(2000), gen)) return;

            SHTitle("NEBEL!");
            SHHold(0x20, 8, nw(4000), gen);
            if (showGen != gen) return;

            SHTap(0x4C, 8, 0); // Preset 5
            if (!SHWait(nw(2000), gen)) return;

            if (sb) {{ SHTap(0x2E, 8, 0x1D); if (!SHWait(nw(2000), gen)) return; }}

            if (!SHWait(nw(2000), gen)) return;
            SHTap(0x1E, 8, 0x2A); Thread.Sleep(150); // Farbstroboskop AUS

            // ============ PHASE 11: BREMSEN Speed+15 = von -100% zu 0% ============
            SHTitle("Bremsen!");
            for (int i = 0; i < 8; i++)
            {{
                SHTap(0x13, 8, 0); // Speed+ (zurueck zu 0)
                if (!SHWait(600, gen)) return;
            }}
            SHTap(0x4D, 8, 0); // Preset 6

            SHTitle("Auslaufen");
            for (int i = 0; i < 7; i++)
            {{
                SHTap(0x13, 8, 0); // Speed+
                if (!SHWait(600, gen)) return;
            }}
            if (!SHWait(3000, gen)) return;

            // ============ PHASE 12: PARKEN + AUSSTEIGEN ============
            // WICHTIG: Parking braucht Arm AN! Erst parken, DANN Arm aus!
            SHTitle("Gondel 1\\\\nparken");
            SHHold(0x22, 8, 500, gen); // Park Gondel 1 (G) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(8000, gen)) return; // Arm bremst und parkt Gondel 1 bei 0°

            SHTitle("Arm AUS");
            SHHold(0x31, 8, 500, gen); // Arm AUS (N) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;

            // Platform hoch, Gondel 1 aussteigen
            SHTitle("Platform\\\\nhoch");
            SHHold(0x15, 8, 500, gen); // Platform HOCH (Y) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(4000, gen)) return;
            SHTap(0x4F, 8, 0); // Preset 1

            // SpotColor auf Position 7 zuruecksetzen
            int scReset = (23 - scTotal % 23) % 23;
            for (int j = 0; j < scReset; j++) {{ SHTap(0x11, 8, 0x2A); Thread.Sleep(100); }}

            SHTitle("Gondel 1\\\\nAussteigen");
            if (!SHWait(15000, gen)) return;

            // Gondel 2 zur Platte: Platform runter, Arm AN, Park, Arm AUS, Platform hoch
            SHTitle("Platform\\\\nrunter");
            SHHold(0x15, 8, 500, gen); // Platform RUNTER (Y) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(8000, gen)) return; // Gondel muss runterkommen!
            SHTitle("Arm AN");
            if (!SHWait(1000, gen)) return; // warten bis Spiel On_End registriert
            SHHold(0x23, 8, 1000, gen); // Arm AN (H) - 1s halten!
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHHold(0x23, 8, 1000, gen); // Arm AN nochmal druecken (Sicherheit!)
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHTitle("Gondel 2\\\\nparken");
            SHHold(0x30, 8, 500, gen); // Park Gondel 2 (B) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(18000, gen)) return; // Arm dreht Gondel 2 zur Platte (180°)

            SHTitle("Arm AUS");
            SHHold(0x31, 8, 500, gen); // Arm AUS (N) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(1000, gen)) return;
            SHTitle("Platform\\\\nhoch");
            SHHold(0x15, 8, 500, gen); // Platform HOCH (Y) - 500ms halten!
            if (showGen != gen) return;
            if (!SHWait(4000, gen)) return;

            SHTitle("Gondel 2\\\\nAussteigen");
            if (!SHWait(15000, gen)) return;

            SHTitle("Fertig!");
            Log("AutoShow TK [" + tourNm[t] + "]: Beendet");
            if (!SHWait(5000, gen)) return;

            if (autoLoop && showGen == gen)
            {{
                int rem = loopPause;
                while (rem > 0 && showGen == gen)
                {{
                    SHTitle("PAUSE " + rem + "s");
                    if (rem > 10) {{ Thread.Sleep(5000); rem -= 5; }}
                    else {{ Thread.Sleep(1000); rem--; }}
                }}
                if (showGen != gen) return;
                Log("AutoLoop TK: Naechste Show startet");
                RunTKShow(gen);
                return;
            }}

            showRunning = false;
            SHTitle("AUTO\\\\nSHOW");
            SetImg(showCtx, false);
        }}
        catch (Exception ex)
        {{
            Log("AutoShow TK error: " + ex.Message);
            showRunning = false;
            SHTitle("FEHLER!");
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
    """Generiert die manifest.json für das Plugin."""
    # Reihenfolge: Fahrgeschäfte zuerst, Sound/Mic ganz unten
    MANIFEST_ORDER = [
        "breakdance", "starlight", "xplosion", "funhouse", "rotator", "turaka",
        "lighteffect", "movingheads", "sound","jingles", "standard", "timer", "settings",
    ]
    rides_by_id = {r[0]: r for r in RIDES}
    ordered_rides = [rides_by_id[rid] for rid in MANIFEST_ORDER if rid in rides_by_id]
    # Für Rides die nicht in MANIFEST_ORDER sind, am Ende anfügen
    for r in RIDES:
        if r[0] not in MANIFEST_ORDER:
            ordered_rides.append(r)

    actions = []
    for ride_id, ride_name, _, action_list in ordered_rides:
        # Separator/Header für jede Kategorie
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
            uuid = f"{PLUGIN_ID}.{ride_id}.{action_id}"
            entry = {
                "Icon": icon_path,
                "Name": f"    {label}",
                "States": [{"Image": icon_path, "ShowTitle": True, "TitleAlignment": "bottom"}],
                "Tooltip": f"{ride_name} - {label}",
                "UUID": uuid,
            }
            if uuid == f"{PLUGIN_ID}.timer.startstop":
                entry["PropertyInspectorPath"] = "timer_pi.html"
            if uuid == f"{PLUGIN_ID}.breakdance.autoshow":
                entry["PropertyInspectorPath"] = "show_pi.html"
            if uuid == f"{PLUGIN_ID}.breakdance.autoshow_drive":
                entry["PropertyInspectorPath"] = "show_pi.html"
            if uuid == f"{PLUGIN_ID}.turaka.autoshow":
                entry["PropertyInspectorPath"] = "show_pi.html"
            if uuid == f"{PLUGIN_ID}.settings.s2l":
                entry["PropertyInspectorPath"] = "s2l_pi.html"
            if uuid == f"{PLUGIN_ID}.settings.s2l_licht":
                entry["PropertyInspectorPath"] = "s2l_pi.html"
            actions.append(entry)

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
    }
    return manifest


# HAUPTPROGRAMM
# =====================================================================
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

    # Aufräumen
    if os.path.exists(SDPLUGIN_DIR):
        shutil.rmtree(SDPLUGIN_DIR)
    os.makedirs(SDPLUGIN_DIR, exist_ok=True)

    # 1) C# Quellcode generieren
    print("[1/5] C# Quellcode generieren...")
    cs_path = os.path.join(SDPLUGIN_DIR, "plugin.cs")
    with open(cs_path, "w", encoding="utf-8") as f:
        f.write(generate_cs())
    
    # Anzahl der Aktionen zaehlen
    total_actions = sum(len(a) for _, _, _, a in RIDES)
    print(f"      {total_actions} Aktionen definiert")

    # 2) Kompilieren
    print("[2/5] Kompilieren mit csc.exe...")
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

    # C# Source behalten (für Debugging)
    # os.remove(cs_path)

    # 3) manifest.json
    print("[3/5] manifest.json generieren...")
    manifest = generate_manifest()
    with open(os.path.join(SDPLUGIN_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"      {len(manifest['Actions'])} Aktionen im Manifest")

    # VERSION Datei schreiben
    with open(os.path.join(SDPLUGIN_DIR, "VERSION"), "w") as f:
        f.write(PLUGIN_VERSION)

    # Timer Property Inspector HTML
    timer_pi = '''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{font-family:Arial,sans-serif;background:#2D2D2D;color:#969696;margin:0;padding:12px;font-size:13px}
.row{display:flex;align-items:center;padding:8px 0}
.lbl{flex:0 0 80px;text-align:right;padding-right:12px}
input[type=number]{width:60px;padding:4px 6px;background:#0D0D0D;border:1px solid #3a3a3a;border-radius:3px;color:#d8d8d8;font-size:13px;text-align:center}
.info{color:#666;font-size:11px;margin-top:8px;padding:0 12px}
</style></head><body>
<div class="row"><span class="lbl">Minuten:</span><input type="number" id="m" min="0" max="99" value="3"></div>
<div class="row"><span class="lbl">Sekunden:</span><input type="number" id="s" min="0" max="59" step="10" value="0"></div>
<div class="info">Kurz druecken = Start/Pause<br>Gehalten = Reset</div>
<script>
var ws,uid;
function connectElgatoStreamDeckSocket(p,u,r,i,a){
uid=u;var ai=JSON.parse(a);
ws=new WebSocket("ws://localhost:"+p);
ws.onopen=function(){ws.send(JSON.stringify({event:r,uuid:u}));
var st=ai.payload&&ai.payload.settings;
if(st&&st.duration){var d=parseInt(st.duration);if(d>0){document.getElementById("m").value=Math.floor(d/60);document.getElementById("s").value=d%60}}};
ws.onmessage=function(e){var msg=JSON.parse(e.data);
if(msg.event==="didReceiveSettings"&&msg.payload&&msg.payload.settings&&msg.payload.settings.duration){
var d=parseInt(msg.payload.settings.duration);if(d>0){document.getElementById("m").value=Math.floor(d/60);document.getElementById("s").value=d%60}}}}
function sv(){var m=parseInt(document.getElementById("m").value)||0,s=parseInt(document.getElementById("s").value)||0,d=m*60+s;
if(d<10)d=10;ws.send(JSON.stringify({event:"setSettings",context:uid,payload:{duration:d.toString()}}))}
document.getElementById("m").onchange=sv;document.getElementById("s").onchange=sv;
</script></body></html>'''
    with open(os.path.join(SDPLUGIN_DIR, "timer_pi.html"), "w", encoding="utf-8") as f:
        f.write(timer_pi)

    # AutoShow Tour Property Inspector HTML
    show_pi = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{font-family:Arial,sans-serif;background:#2D2D2D;color:#969696;margin:0;padding:12px;font-size:13px}
.row{display:flex;align-items:center;padding:8px 0}
.lbl{flex:0 0 50px;text-align:right;padding-right:12px;font-weight:bold}
select{width:180px;padding:6px 8px;background:#0D0D0D;border:1px solid #3a3a3a;border-radius:3px;color:#d8d8d8;font-size:13px}
input[type=checkbox]{width:18px;height:18px;accent-color:#ff8800;cursor:pointer}
.desc{color:#aaa;font-size:11px;padding:8px 12px;margin-top:6px;background:#1a1a1a;border-radius:4px;line-height:1.5}
.info{color:#555;font-size:10px;margin-top:10px;padding:0 12px}
h3{color:#ccc;margin:12px 0 4px 0;font-size:12px;border-bottom:1px solid #3a3a3a;padding-bottom:4px}
.night{color:#ff8800;font-size:11px;padding:4px 12px}
</style></head><body>
<h3 id="ttl">BreakDance / MegaDance AutoShow</h3>
<div class="row"><span class="lbl">Tour:</span>
<select id="t">
<optgroup label="BreakDance">
<option value="0">BD 1 - Klassisch</option>
<option value="1">BD 2 - Pirouette</option>
<option value="2">BD 3 - Nebelwand</option>
<option value="3">BD 4 - Lichtgewitter</option>
<option value="4">BD 5 - Inferno</option>
<option value="5">BD \U0001F3B2 Zufall</option>
</optgroup>
<optgroup label="MegaDance (KI)">
<option value="6">MD 1 - Programm 1 (5:22)</option>
<option value="7">MD 2 - Programm 2 (4:42)</option>
<option value="8">MD 3 - Programm 3 (4:10)</option>
<option value="9">MD \U0001F3B2 Zufall</option>
</optgroup>
</select></div>
<div class="row"><span class="lbl">Nacht:</span><input type="checkbox" id="n"><label for="n" style="padding-left:8px;color:#d8d8d8;cursor:pointer">\U0001F319 Nacht-Modus (kuerzer)</label></div>
<div class="night" id="nightinfo" style="display:none">\u26A1 Kurzshow aktiv: Alle Wartezeiten auf 60% gekuerzt</div>
<div class="row"><span class="lbl">Loop:</span><input type="checkbox" id="lp"><label for="lp" style="padding-left:8px;color:#d8d8d8;cursor:pointer">\U0001F501 Endlos-Schleife</label></div>
<div class="row" id="pauserow" style="display:none"><span class="lbl">Pause:</span>
<select id="ps">
<option value="30">30 Sekunden</option>
<option value="45">45 Sekunden</option>
<option value="60" selected>60 Sekunden</option>
<option value="90">90 Sekunden</option>
<option value="120">2 Minuten</option>
<option value="180">3 Minuten</option>
</select></div>
<div class="night" id="loopinfo" style="display:none">\u267B Show wiederholt sich automatisch nach der Pause</div>
<div id="desc" class="desc"></div>
<div class="info" id="modeinfo">Kurz druecken = Show starten / Nochmal = Abbrechen<br>Effekte werden bei jedem Start zufaellig aus dem Tour-Pool gewaehlt!</div>
<script>
var descs=[
"Klassischer ausgewogener Mix.\\nAsymmetrie: Kreuz\\u2192Platte\\u2192Kreuz\\nEffekte: Strobo+Nebel, Flamme+Nebel, LED+Flamme Kombos\\nSeifenblasen: Ja",
"Umgekehrte Drehrichtung!\\nAsymmetrie: Platte\\u2192Kreuz\\u2192Platte\\nEffekte: Strobo+Nebel, Flamme+Nebel, LED+Flamme Kombos\\nSeifenblasen: Ja",
"Nebel-Offensive!\\nAsymmetrie: Kreuz\\u2192Platte\\u2192Kreuz\\nEffekte: Extra viel Nebel, Nebel+Flamme, Nebel+Strobo, ALLES\\nSeifenblasen: Ja",
"Strobo + LED Gewitter!\\nAsymmetrie: Platte\\u2192Kreuz\\u2192Platte\\nEffekte: Strobo, LED, Strobo+LED, Strobo+Flamme\\nSeifenblasen: Nein",
"ALLES MAXIMUM!\\nAsymmetrie: Kreuz\\u2192Platte\\u2192Kreuz\\nEffekte: Strobo+Nebel+Flamme, alle Mega-Kombos\\nSeifenblasen: Ja",
"\\u2728 Bei jedem Start wird zufaellig eine der 5 BD-Touren gewaehlt!\\nJede Tour hat eigene Effekte und Asymmetrie.\\nFuer maximale Abwechslung!",
"\\U0001F3A0 MegaDance KI-Programm 1 (5:22)\\n1:1 Nachbau der Spiel-KI!\\nVollgas mit Richtungswechsel, Gondelbremse, Nebel-Bursts\\nFarbstrobo + Moving Heads",
"\\U0001F3A0 MegaDance KI-Programm 2 (4:42)\\n1:1 Nachbau der Spiel-KI!\\nDunkel-Phasen mit Farbstrobo-Flicker\\nKreuz-Richtungswechsel + Gondelbremse",
"\\U0001F3A0 MegaDance KI-Programm 3 (4:10)\\n1:1 Nachbau der Spiel-KI!\\nKuerzestes Programm, viele Richtungswechsel\\nStrobo + Nebel Kombos",
"\\U0001F3B2 Bei jedem Start wird zufaellig eines der 3 MegaDance KI-Programme gewaehlt!\\nAlle Programme mit Flamme, Nebel, Seifenblasen und ALLES AN!"];
var descsDrive=[
"Klassischer ausgewogener Mix.\\nAsymmetrie: Kreuz\\u2192Platte\\u2192Kreuz\\nAUTO DRIVE: Keine FX-Steuerung\\nFokus: Bewegung und Timing",
"Umgekehrte Drehrichtung!\\nAsymmetrie: Platte\\u2192Kreuz\\u2192Platte\\nAUTO DRIVE: Keine FX-Steuerung\\nFokus: Bewegung und Timing",
"Nebelwand-Motionprofil (ohne FX).\\nAsymmetrie: Kreuz\\u2192Platte\\u2192Kreuz\\nAUTO DRIVE: Keine FX-Steuerung\\nFokus: Bewegung und Timing",
"Lichtgewitter-Motionprofil (ohne FX).\\nAsymmetrie: Platte\\u2192Kreuz\\u2192Platte\\nAUTO DRIVE: Keine FX-Steuerung\\nFokus: Bewegung und Timing",
"Inferno-Motionprofil (ohne FX).\\nAsymmetrie: Kreuz\\u2192Platte\\u2192Kreuz\\nAUTO DRIVE: Keine FX-Steuerung\\nFokus: Bewegung und Timing",
"\\u2728 Bei jedem Start wird zufaellig eine der 5 BD-Touren gewaehlt!\\nAUTO DRIVE waehlt nur das Fahrprofil.\\nKeine FX-Steuerung.",
"\\U0001F3A0 MegaDance KI-Programm 1 (5:22)\\n1:1 Bewegungsablauf der Spiel-KI\\nVollgas mit Richtungswechsel und Gondelbremse\\nKeine FX-Steuerung",
"\\U0001F3A0 MegaDance KI-Programm 2 (4:42)\\n1:1 Bewegungsablauf der Spiel-KI\\nDunkel-Phasen im Fahrprofil enthalten\\nKeine FX-Steuerung",
"\\U0001F3A0 MegaDance KI-Programm 3 (4:10)\\n1:1 Bewegungsablauf der Spiel-KI\\nKuerzestes Programm, viele Richtungswechsel\\nKeine FX-Steuerung",
"\\U0001F3B2 Bei jedem Start wird zufaellig eines der 3 MegaDance KI-Programme gewaehlt!\\nAUTO DRIVE waehlt nur das Fahrprofil.\\nKeine FX-Steuerung"];
var ws,uid,isDrive=false;
function connectElgatoStreamDeckSocket(p,u,r,i,a){
uid=u;var ai=JSON.parse(a);
var ii={};
try{ii=JSON.parse(i||"{}")}catch(_){ii={}};
isDrive=(ai&&ai.action==="com.blackmautz.fairground.breakdance.autoshow_drive")||(ii&&ii.action==="com.blackmautz.fairground.breakdance.autoshow_drive");
if(isDrive){
document.getElementById("ttl").textContent="BreakDance / MegaDance AUTO DRIVE";
document.getElementById("modeinfo").innerHTML="Kurz druecken = AUTO DRIVE starten / Nochmal = Abbrechen<br>Nur Fahrprogramm, keine FX-Steuerung (Nebel/Flamme/Strobo aus)";
}
ws=new WebSocket("ws://localhost:"+p);
ws.onopen=function(){ws.send(JSON.stringify({event:r,uuid:u}));
var st=ai.payload&&ai.payload.settings;
if(st){
if(st.tour){document.getElementById("t").value=st.tour}
if(st.night==="true"){document.getElementById("n").checked=true}
if(st.loop==="true"){document.getElementById("lp").checked=true}
if(st.pause){document.getElementById("ps").value=st.pause}
}
upd()};
ws.onmessage=function(e){var msg=JSON.parse(e.data);
if(msg.event==="didReceiveSettings"&&msg.payload&&msg.payload.settings){
var s=msg.payload.settings;
if(s.tour){document.getElementById("t").value=s.tour}
if(s.night){document.getElementById("n").checked=s.night==="true"}
if(s.loop){document.getElementById("lp").checked=s.loop==="true"}
if(s.pause){document.getElementById("ps").value=s.pause}
upd()}}}
function upd(){var d=document.getElementById("desc");var v=parseInt(document.getElementById("t").value);var src=isDrive?descsDrive:descs;d.innerHTML=src[v].replace(/\\n/g,"<br>");
document.getElementById("nightinfo").style.display=document.getElementById("n").checked?"block":"none";
var lc=document.getElementById("lp").checked;
document.getElementById("pauserow").style.display=lc?"flex":"none";
document.getElementById("loopinfo").style.display=lc?"block":"none"}
function sv(){var v=document.getElementById("t").value;var nc=document.getElementById("n").checked?"true":"false";var lc=document.getElementById("lp").checked?"true":"false";var ps=document.getElementById("ps").value;
ws.send(JSON.stringify({event:"setSettings",context:uid,payload:{tour:v,night:nc,loop:lc,pause:ps}}));upd()}
document.getElementById("t").onchange=sv;
document.getElementById("n").onchange=sv;
document.getElementById("lp").onchange=sv;
document.getElementById("ps").onchange=sv;upd();
</script></body></html>"""
    with open(os.path.join(SDPLUGIN_DIR, "show_pi.html"), "w", encoding="utf-8") as f:
        f.write(show_pi)

    # Sound2Light Property Inspector
    s2l_pi = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{font-family:Arial,sans-serif;background:#2D2D2D;color:#969696;margin:0;padding:12px;font-size:13px}
.row{display:flex;align-items:center;padding:8px 0}
.lbl{flex:0 0 80px;text-align:right;padding-right:12px;font-weight:bold}
select,input[type=range]{width:160px;padding:4px;background:#0D0D0D;border:1px solid #3a3a3a;border-radius:3px;color:#d8d8d8;font-size:13px}
input[type=checkbox]{width:18px;height:18px;accent-color:#ff8800;cursor:pointer}
input[type=range]{accent-color:#00aaff;height:6px;cursor:pointer}
.val{color:#00aaff;font-size:12px;padding-left:8px;min-width:30px}
</style></head><body>
<h3>\U0001F3B5 Sound2Light AutoShow</h3>
<div class="row"><span class="lbl">Sensitivity:</span><input type="range" id="sens" min="10" max="100" value="50"><span class="val" id="sensval">50</span></div>
<div class="row"><span class="lbl">Preset Min:</span>
<select id="plo"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select></div>
<div class="row"><span class="lbl">Preset Max:</span>
<select id="phi"><option value="5">5</option><option value="6">6</option><option value="7">7</option><option value="8">8</option><option value="9" selected>9</option></select></div>
<div class="row"><span class="lbl">Effekte:</span>
<div style="display:flex;flex-direction:column;gap:4px">
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="strobo" checked style="margin-right:6px">Strobo</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="fog" checked style="margin-right:6px">Nebel</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="flame" checked style="margin-right:6px">Flamme</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="led" checked style="margin-right:6px">LED Strobo</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="colorstrobe" checked style="margin-right:6px">Farbstroboskop</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="spot" checked style="margin-right:6px">Spot</label>
<label style="padding-left:8px;color:#ff8800;cursor:pointer;font-weight:bold"><input type="checkbox" id="alles" checked style="margin-right:6px">\u2B50 Alles AN</label>
</div></div>
<div class="row"><span class="lbl">Beleuchtung:</span>
<div style="display:flex;flex-direction:column;gap:4px">
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light1" checked style="margin-right:6px">Gondel R\u00fcckwand</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light2" checked style="margin-right:6px">Kasse Logo</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light3" checked style="margin-right:6px">Front</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light4" checked style="margin-right:6px">Light 4</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light5" checked style="margin-right:6px">Light 5</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light6" checked style="margin-right:6px">Light 6</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light7" checked style="margin-right:6px">Light 7</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light8" checked style="margin-right:6px">Light 8</label>
<label style="padding-left:8px;color:#d8d8d8;cursor:pointer"><input type="checkbox" id="light9" checked style="margin-right:6px">Light 9</label>
</div></div>
<div class="row"><span class="lbl">Nacht:</span><input type="checkbox" id="nt"><label for="nt" style="padding-left:8px;color:#d8d8d8">Nacht-Modus</label></div>
<div class="row"><span class="lbl">Loop:</span><input type="checkbox" id="lp"><label for="lp" style="padding-left:8px;color:#d8d8d8">Endlos-Schleife</label></div>
<div class="row"><span class="lbl">Motor-Pausen:</span><input type="checkbox" id="gp" checked><label for="gp" style="padding-left:8px;color:#d8d8d8">Gondel-Pauses</label></div>
<div class="row"><span class="lbl">Dauer:</span>
<select id="dur">
<option value="0">Endlos (manuell stoppen)</option>
<option value="180" selected>3 Minuten</option>
<option value="300">5 Minuten</option>
<option value="420">7 Minuten</option>
<option value="600">10 Minuten</option>
<option value="900">15 Minuten</option>
</select></div>
<div style="border-top:1px solid #444;padding-top:12px;margin-top:12px">
<h4 style="margin:0 0 12px 0;color:#00aaff">\u2B58 Multi-Fahrt-Serie</h4>
<div class="row"><span class="lbl">Fahrten:</span>
<select id="nfrt">
<option value="0">⊘ Deaktiviert</option>
<option value="1">1 Fahrt</option>
<option value="2">2 Fahrten</option>
<option value="3">3 Fahrten</option>
<option value="4">4 Fahrten</option>
<option value="5">5 Fahrten</option>
</select></div>
<div class="row"><span class="lbl">Pause:</span>
<select id="paus">
<option value="30">30 Sekunden</option>
<option value="60" selected>1 Minute</option>
<option value="90">1:30 Minuten</option>
<option value="120">2 Minuten</option>
<option value="180">3 Minuten</option>
</select></div>
<div class="row"><span class="val" id="frtinfo" style="color:#00aa00;padding-left:12px">Deaktiviert</span></div>
</div>
<script>
var ws,uid;
function updateFrtInfo(){
var nfrt=document.getElementById("nfrt").value||"0";
if(nfrt==="0"){
document.getElementById("frtinfo").textContent="\u2296 Deaktiviert";
}else{
document.getElementById("frtinfo").textContent="Fahrt 1 von "+nfrt;
}}
function connectElgatoStreamDeckSocket(p,u,r,i,a){
uid=u;var ai=JSON.parse(a);
ws=new WebSocket("ws://localhost:"+p);
ws.onopen=function(){ws.send(JSON.stringify({event:r,uuid:u}));
var st=ai.payload&&ai.payload.settings;
if(st){
if(st.sensitivity){document.getElementById("sens").value=st.sensitivity;document.getElementById("sensval").textContent=st.sensitivity}
if(st.presetlow){document.getElementById("plo").value=st.presetlow}
if(st.presethigh){document.getElementById("phi").value=st.presethigh}
if(st.strobo){document.getElementById("strobo").checked=st.strobo==="true"}
if(st.fog){document.getElementById("fog").checked=st.fog==="true"}
if(st.flame){document.getElementById("flame").checked=st.flame==="true"}
if(st.led){document.getElementById("led").checked=st.led==="true"}
if(st.colorstrobe){document.getElementById("colorstrobe").checked=st.colorstrobe==="true"}
if(st.spot){document.getElementById("spot").checked=st.spot==="true"}
if(st.alles){document.getElementById("alles").checked=st.alles==="true"}
if(st.light1){document.getElementById("light1").checked=st.light1==="true"}
if(st.light2){document.getElementById("light2").checked=st.light2==="true"}
if(st.light3){document.getElementById("light3").checked=st.light3==="true"}
if(st.light4){document.getElementById("light4").checked=st.light4==="true"}
if(st.light5){document.getElementById("light5").checked=st.light5==="true"}
if(st.light6){document.getElementById("light6").checked=st.light6==="true"}
if(st.light7){document.getElementById("light7").checked=st.light7==="true"}
if(st.light8){document.getElementById("light8").checked=st.light8==="true"}
if(st.light9){document.getElementById("light9").checked=st.light9==="true"}
if(st.night){document.getElementById("nt").checked=st.night==="true"}
if(st.loop){document.getElementById("lp").checked=st.loop==="true"}
if(st.gondelpause){document.getElementById("gp").checked=st.gondelpause==="true"}
if(st.duration){document.getElementById("dur").value=st.duration}
if(st.numfahrten){document.getElementById("nfrt").value=st.numfahrten;updateFrtInfo()}
if(st.pauseduration){document.getElementById("paus").value=st.pauseduration}
}};
ws.onmessage=function(e){var msg=JSON.parse(e.data);
if(msg.event==="didReceiveSettings"&&msg.payload&&msg.payload.settings){
var s=msg.payload.settings;
if(s.sensitivity){document.getElementById("sens").value=s.sensitivity;document.getElementById("sensval").textContent=s.sensitivity}
if(s.presetlow){document.getElementById("plo").value=s.presetlow}
if(s.presethigh){document.getElementById("phi").value=s.presethigh}
if(s.strobo){document.getElementById("strobo").checked=s.strobo==="true"}
if(s.fog){document.getElementById("fog").checked=s.fog==="true"}
if(s.flame){document.getElementById("flame").checked=s.flame==="true"}
if(s.led){document.getElementById("led").checked=s.led==="true"}
if(s.colorstrobe){document.getElementById("colorstrobe").checked=s.colorstrobe==="true"}
if(s.spot){document.getElementById("spot").checked=s.spot==="true"}
if(s.alles){document.getElementById("alles").checked=s.alles==="true"}
if(s.light1){document.getElementById("light1").checked=s.light1==="true"}
if(s.light2){document.getElementById("light2").checked=s.light2==="true"}
if(s.light3){document.getElementById("light3").checked=s.light3==="true"}
if(s.light4){document.getElementById("light4").checked=s.light4==="true"}
if(s.light5){document.getElementById("light5").checked=s.light5==="true"}
if(s.light6){document.getElementById("light6").checked=s.light6==="true"}
if(s.light7){document.getElementById("light7").checked=s.light7==="true"}
if(s.light8){document.getElementById("light8").checked=s.light8==="true"}
if(s.light9){document.getElementById("light9").checked=s.light9==="true"}
if(s.night){document.getElementById("nt").checked=s.night==="true"}
if(s.loop){document.getElementById("lp").checked=s.loop==="true"}
if(s.gondelpause){document.getElementById("gp").checked=s.gondelpause==="true"}
if(s.duration){document.getElementById("dur").value=s.duration}
if(s.numfahrten){document.getElementById("nfrt").value=s.numfahrten;updateFrtInfo()}
if(s.pauseduration){document.getElementById("paus").value=s.pauseduration}
}}}
function sv(changedId){
var sens=document.getElementById("sens").value;
var plo=document.getElementById("plo").value;
var phi=document.getElementById("phi").value;
var strobo=document.getElementById("strobo").checked?"true":"false";
var fog=document.getElementById("fog").checked?"true":"false";
var flame=document.getElementById("flame").checked?"true":"false";
var led=document.getElementById("led").checked?"true":"false";
var colorstrobe=document.getElementById("colorstrobe").checked?"true":"false";
var spot=document.getElementById("spot").checked?"true":"false";
var alles=document.getElementById("alles").checked?"true":"false";
var light1=document.getElementById("light1").checked?"true":"false";
var light2=document.getElementById("light2").checked?"true":"false";
var light3=document.getElementById("light3").checked?"true":"false";
var light4=document.getElementById("light4").checked?"true":"false";
var light5=document.getElementById("light5").checked?"true":"false";
var light6=document.getElementById("light6").checked?"true":"false";
var light7=document.getElementById("light7").checked?"true":"false";
var light8=document.getElementById("light8").checked?"true":"false";
var light9=document.getElementById("light9").checked?"true":"false";
var nt=document.getElementById("nt").checked?"true":"false";
var lp=document.getElementById("lp").checked?"true":"false";
var gp=document.getElementById("gp").checked?"true":"false";
var dur=document.getElementById("dur").value;
var nfrt=document.getElementById("nfrt").value;
var paus=document.getElementById("paus").value;
if(changedId==="alles"&&document.getElementById("alles").checked){
document.getElementById("strobo").checked=true;
document.getElementById("fog").checked=true;
document.getElementById("flame").checked=true;
document.getElementById("led").checked=true;
document.getElementById("colorstrobe").checked=true;
document.getElementById("spot").checked=true;
strobo=fog=flame=led=colorstrobe=spot="true";}
if(changedId!=="alles"){
if(!document.getElementById("strobo").checked||!document.getElementById("fog").checked||!document.getElementById("flame").checked||!document.getElementById("led").checked||!document.getElementById("colorstrobe").checked||!document.getElementById("spot").checked){
document.getElementById("alles").checked=false;alles="false";}
else{document.getElementById("alles").checked=true;alles="true";}}
strobo=document.getElementById("strobo").checked?"true":"false";
fog=document.getElementById("fog").checked?"true":"false";
flame=document.getElementById("flame").checked?"true":"false";
led=document.getElementById("led").checked?"true":"false";
colorstrobe=document.getElementById("colorstrobe").checked?"true":"false";
spot=document.getElementById("spot").checked?"true":"false";
alles=document.getElementById("alles").checked?"true":"false";
updateFrtInfo();
ws.send(JSON.stringify({event:"setSettings",context:uid,payload:{sensitivity:sens,presetlow:plo,presethigh:phi,strobo:strobo,fog:fog,flame:flame,led:led,colorstrobe:colorstrobe,spot:spot,alles:alles,light1:light1,light2:light2,light3:light3,light4:light4,light5:light5,light6:light6,light7:light7,light8:light8,light9:light9,night:nt,loop:lp,gondelpause:gp,duration:dur,numfahrten:nfrt,pauseduration:paus}}));}
document.getElementById("sens").oninput=function(){sv("sens")};
document.getElementById("plo").onchange=function(){sv("plo")};
document.getElementById("phi").onchange=function(){sv("phi")};
document.getElementById("strobo").onchange=function(){sv("strobo")};
document.getElementById("fog").onchange=function(){sv("fog")};
document.getElementById("flame").onchange=function(){sv("flame")};
document.getElementById("led").onchange=function(){sv("led")};
document.getElementById("colorstrobe").onchange=function(){sv("colorstrobe")};
document.getElementById("spot").onchange=function(){sv("spot")};
document.getElementById("alles").onchange=function(){sv("alles")};
document.getElementById("light1").onchange=function(){sv("light1")};
document.getElementById("light2").onchange=function(){sv("light2")};
document.getElementById("light3").onchange=function(){sv("light3")};
document.getElementById("light4").onchange=function(){sv("light4")};
document.getElementById("light5").onchange=function(){sv("light5")};
document.getElementById("light6").onchange=function(){sv("light6")};
document.getElementById("light7").onchange=function(){sv("light7")};
document.getElementById("light8").onchange=function(){sv("light8")};
document.getElementById("light9").onchange=function(){sv("light9")};
document.getElementById("nt").onchange=function(){sv("nt")};
document.getElementById("lp").onchange=function(){sv("lp")};
document.getElementById("gp").onchange=function(){sv("gp")};
document.getElementById("dur").onchange=function(){sv("dur")};
document.getElementById("nfrt").onchange=function(){sv("nfrt")};
document.getElementById("paus").onchange=function(){sv("paus")};
</script></body></html>"""
    with open(os.path.join(SDPLUGIN_DIR, "s2l_pi.html"), "w", encoding="utf-8") as f:
        f.write(s2l_pi)

    # 4) Icons erstellen
    print("[4/5] Icons erstellen...")
    imgs_dir = os.path.join(SDPLUGIN_DIR, "imgs")
    os.makedirs(imgs_dir, exist_ok=True)

    # Plugin-Icon + Kategorie-Icon aus Githubreadmybild.png
    from PIL import Image
    main_img_path = os.path.join(BASE_DIR, "icons", "categories", "Githubreadmybild.png")
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

    # Action-Icon (für die Aktionsliste)
    for name, size in [("action.png", 20), ("action@2x.png", 40)]:
        with open(os.path.join(imgs_dir, name), "wb") as f:
            f.write(create_png(size, size, 50, 50, 50))

    # Key-Image (auf dem Button angezeigt)
    for name, size in [("key.png", 72), ("key@2x.png", 144)]:
        with open(os.path.join(imgs_dir, name), "wb") as f:
            f.write(create_png(size, size, 35, 35, 40))

    # Kategorie-Icons kopieren
    import shutil
    cat_icons_src = os.path.join(BASE_DIR, "icons", "categories")
    cat_dir = os.path.join(imgs_dir, "categories")
    os.makedirs(cat_dir, exist_ok=True)
    if os.path.exists(cat_icons_src):
        for png in os.listdir(cat_icons_src):
            if png.endswith(".png") and png != "Githubreadmybild.png":
                ride_id = png.replace(".png", "")
                shutil.copy2(os.path.join(cat_icons_src, png), os.path.join(cat_dir, f"{ride_id}.png"))

    # Per-Action Icons kopieren
    icons_src = os.path.join(BASE_DIR, "icons")
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

    # 5) Als .streamDeckPlugin verpacken (ZIP)
    print("[5/5] Als .streamDeckPlugin verpacken...")
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
        print("[+] Direkt in installierten Plugin-Ordner kopieren...")
        # plugin.exe kopieren
        shutil.copy2(exe_path, os.path.join(installed_dir, "plugin.exe"))
        # manifest.json aktualisieren
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
        # Timer Property Inspector kopieren
        shutil.copy2(os.path.join(SDPLUGIN_DIR, "timer_pi.html"), os.path.join(installed_dir, "timer_pi.html"))
        shutil.copy2(os.path.join(SDPLUGIN_DIR, "show_pi.html"), os.path.join(installed_dir, "show_pi.html"))
        shutil.copy2(os.path.join(SDPLUGIN_DIR, "s2l_pi.html"), os.path.join(installed_dir, "s2l_pi.html"))
        print(f"      plugin.exe + manifest + imgs + VERSION + PI kopiert nach {installed_dir}")
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
    print(f"\nInstallation:")
    print(f"  Doppelklick auf 'Fairground_Online.streamDeckPlugin'")
    print(f"  Stream Deck App installiert die Erweiterung automatisch!")
    print(f"{'='*55}")
