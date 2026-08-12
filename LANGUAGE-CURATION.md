# Sprach-Kuratierung — Workflow für Citizen Agents

Citizen Agents liefert den Breakfast Ticker in mehreren Sprachen. Dieses Dokument
beschreibt, wie Übersetzungen in die Sprachen **TR · RU · AR · VI · PL** (und künftig
weitere) kommen — kuratiert (geprüft) statt nur maschinell.

## Status der Sprachen

| Sprache | Quelle | Status-Flag im Feed | Banner |
|---------|--------|--------------------|--------|
| DE      | Watchdog (Quelle der Wahrheit) | `human` | keins |
| EN      | Watchdog (parallel produziert) | `human` | keins |
| TR · RU · AR | Community/Stiftung kuratiert | `human` nach Freigabe | "geprüft" |
| VI · PL | Maschinenübersetzung aus DE/EN | `mt` | "automatisch übersetzt" |

DE und EN werden vom Watchdog-Agenten direkt erzeugt. TR/RU/AR/VI/PL werden über
das `translations`-Feld je Meldung angedockt.

## Feed-Schema (Zielarchitektur)

Jede Meldung im `breakfast-feed.json` trägt:

```json
{
  "headline": "...",            // DE (Rückwärtskompatibilität)
  "de":  { "headline": "...", "what_changed": "...", ... },
  "en":  { "headline": "...", "what_changed": "...", ... },
  "translations": {
    "tr": { "status": "mt",      "headline": "...", ... },
    "ru": { "status": "human",   "headline": "...", ... },
    "ar": { "status": "human",   "headline": "...", ... },
    "vi": { "status": "mt",      "headline": "...", ... },
    "pl": { "status": "mt",      "headline": "...", ... }
  },
  "sources": [ "https://..." ]
}
```

- `status: "mt"`  → maschinell übersetzt, Banner "automatisch übersetzt — bitte mit
  offizieller Quelle abgleichen".
- `status: "human"` → von geprüfter Person/freiwilliger Muttersprachler:in übersetzt,
  Banner "geprüfte Übersetzung".

## Kuratierungs-Workflow (TR/RU/AR hochstufen)

1. **Meldung auswählen.** Die ~10 wichtigsten Meldungen pro Woche (höchster
   Bürger:innen-Impact, z.B. Wohngeld, Bürgergeld, Elterngeld).
2. **Übersetzen.** Muttersprachler:in oder geprüfter Agent übersetzt DE→Zielsprache.
   Fakten und Zahlen müssen exakt bleiben (keine Zusammenfassung).
3. **Freigeben.** Eintrag im `translations`-Feld mit `status: "human"` ablegen.
4. **Haftungshinweis.** Jede kuratierte Übersetzung trägt: "Geprüfte Übersetzung der
   deutschen Originalmeldung. Verbindliche Auskunft gibt die genannte Quelle."

## Finanzierung

Die kuratierten Übersetzungen (v.a. TR/RU/AR) sind das Kernargument für
**B2B-Lizenzen an Stiftungen & Verbraucherzentralen**: sie erreichen genau die
Communities, die Deutsch am wenigsten beherrschen. Die "Für Organisationen"-Seite
verkauft nicht "wir zeigen's auf Türkisch", sondern "wir erreichen die türkische
Community vertrauenswürdig".

## Skalierung

Neue Sprache = neues Feld unter `translations`, kein Refactor der Seite. Start als
`mt`, Hochstufung zu `human`, sobald Traffic/Nachfrage da ist.
