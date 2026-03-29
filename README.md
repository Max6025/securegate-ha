<p align="center">
  <img src="https://img.shields.io/badge/SecureGate-Home%20Assistant-41BDF5?style=for-the-badge&logo=home-assistant&logoColor=white" alt="SecureGate HA"/>
</p>

<h1 align="center">🔐 SecureGate — Home Assistant Integration</h1>

<p align="center">
  <strong>Professionelle NFC-Zutrittskontrolle direkt in Home Assistant</strong><br>
  Multi-Room · Auto-Discovery · Echtzeit-Sensoren · Steuerbare Switches
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-green?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/HACS-Custom-orange?style=flat-square" alt="HACS"/>
  <img src="https://img.shields.io/badge/iot_class-local_polling-blue?style=flat-square" alt="IoT Class"/>
  <img src="https://img.shields.io/badge/license-Apache%202.0-lightgrey?style=flat-square" alt="License"/>
</p>

---

## 📋 Übersicht

Diese Custom Integration verbindet dein **SecureGate NFC-Zutrittskontrollsystem** mit Home Assistant. Alle Räume werden automatisch erkannt und als eigene Geräte angelegt — inklusive Live-Sensoren, Binärsensoren und steuerbaren Switches.

### Highlights

- **Auto-Discovery** — Scannt automatisch Ports 5000–5900 und erkennt alle aktiven Räume
- **Multi-Room** — Jeder Raum erscheint als eigenes HA-Gerät mit bis zu 20 Entitäten
- **Admin-Gerät** — Aggregierte Übersicht über alle Räume
- **Steuerbar** — Lockdown und Wartungsmodus direkt aus HA schalten
- **Services** — Broadcasts senden, Befehle ausführen, Massenaktionen
- **112 Entitäten** bei 5 Räumen — alles live

---

## 🚀 Installation

### HACS (empfohlen)

1. **HACS** → Integrationen → ⋮ Menü → **Benutzerdefinierte Repositories**
2. URL: `https://github.com/Max6025/SecureGate` — Kategorie: **Integration**
3. **SecureGate** suchen und installieren
4. Home Assistant neu starten

### Manuell

1. ZIP herunterladen und entpacken
2. Den Ordner `custom_components/securegate/` nach `/config/custom_components/securegate/` kopieren
3. Home Assistant neu starten

---

## ⚙️ Einrichtung

1. **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
2. Suche: **SecureGate**
3. IP-Adresse deines SecureGate Systems eingeben (z.B. `192.168.1.135`)
4. Räume werden automatisch erkannt ✓

Die Integration scannt die Ports 5000–5900 und findet alle laufenden SecureGate Instanzen. Jeder Raum wird als eigenes Gerät in Home Assistant angelegt.

---

## 🏗️ Geräte-Architektur

```
SecureGate Admin          ← Aggregierte Übersicht
├── Haus Tür              ← Port 5000
├── EG Terasse            ← Port 5100
├── Zimmer Max            ← Port 5200
├── OG Bad                ← Port 5300
└── EG Klo                ← Port 5400
```

Jeder Raum ist ein eigenes HA-Gerät mit eigenem Status, Sensoren und Steuerung. Das Admin-Gerät fasst alle Räume zusammen und bietet Massensteuerung.

---

## 📊 Entitäten

### Pro Raum — Sensoren (10)

| Entity | Typ | Beschreibung |
|:--|:--|:--|
| `sensor.RAUM_active_users` | Measurement | Anzahl aktuell eingecheckter User |
| `sensor.RAUM_active_guests` | Measurement | Anzahl aktiver Gäste |
| `sensor.RAUM_today_logins` | Counter | Logins heute (gesamt) |
| `sensor.RAUM_status` | Status | Bereit / Lockdown / Wartungsmodus / Offline |
| `sensor.RAUM_broadcast` | Text | Aktueller Broadcast-Text |
| `sensor.RAUM_akzentfarbe` | Hex | Aktuelle Akzentfarbe (`#c8a04a`) |
| `sensor.RAUM_countdown` | Timer | Aktiver Countdown (z.B. `Schließt in 4:32`) |
| `sensor.RAUM_letztes_event` | Event | Letzter Scan (`CHECK-IN Max Starnberg`) |
| `sensor.RAUM_zugangszeiten` | Zeitfenster | `07:00 – 20:00` oder `Geschlossen` |
| `sensor.RAUM_uptime` | Dauer | Laufzeit des Raum-Controllers |

