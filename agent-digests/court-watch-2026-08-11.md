# ⚖️ Court-Watch — 2026-08-11

Wache für Bürgerrechte: **Landmark-Entscheidungen von BVerfG und EuGH, die den Alltag verändern.** Jeder Eintrag nennt Quelle und (falls betroffen) das Citizen-Tool, das nachgebessert werden sollte.
**6 Entscheidungen in diesem Lauf** — 3× EuGH, 3× BVerfG.

---

## 1. EuGH (C-234/25, 09.07.2026): Streaming-Abos dürfen das Widerrufsrecht nicht wegnehmen
- **Was passiert ist:** Sky Österreich wollte in der AGB-Klausel, dass das Widerrufsrecht (14 Tage Bedenkzeit) verfällt, sobald das Streaming während der Frist startet. Der EuGH stellt klar: Ein Streaming-Dienst, der Inhalte dynamisch an das Nutzerverhalten anpasst (Empfehlungen, personalisierte Profile), ist eine **digitale Dienstleistung**, kein bloß „digitaler Inhalt“. Bei einer Dienstleistung darf das Widerrufsrecht **nicht** durch Vorab-Zustimmung ausgeschlossen werden.
- **Was sich für Bürger ändert:** Wer Netflix, Sky, Disney+ & Co. abschließt, hat bei dynamisch angepassten Angeboten eine echte 14-tägige Bedenkzeit — auch wenn gestreamt wurde (anteilige Nutzungsentschädigung schuldet nur, wer ausdrücklich Sofort-Start verlangt hat).
- **Tool-Hinweis:** `agb-reader` — Klauseln, die das Widerrufsrecht für Streaming-Abos pauschal ausschließen, sind nach dieser Linie **unwirksam** und sollten vom Reader rot geflaggt werden.
- **Sources:**
  - https://curia.europa.eu/site/upload/docs/application/pdf/2026-07/cp260097de.pdf
  - https://dejure.org/dienste/vernetzung/rechtsprechung?Gericht=EuGH&Datum=09.07.2026&Aktenzeichen=C-234%2F25

## 2. EuGH (C-45/24, 15.01.2026): Bei Flugausfall volle Erstattung — inkl. Reisebüro-Provision
- **Was passiert ist:** KLM stornierte einen über Opodo gebuchten Flug und zahlte nur den Ticketpreis, nicht die ~95 € Vermittlungsgebühr. Der EuGH: Die Erstattung nach Fluggastrechte-VO muss **auch die Provision des Vermittlers** umfassen, wenn die Airline dessen Verkauf in ihrem Namen duldet. Die Airline muss die genaue Provisionshöhe dabei nicht kennen — die Provision ist „unvermeidbarer“ Teil des Ticketpreises.
- **Was sich für Bürger ändert:** Bei Annullierung/ Nichtbeförderung gehört die komplette Zahlung zurück — auch Online-Reisebüro-Gebühren. Wer nur den Netto-Ticketpreis erstattet bekommt, kann die Buchungsgebühr separat einfordern.
- **Tool-Hinweis:** `flight-rights-mcp` (EU261) — die Erstattungsberechnung muss die Vermittlerprovision einschließen; der Bot sollte Buchungsgebühren explizit als erstattungsfähig ausweisen.
- **Sources:**
  - https://www.beck-aktuell.de/heute-im-recht/rechtsprechung/eugh-c4524-flugannullierung-airline-vermittlerprovision-erstattung-opodo-2026-01-15
  - https://eur-lex.europa.eu/legal-content/DE/TXT/PDF/?uri=CELEX:62024CJ0045

## 3. EuGH (C-526/24, 19.03.2026): DSGVO-Auskunftsanspruch darf nicht als Abmahn-Fabrik missbraucht werden
- **Was passiert ist:** Eine Person meldete sich systematisch bei Newslettern an, forderte dann Auskunft nach DSGVO und verlangte Schadensersatz (≥ 1.000 €). Der EuGH: Ein Auskunftsantrag kann schon beim **ersten** Mal „exzessiv“ und missbräuchlich sein, wenn er allein dazu dient, künstlich Schadensersatzansprüche zu erzeugen — erkennbar z. B. an einer Serie gleichartiger Anträge gefolgt von Forderungen.
- **Was sich für Bürger ändert:** Das Auskunftsrecht (Art. 15 DSGVO) bleibt voll intakt für ordentliche Anfragen. Aber: Wer es nur als Hebel für pauschale Schadensersatzklagen nutzt, geht leer aus. Bürger sollten Auskunft ernsthaft zur Prüfung der Datenverarbeitung nutzen.
- **Sources:**
  - https://www.datev-magazin.de/nachrichten-steuern-recht/recht/eugh-stoppt-dsgvo-abmahnstrategie-durch-auskunftsantraege-145515
  - https://curia.europa.eu/site/upload/docs/application/pdf/2026-02/cp260011de.pdf

