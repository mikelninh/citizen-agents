# AVV — Auftragsverarbeitungsvertrag (Art. 28 DSGVO) — Skeleton

**Vorlage für Institutionen, die Citizen Agents als Auftragsverarbeiter einsetzen.**
Bilingual (DE/EN). This is a skeleton for legal review — NOT final legal advice.
Ein Datenschutzbeauftragter muss die konkrete Fassung prüfen.

---

## Vertragsparteien / Parties

- **Auftraggeber (Verantwortlicher / Controller):** [Institution, Anschrift, DSB]
- **Auftragsnehmer (Auftragsverarbeiter / Processor):** [Rechtsträger, Anschrift, DSB]

## Gegenstand / Subject

Verarbeitung im Auftrag gemäß Art. 28 DSGVO im Rahmen der Nutzung der
Citizen-Agents-Plattform (Watchdog-Agenten, MCP-Server, Digests/Logs).

## Arten personenbezogener Daten / Categories of personal data

Bei Standardbetrieb der Watchdog-Flotte: **keine** (nur öffentliche Quellen).
Bei aktivierten Citizen-Flächen (SafeVoice, Leistungsrechner): vom Nutzer
eingegebene Angaben (Sachverhalt, Einkommen, Haushaltsdaten).

## Kategorien betroffener Personen / Data subjects

Nutzer:innen der Citizen-Flächen, die Daten aktiv übermitteln.

## Weisungen / Instructions

- Verarbeitung nur nach dokumentierter Weisung des Auftraggebers (Art. 28 Abs. 3 lit. a).
- Änderungen der Weisung bedürfen der Schriftform.

## Technische und organisatorische Maßnahmen (TOM, Art. 32)

- Browser-First-Verarbeitung: Berechnung lokal im Browser, kein Serverkontakt ohne explizite Übermittlung
- Pseudonymisierung interner IDs
- Verschlüsselung: TLS in transit, AES-256 at rest
- EU-only Hosting (Hetzner Frankfurt/Falkenstein)
- Zugriffskontrolle: individuelle Accounts, Rollen, Audit-Log
- Löschkonzept: Datenlöschung nach Zweckerfüllung (Standard: 30 Tage, es sei denn Nutzer exportiert)
- **Nachweispflicht:** alle TOMs sind aus dem öffentlichen Repository ablesbar (agent-logs als lebendes TOM)

## Unterauftragsverarbeiter / Sub-processors

| Name | Zweck | Land | AVV |
|---|---|---|---|
| Hetzner Online GmbH | Hosting | DE | ✓ mit Hetzner |
| [LLM-Provider] | Inferenz | [EU/US] | ✓ bei Bedarf (siehe Datenschutzerklärung) |

## Betroffenenrechte / Data subject rights

- Unterstützung bei Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit (Art. 15–20)
- Frist: 30 Tage

## Meldung von Verletzungen / Breach notification

- Unverzügliche Meldung an Auftraggeber (Art. 33/34), spätestens 48h nach Kenntnis

## Löschung / Deletion

- Nach Vertragsende: Löschung oder Rückgabe aller Daten (Art. 28 Abs. 3 lit. g)
- Standard-Löschfrist: 30 Tage nach Zweckerfüllung

## Haftung / Liability

- Auftragsnehmer haftet gemäß Art. 82 DSGVO für seine Verarbeitung

## Schlussbestimmungen

- Schriftform, salvatorische Klausel, deutsches Recht, Gerichtsstand [Ort]

---

**English skeleton available on request — same structure.**

*Vorlage Digital Democracy Studio, 2026. Rechtlich unverbindlich; finale Fassung
durch Datenschutzbeauftragte/n Rechtsanwalt.*