### Pro Raum — Binärsensoren (8)

| Entity | Device Class | Beschreibung |
|:--|:--|:--|
| `binary_sensor.RAUM_locked` | Lock | Lockdown aktiv? |
| `binary_sensor.RAUM_maintenance` | — | Wartungsmodus aktiv? |
| `binary_sensor.RAUM_master_mode` | — | Master-Modus aktiv? |
| `binary_sensor.RAUM_card_stuck` | Problem | Karte klemmt auf dem Leser? |
| `binary_sensor.RAUM_reader_error` | Problem | Lesegerät meldet Fehler? |
| `binary_sensor.RAUM_invalid_card` | Problem | Unbekannte Karte gescannt? |
| `binary_sensor.RAUM_online` | Connectivity | Raum erreichbar? |
| `binary_sensor.RAUM_zugang_geschlossen` | — | Außerhalb der Zugangszeiten? |

### Pro Raum — Switches (2)

| Entity | Aktion |
|:--|:--|
| `switch.RAUM_lockdown` | Lockdown ein-/ausschalten |
| `switch.RAUM_wartungsmodus` | Wartungsmodus ein-/ausschalten |

### Admin — Sensoren (7)

| Entity | Beschreibung |
|:--|:--|
| `sensor.securegate_total_users` | Summe aller aktiven User |
| `sensor.securegate_total_guests` | Summe aller aktiven Gäste |
| `sensor.securegate_total_logins` | Summe aller Logins heute |
| `sensor.securegate_rooms_online` | Anzahl erreichbarer Räume |
| `sensor.securegate_rooms_locked` | Anzahl gesperrter Räume |
| `sensor.securegate_rooms_maintenance` | Anzahl Räume in Wartung |
| `sensor.securegate_system_health` | OK / Lockdown / Wartung / Teilweise / Offline |

### Admin — Binärsensoren (3)

| Entity | Beschreibung |
|:--|:--|
| `binary_sensor.securegate_alle_online` | Alle Räume erreichbar? |
| `binary_sensor.securegate_lockdown_aktiv` | Mindestens ein Raum im Lockdown? |
| `binary_sensor.securegate_wartung_aktiv` | Mindestens ein Raum in Wartung? |

### Admin — Switches (2)

| Entity | Aktion |
|:--|:--|
| `switch.securegate_alle_lockdown` | Lockdown in **allen** Räumen |
| `switch.securegate_alle_wartung` | Wartung in **allen** Räumen |

---

## 🎯 Services

| Service | Parameter | Beschreibung |
|:--|:--|:--|
| `securegate.broadcast` | `message`, `type`, `duration`, `port` | Broadcast senden (port=0 → alle) |
| `securegate.kick_all` | `port` | Alle User auschecken |
| `securegate.cmd` | `command`, `port` | Beliebigen Befehl senden |
| `securegate.lockdown_all` | — | Alle Räume sperren |
| `securegate.unlock_all` | — | Alle Räume entsperren |
| `securegate.maintenance_all` | `duration`, `message` | Wartung überall aktivieren |
| `securegate.maintenance_off_all` | — | Wartung überall deaktivieren |

### Service-Beispiele

**Broadcast an alle Räume:**
```yaml
service: securegate.broadcast
data:
  message: "Besprechung in 5 Minuten im Konferenzraum"
  type: info
  duration: 300
```

**Lockdown eines bestimmten Raums:**
```yaml
service: securegate.cmd
data:
  command: lock
  port: 5000
```

**Wartungsmodus für 30 Minuten:**
```yaml
service: securegate.maintenance_all
data:
  duration: 1800
  message: "System-Update läuft"
```