## 4. BVerfG (2 BvR 319/26, PM 46/2026, 24.07.2026): Pauschales Streichen der Afghanistan-„Menschenrechtsliste“ verfassungswidrig
- **Was passiert ist:** Die neue Koalition beendete freiwillige Aufnahmeprogramme; das BMI erklärte im Dezember 2025 alle Aufnahmezusagen der „Menschenrechtsliste“ pauschal für „ungültig und erloschen“. Das BVerfG gibt der Verfassungsbeschwerde einer afghanischen Mutter mit zwei Kindern statt: Eine solche **pauschale** Abkehrerklärung verstößt gegen das Willkürverbot — sie muss im Einzelfall, mit Blick auf die individuellen Belange, ergehen. Die Bundesrepublik muss die Unterstützung in Pakistan bis zu einer verfassungsmäßigen Entscheidung fortsetzen.
- **Was sich für Bürger ändert:** Staatliche Zusagen (auch humanitäre Aufnahme) dürfen nicht kollektiv und ohne Einzelfallprüfung annulliert werden. Wer eine rechtskräftige Zusage hat, kann sich auf den Rechtsstaat berufen — pauschale „alle erloschen“-Erklärungen sind angreifbar.
- **Sources:**
  - https://www.bundesverfassungsgericht.de/SharedDocs/Pressemitteilungen/DE/2026/bvg26-046.html
  - https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/2026/07/rs20260722_2bvr031926.html

## 5. BVerfG (2 BvC 20/26, PM 51/2026, 06.08.2026): Bundestag muss Wahlprüfung zügig und sachgerecht machen
- **Was passiert ist:** Der 2. Senat verwirft eine Wahlprüfungsbeschwerde, rügt aber scharf das Tempo des Bundestags: 15 Monate nach der Bundestagswahl 2025 hatte der 21. Bundestag von ~1.000 Einsprüchen nur 450 erledigt (der 20. schaffte ~2.000 in 14 Monaten). Das verfehle den verfassungsrechtlichen Zweck der Wahlprüfung (Art. 41 Abs. 1 GG); der Bundestag ist zu zeitnaher, sachgerechter Bearbeitung verpflichtet.
- **Was sich für Bürger ändert:** Das Wahlprüfungsverfahren ist ein demokratisches Recht — Wählerinnen und Wähter können Einspruch einlegen, und der Bundestag muss diesen ernsthaft und zügig nachgehen. Die Entscheidung stärkt die Kontrolle der Wahllegitimation.
- **Sources:**
  - https://www.bundesverfassungsgericht.de/SharedDocs/Pressemitteilungen/DE/2026/bvg26-051.html
  - https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/2026/07/cs20260723_2bvc002026.html

## 6. BVerfG (1 BvR 183/25, PM 12/2026, 17.02.2026): Verlängerung der Mietpreisbremse ist verfassungsgemäß
- **Was passiert ist:** Eine Berliner Vermieterin wehrte sich gegen die Verlängerung der Mietpreisbremse (§ 556d BGB: Miete darf bei Neuvermietung in angespannten Märkten die ortsübliche Vergleichsmiete höchstens um 10 % übersteigen). Die 2. Kammer des 1. Senats nimmt die Beschwerde nicht zur Entscheidung an: Weder die Regelung noch die Berliner Begrenzungsverordnung verletzen die Eigentumsgarantie; die Verlängerung ist verfassungsgemäß.
- **Was sich für Bürger ändert:** Die Mietpreisbremse bleibt wirksam — Mieter in angespannten Wohnungsmärkten dürfen bei Neuvermietung nicht mehr als 10 % über der Vergleichsmiete zahlen; zu hohe Mieten sind rügbar. (Hinweis: Die Länderverordnungen sind befristet — Stand 2025 war das Ende auf den 31.12.2025 gesetzt; Mieter sollten aktuelle Landesregelung prüfen.)
- **Tool-Hinweis:** `agb-reader` / Mietrecht — bei neuen Mietverträgen in Gebieten mit Mietpreisbremse ist eine um >10 % über Vergleichsmiete liegende Miete angreifbar.
- **Sources:**
  - https://www.bundesverfassungsgericht.de/SharedDocs/Pressemitteilungen/DE/2026/bvg26-012.html
  - https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/2026/01/rk20260108_1bvr018325.html

---

*Hinweis: Alle Entscheidungen sind real und per Quellen-URL verifiziert (BVerfG-Presseservice, Curia/EuGH, beck-aktuell, DATEV, dejure). Keine PR- oder KI-erfundenen Inhalte.*
