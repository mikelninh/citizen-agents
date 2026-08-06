# Citizen Agents — Brand Design System

**Stand: 2026-08-06 · Version 0.9 (Entwurf zur Diskussion)**

---

## 1. Die Markenidee

> **„Wir beobachten. Wir verifizieren. Du entscheidest."**

Citizen Agents ist die erste Anlaufstelle für Rechte — die Marke muss auf einen Blick
vermitteln: **Wachsamkeit (watchdog), Verifikation (prüfbar), Bürgernähe (dein Recht).**

Drei Begriffe tragen die Marke:
- **Auge** — wir beobachten das Mächtige, für dich
- **Haken/Stempel** — alles ist geprüft, verifizierbar, nachweisbar
- **Zeitung/Leuchtturm** — verständlich, seriös, mit Quellen

---

## 2. Das Logo: „Das prüfende Auge"

Ein Auge, in dessen Pupille ein Haken sitzt. Zwei Bedeutungen in einem Zeichen:
- Das **Auge** = die Wächter, die niemals schlafen
- Der **Haken** = Verifizierbarkeit als Bürgerrecht — jede Meldung geprüft

```
   ┌───────────────┐
   │   ╭───────╮   │
   │  (   ●✓   )  │   ← Auge + Haken in der Pupille
   │   ╰───────╯   │
   └───────────────┘
```

**Regeln:**
- Das Mark steht immer in einem abgerundeten Quadrat (Rounded-Square, 22% Radius)
- Verlauf: `#533afd` → `#f96bee` (lila → magenta) — der Signature-Verlauf
- Wortmarke daneben: „Citizen Agents" in Source Sans 3, 600, `#061b31`
- Kleinste Größe: 20px (dann nur das Mark, ohne Wort)
- Favicon = das Mark allein

**SVG-Grundform:**
```svg
<svg viewBox="0 0 48 48">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#533afd"/><stop offset="1" stop-color="#f96bee"/>
  </linearGradient></defs>
  <rect width="48" height="48" rx="11" fill="url(#g)"/>
  <path d="M6 24 C12 12 36 12 42 24 C36 36 12 36 6 24 Z" fill="none" stroke="#fff" stroke-width="2.4"/>
  <circle cx="24" cy="24" r="7.5" fill="#fff"/>
  <path d="M20.5 24 L23 26.5 L27.8 21.4" stroke="url(#g)" stroke-width="3" fill="none"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

---

## 3. Farbsystem

| Rolle | Wert | Einsatz |
|---|---|---|
| Primär (Action) | `#533afd` | Buttons, Links, Fokus |
| Primär Hover | `#4434d4` | Hover-Zustände |
| Signature-Verlauf | `#533afd → #f96bee` | Logo, Hero-Beam, Highlights |
| Headline | `#061b31` (Deep Navy) | Überschriften (nie reines Schwarz) |
| Text | `#273951` | Fließtext |
| Sekundärtext | `#64748d` | Beschreibungen |
| Border | `#e5edf5` | Karten, Trennlinien |
| Verifiziert | `#15be53` / Text `#108c3d` | Status „verifiziert" |
| Teilweise | `#9b6829` (Lemon) | Status „teilweise belegt" |
| Fehler/Rot | `#ea2261` | Warnung, Korrekturhinweis |
| Dunkle Sektion | `#1c1e54` | Prinzip-Block, Footer-Kontrast |

**Schatten:** immer blaustichig — `rgba(50,50,93,0.25)` — nie neutral-grau.

---

## 4. Typografie

| Rolle | Schrift | Größe/Gewicht |
|---|---|---|
| Display | Source Sans 3 · 300 | 54px, -1.3px tracking |
| Headline | Source Sans 3 · 300 | 32px, -0.64px |
| Signatur-Phrase | **Newsreader Italic** · 300 | kursiv, für das „emotionale" Wort |
| Text | Source Sans 3 · 300–400 | 16px |
| UI/Buttons | Source Sans 3 · 400 | 14px |
| Mono (Daten) | Source Code Pro | Tabellenzahlen, Status |

**Die Signatur-Phrase:** In der Headline wird genau EIN Wort kursiv-serif gesetzt —
das emotionale: *„Dein Recht. Dein Geld. **Deine Frage.**"* Das ist der Marken-Tick.

---

## 5. Bildsprache & Motive

1. **Der Beam** — ein weicher Verlaufsstrahl (lila→magenta, radial, 8–10% Deckkraft)
   hinter der Hero-Headline: „der Leuchtturm beleuchtet dein Recht"
2. **Der Prüfstempel** — ein runder Stempel „GEPRÜFT" / „VERIFIED" als SVG mit
   doppeltem Ring — erscheint bei verifizierten Meldungen, wie ein offizieller
   Dokumentenstempel. Vertrauen als *physisches* Motiv.
3. **Status-Badges** — VERIFIZIERT (grün), TEILWEISE (lemon), KORRIGIERT (rot):
   Ehrlichkeit als Design-Element, nicht als Fehler.
4. **Quellen-Zeile** — jede Meldung endet mit „Quelle: …" in Mono — der
   journalistische Beleg, immer sichtbar.

---

## 6. Ton (Voice)

| Statt | Sagen |
|---|---|
| „Unsere Agenten überwachen Gesetze" | „Wir beobachten, was mit deinem Recht passiert." |
| „Kostenlos" | „0 € für dich. Für immer." |
| „Transparent" | „Jede Meldung mit Quelle. Sieh selbst." |
| „Fehler möglich" | „Geprüft, gemeldet, korrigierbar — das ist das System." |

**Claim-Linien:**
- Primär: **„Dein Recht. Dein Geld. Deine Frage."**
- Sekundär: **„Wir beobachten. Du entscheidest."**
- Lang: **„Recht auf dem Papier → Recht im Leben."**

---

## 7. Was fehlt bis v1.0

- [ ] Logo in allen Formaten (SVG/PNG/Favicon/App-Icon)
- [ ] Briefkopf / Social-Media-Vorlagen
- [ ] Icon-Set der 18 Wächter (einheitlich, gleiche Linienstärke)
- [ ] Motion: Beam-Animation in der Hero (sanftes Pulsieren)
- [ ] Barrierefreiheit: Kontrast-Check (BITV 2.0) — Pflicht für den öffentlichen Auftritt

*Digital Democracy Studio, Berlin — 2026. Das Auge wacht, der Haken prüft, du entscheidest.*