---

## 🤖 Automationen

### Beispiel: Alarm bei unbekannter Karte

```yaml
automation:
  - alias: "SecureGate — Unbekannte Karte Alarm"
    trigger:
      - platform: state
        entity_id: binary_sensor.haus_tur_invalid_card
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ SecureGate"
          message: "Unbekannte Karte an Haus Tür gescannt!"
```

### Beispiel: Lockdown bei Nacht

```yaml
automation:
  - alias: "SecureGate — Nacht-Lockdown"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: securegate.lockdown_all
  
  - alias: "SecureGate — Morgens entsperren"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: securegate.unlock_all
```

### Beispiel: Dashboard-Info wenn niemand da ist

```yaml
automation:
  - alias: "SecureGate — Letzter geht"
    trigger:
      - platform: numeric_state
        entity_id: sensor.securegate_total_users
        below: 1
    action:
      - service: securegate.broadcast
        data:
          message: "Alle ausgecheckt — System wird gesperrt"
          type: warnung
          duration: 60
      - delay: "00:01:00"
      - service: securegate.lockdown_all
```

---

## 📱 Dashboard-Karten

### Einfache Übersicht

```yaml
type: entities
title: SecureGate
entities:
  - entity: sensor.securegate_system_health
  - entity: sensor.securegate_total_users
  - entity: sensor.securegate_rooms_online
  - entity: switch.securegate_alle_lockdown
  - entity: switch.securegate_alle_wartung
```

### Raum-Karte mit Glance

```yaml
type: glance
title: Haus Tür
entities:
  - entity: sensor.haus_tur_active_users
    name: User
  - entity: sensor.haus_tur_status
    name: Status
  - entity: binary_sensor.haus_tur_online
    name: Online
  - entity: switch.haus_tur_lockdown
    name: Lock
```

---

## 🔧 Konfiguration

| Parameter | Standard | Beschreibung |
|:--|:--|:--|
| `host` | — | IP-Adresse des SecureGate Systems |
| `name` | SecureGate | Anzeigename |
| `scan_interval` | 10 | Aktualisierungsintervall in Sekunden |

Die Integration pollt alle Räume gleichzeitig. Bei 5 Räumen und 10 Sekunden Intervall sind das ~10 API-Calls pro Zyklus.

---

## 🛡️ Voraussetzungen

- **Home Assistant** 2024.1 oder neuer
- **SecureGate** System auf einem Raspberry Pi im lokalen Netzwerk
- Ports 5000–5900 müssen von HA aus erreichbar sein
- HACS (für automatische Updates)

---

## 📁 Dateistruktur

```
custom_components/securegate/
├── __init__.py          # Integration Setup + Services
├── config_flow.py       # UI-Konfiguration + Auto-Discovery
├── const.py             # Konstanten
├── coordinator.py       # Multi-Room Daten-Fetcher
├── sensor.py            # 10 Raum-Sensoren + 7 Admin-Sensoren
├── binary_sensor.py     # 8 Raum-Binärsensoren + 3 Admin
├── switch.py            # 2 Raum-Switches + 2 Admin-Switches
├── services.yaml        # 7 Service-Definitionen
├── manifest.json        # Integration Metadata
├── strings.json         # UI-Texte
└── translations/
    ├── de.json           # Deutsch
    └── en.json           # English
```

---

## 📝 Changelog

### v2.0.0
- Multi-Room Architektur — jeder Raum als eigenes Gerät
- Auto-Discovery scannt Ports 5000–5900
- 20 Entitäten pro Raum (10 Sensoren, 8 Binary, 2 Switches)
- Admin-Gerät mit aggregierten Werten
- 7 Services mit optionalem Port-Targeting
- Zugangszeiten, Countdown, Akzentfarbe als Sensoren

### v1.0.0
- Initiale Version mit Einzelraum-Support

---

<p align="center">
  <strong>SecureGate</strong> — Professionelle NFC-Zutrittskontrolle<br>
  <a href="https://github.com/Max6025/SecureGate">GitHub</a> · Apache 2.0
</p>
