# Gerichteter Spannbaum – die Arboreszenz (Chu-Liu/Edmonds) – Streamlit-Demo

Fünftes Stück der **Spannbaum-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning". Bisher waren alle Kosten symmetrisch. Hat eine Leitung **Fließrichtung** - bergauf wird Pumpenergie fällig, bergab nicht, manche Trassen sind Einbahnen -, dann zählt jeder **Bogen** einzeln: gesucht ist der billigste **Verteilbaum ab einer Wurzel** (dem Werk), in dem jeder andere Standort genau **einen Zulauf** hat und alle vom Werk aus erreichbar sind, eine **minimale Arboreszenz**. Kruskal und Prim sind für ungerichtete Kanten gebaut und liefern hier nicht mehr das Optimum, oft gar keinen Baum. Der richtige Algorithmus ist **Chu-Liu/Edmonds**: je Knoten den billigsten Zulauf wählen; bilden diese Kreise, den Kreis zu einem Superknoten **kontrahieren**, die Kosten der Bögen in ihn um den Kreisbogen senken und von vorn beginnen, am Ende rückwärts expandieren. Die Demo misst, **was das Ignorieren der Richtung kostet**, wie oft und wie tief die Kontraktion nötig ist, was **Einbahn-Trassen** anrichten und was die **freie Wurzel** spart. Kruskal und Prim aus [kruskal-demo](../kruskal-demo) und [prim-demo](../prim-demo) laufen als naive Vergleichsverfahren mit.

**Einordnung in die Reihe:** geplant sind elf Stücke, dies ist das fünfte:

```
Kruskal (Wurzel)                                                                           [gebaut: kruskal-demo]
 ├─ Prim (Kontrast: wächst von einem Punkt)                                                [gebaut: prim-demo]
 ├─ Borůvka (Kontrast: alle Komponenten parallel)                                          [gebaut: boruvka-demo]
 ├─ Euklidischer MST (keine n²-Kantenliste, Delaunay)                                      [gebaut: euclidean-mst-demo]
 ├─ Gerichteter Spannbaum (Chu-Liu/Edmonds)                                                [DIESES STÜCK]
 ├─ Bottleneck-/Grad-/Hop-beschränkter Spannbaum → Kapazitierter MST                       [nicht gebaut]
 ├─ Steiner-Baum → Prize-Collecting Steiner-Baum                                           [nicht gebaut]
 ├─ MST-Sensitivität & dynamischer MST                                                     [nicht gebaut]
 └─ Zufällige Spannbäume & Kirchhoff                                                       [nicht gebaut]
```

Ergebnis in Kürze: **Die Richtung zu ignorieren kostet erst bei starker Steigung viel (5,8 % bei α = 3), Einbahn-Trassen brechen die naive Antwort aber sofort (ab 10 % Einbahn-Anteil in 80 % der Instanzen kein gültiger Baum); der billigste Zulauf je Knoten enthält immer Kreise, die Kontraktion wächst mit n, und im Worst Case braucht der Algorithmus n − 1 Ebenen.** Das Optimum ist bewiesen (Brute-Force, networkx, Dualwert = Baumkosten). Der Kürzeste-Wege-Baum ist keine Alternative: er ist 70 bis 87 % teurer, weil er jeden einzelnen Weg statt der Summe minimiert.

| Frage | Ergebnis (30 Knoten, k = 6 nächste Nachbarn, Steigungsaufschlag α = 0,5, keine Einbahnen, Wurzel = Werk, sofern nicht anders angegeben; **Median** über 5 feste Instanzen, Seeds 100000–100004; vollständig deterministisch) |
|---|---|
| **Ist Chu-Liu/Edmonds optimal?** | ✅ ja, direkt geprüft: gleich Brute-Force auf 120 zufälligen Kleingraphen (auch nicht lösbaren: dann erkannt) und gleich `networkx.minimum_spanning_arborescence` auf 200 zufälligen Graphen; der **Dualwert** (Summe der in allen Ebenen abgezogenen Mindest-Zulaufkosten) ist auf jeder Instanz gleich den Baumkosten |
| **Was kostet es, die Richtung zu ignorieren?** | Mehrkosten der naiven Antwort (ungerichteter MST auf den Leitungslängen, von der Wurzel aus orientiert) bei α = 0/0,25/0,5/1/2/3: **0,00/0,00/0,18/1,38/3,73/5,79 %**; gerichtetes Prim **0,00/0,00/0,00/0,84/5,65/11,6 %**; Kürzeste-Wege-Baum **67,9/69,3/69,6/71,4/79,7/86,7 %**. Bei α = 0 (symmetrisch) ist der Kruskal-Baum exakt optimal - Chu-Liu/Edmonds kontrahiert dort trotzdem (im Mittel 22,0 Kreise) |
| **Einbahn-Trassen** | Anteil q der Knotenpaare mit nur einer Richtung 0/0,1/0,2/0,4/0,6: "Kruskal orientiert" liefert **in 0/80/100/100/100 % der Instanzen keinen gültigen Baum** (ein benötigter Bogen fehlt); gerichtetes Prim ist immer gültig, aber 0,00/0,12/1,46/3,92/6,32 % teurer als das Optimum |
| **Kreise unter den billigsten Zuläufen** | in **100 %** der Instanzen mindestens einer (50 Instanzen: im Mittel 8,1, höchstens 11), **alle der Länge 2** (zwei Nachbarn wählen einander); Kontraktionen im Mittel 20,8 (höchstens 28), höchstens 18 Ebenen |
| **Wie viele Ebenen?** | ⚠️ wachsen mit n (Erwartung "kaum" widerlegt): n = 10/20/40/80/120: **4/6/10/18/17** Ebenen, 5/12/27/65/97 Kontraktionen, 5,9/9,3/12,3/20,5/18,9 Elementarschritte je Bogen |
| **Worst Case** | geschachtelte Instanz: n = 5/10/20/40/80 braucht genau **n − 1 Ebenen** und 41/206/911/3821/15 641 Elementarschritte (quadratisch) |
| **Freie Wurzel** | beste Wurzel gegenüber dem Werk im Median **1,69 %** billiger (α = 0,5), bei α = 3 **8,60 %**, bei α = 0 nichts; dafür läuft der Algorithmus für jede mögliche Wurzel (Standardinstanz: 59 052 statt 1772 Elementarschritte) |

## Was die Demo zeigt

1. **Chu-Liu/Edmonds in Aktion** (Schritt-Slider): **Instanz** (gerichtete Bögen mit Pfeilspitzen, Wurzel als Stern) → **Billigster Zulauf** (je Knoten der billigste Zulauf blau, Kreise rot; Text mit Kosten und Zahl der Kreise) → **Kontraktion** (Slider über die Ebenen: Punktfarbe = Superknoten, gewählte Zuläufe blau, Kreise rot umrandet; Text mit Knoten, Bögen, abgezogenen Kosten und dem Stand des Dualwerts) → **Ergebnis** (Umschalter Optimum / Kruskal orientiert / Prim gerichtet / Kürzeste-Wege-Baum: grün = wie das Optimum, orange = weicht ab, grau gestrichelt = Optimum-Bogen fehlt; ist ein Verfahren ungültig, steht der Grund da, z. B. "Bogen 19→5 fehlt (Einbahn)"; darunter die Mehrkosten als Balken).
2. **Was kostet die Richtung?** Optimum, Ebenen und Kontraktionen, Mehrkosten von Kruskal (orientiert) und Prim (gerichtet), Elementarschritte je Bogen, Dualwert = Baumkosten, ggf. die beste Wurzel.
3. **🎲 Machbarkeits-Experiment** (auf Abruf): 50 Instanzen - Anteil ohne gültigen Baum, Kreise unter den billigsten Zuläufen, Kontraktionen.
4. **🌐 Die beste Wurzel** (auf Abruf): Ersparnis über 5 Instanzen.
5. **📐 Sweeps** über α, Einbahn-Anteil, n und k (Mehrkosten der Verfahren, Anteil ungültig, Ebenen und Kontraktionen, Schritte je Bogen; 5 feste Instanzen, Median, 10.–90. Perzentil-Band).
6. **🧱 Der Worst Case** (auf Abruf): Ebenen und Schritte an der geschachtelten Instanz.
7. **🚧 Grenzen:** Tabelle "Annahme – was passiert – wer setzt an".

Regler: Instanz (Karte / **Lehrbuchbeispiel** / **Geschachtelt**), Knoten n (5–120), k (3 bis 20), **Steigungsaufschlag α** (0 = symmetrisch bis 3), **Einbahn-Anteil q** (0 bis 60 %), Seed (+ 🎲), **Wurzel** (Werk / beste Wurzel). Alle Regler wirken auf Kosten, Bögen oder Wurzel; Fixtures blenden die Kartenregler aus. Kein Zufall im Kern.

## Messwerte der Presets

| Preset | Instanz | Ergebnis |
|---|---|---|
| Standardfall (Voreinstellung) | 30 Knoten, k = 6, Seed 35, α = 0,5 | Optimum 392,23; 7 Ebenen, 23 Kontraktionen, 10 Zweier-Kreise im billigsten Zulauf; Kruskal orientiert +1,09 %, Prim +1,09 %, Kürzeste-Wege-Baum +87,1 % |
| Symmetrisch (α = 0) | | Optimum 375,50, Kruskal-Lücke 0; trotzdem 24 Kontraktionen in 7 Ebenen |
| Starke Steigung (α = 3) | | Optimum 432,72; Kruskal +15,9 %, Prim +17,9 %, Kürzeste-Wege-Baum +104,5 % |
| Einbahn-Trassen (q = 0,4) | | Optimum 410,42; "Kruskal orientiert" ungültig (Bogen 19→5 fehlt), Prim gültig und hier optimal |
| Freie Wurzel | | Knoten 12 statt Werk: 388,85 statt 392,23 (0,86 % billiger); 59 052 statt 1772 Elementarschritte |
| Lehrbuchbeispiel | 5 Knoten, 8 Bögen | Abzüge 14 + 1 + 2 = 17 = Optimum (Dualwert); Kruskal orientiert 19; 3 Ebenen, 40 Elementarschritte |
| Geschachtelt (Worst Case) | n = 20 | 19 Ebenen, 18 Kontraktionen, 911 Elementarschritte, Kosten 218 |
| Große Instanz (n = 120) | 872 Bögen | 22 Ebenen, 105 Kontraktionen, 17 209 Elementarschritte; Kruskal +0,05 %, Kürzeste-Wege-Baum +83,5 % |

Das **Lehrbuchbeispiel** ist von Hand nachzurechnen: Schritt 1 wählt für B, C, D, E die Zuläufe D→B (3), D→C (2), C→D (8), C→E (1) (Summe 14) und findet den Kreis C↔D; nach der Kontraktion zu {C, D} bleibt B↔{C, D} (Abzug 1) und schließlich A→{B, C, D} (Abzug 2). Expandiert entstehen A→C (5), C→D (8), D→B (3), C→E (1) = 17. Die einzelne Instanz weicht von den Medianen ab - die Mediane sind die belastbaren Zahlen; die Karten-Presets prüfen sich zusätzlich über die 5 festen Instanzen gegen eine gemessene Spannweite des Medians der optimalen Kosten (`tests/test_presets.py`).

## Modell und Verfahren

- **Instanz** (`arb_scenario.py`): n Standorte im Quadrat, Knoten 0 (das Werk) fest links; ein glattes Höhenfeld aus drei Gauß-Hügeln; Kandidaten sind die k nächsten Nachbarn je Knoten, jede Verbindung als zwei Bögen. Kosten u → v = Länge + α · max(0, Höhe(v) − Höhe(u)). Mit dem Einbahn-Anteil q hat jedes Knotenpaar mit Wahrscheinlichkeit q nur eine zufällige Richtung; die Erreichbarkeit von der Wurzel wird durch Wiederherstellen entfernter Gegenrichtungen garantiert, damit alle Instanzen lösbar sind. Zwei Fixtures (Lehrbuch, geschachtelt).
- **Chu-Liu/Edmonds** (`arb_algorithm.py`): iterativ, Ebene für Ebene. Je Ebene: billigster Zulauf je Knoten, Abzug seiner Kosten von allen Bögen in den Knoten, Kreissuche über Zeiger, Kontraktion und Umbenennung; am Ende Expansion rückwärts über die Ebenen (der in einen Superknoten führende Bogen ersetzt den Kreisbogen an seinem Zielknoten). `dual` = Summe aller Abzüge. Eine einfache O(n·m)-Umsetzung; Tarjan (1977) und Gabow u. a. (1986) sind nicht gebaut.
- **Vergleichsverfahren:** *Kruskal orientiert* = ungerichteter MST auf den Leitungslängen (Kruskal-Kopie), von der Wurzel aus orientiert, je Kante der billigste passende Bogen, ungültig, wenn er fehlt; *Prim gerichtet* = vom Baum aus immer den billigsten Bogen zu einem neuen Knoten; *Kürzeste-Wege-Baum* = Dijkstra ab der Wurzel; *billigster Zulauf* = Schritt 1 allein.
- **Beste Wurzel:** Chu-Liu/Edmonds für jede Wurzel, von der alle erreichbar sind; die billigste gewinnt (bei Gleichstand die kleinste). Gegenprobe: virtuelle Wurzel mit großem Bogenpreis.
- **Elementarschritte:** je Ebene alle Bögen prüfen + Zeigerschritte der Kreissuche + alle Bögen umbenennen und reduzieren. Ein Näherungsmaß, **keine Laufzeit**.

## Was nicht funktioniert hat / Grenzen

- **Erwartung "die Ebenen wachsen kaum mit n" - widerlegt:** 4/6/10/18/17 Ebenen bei n = 10/20/40/80/120; die Schritte je Bogen wachsen von 5,9 auf 18,9. Im Worst Case sind es n − 1 Ebenen und quadratisch viele Schritte.
- **Erwartung "Kruskal/Prim liefern ungültige Bäume" - nur mit Einbahnen wahr:** bei symmetrischen und gerichteten Kosten mit beiden Richtungen liefert die orientierte Antwort immer einen gültigen (nur teureren) Baum; erst fehlende Richtungen machen sie ungültig. Gerichtetes Prim ist immer gültig (aber bei starker Steigung teurer als die orientierte Kruskal-Antwort: 11,6 % gegen 5,79 % bei α = 3).
- **Elementarschritte sind keine Laufzeit:** die schnelleren Umsetzungen sind nicht gebaut; die Heuristiken werden nur nach Kosten verglichen, nicht nach Schritten.
- **Synthetisches Modell:** Steigungsaufschlag und Einbahnen sind ein Modell (Punkte im Quadrat, drei Gauß-Hügel, k nächste Nachbarn); keine Kapazitäten, keine echten Rohrnetze. Die Wurzelwahl nutzt n Läufe; ein Wald ohne feste Wurzel (Minimum Branching) ist nicht gebaut.
- **Nicht gebaut:** Grad-/Hop-beschränkter und Kapazitierter MST, Steiner-Bäume, Sensitivität, zufällige Spannbäume.

## Verifikation

- **Optimalität direkt:** gleich Brute-Force (alle Zulauf-Auswahlen) auf 120 zufälligen Kleingraphen mit Gleichständen, parallelen Bögen und nicht lösbaren Fällen; gleich networkx auf 200 zufälligen Graphen (per virtueller Wurzel) und auf allen Fixtures und generierten Instanzen; Dualwert = Baumkosten; jede Ausgabe ist eine gültige Arboreszenz (n − 1 Bögen, je Knoten ein Zulauf, alle erreichbar); nicht lösbare Instanzen werden erkannt.
- **Kontraktion von Hand:** Lehrbuchbeispiel (welche Kreise, welche Abzüge 14/1/2, welche Mitglieder, welche Expansion, 40 Elementarschritte nachgezählt); geschachtelte Instanz mit genau n − 1 Ebenen und quadratischem Aufwand.
- **Symmetrie:** bei α = 0 und q = 0 sind die Kosten gleich dem ungerichteten MST (Kruskal-Kopie) und die Lücke der orientierten Antwort ist genau 0; mit α > 0 Instanzen mit positiver Lücke.
- **Vergleichsverfahren und Wurzelwahl:** Prim und Kürzeste-Wege-Baum gültig und nie billiger als das Optimum; "Kruskal orientiert" genau dann ungültig, wenn eine Richtung fehlt (Handbeispiel); beste Wurzel = Minimum über alle Wurzeln = virtuelle Wurzel; Sonderfälle (n = 1, n = 2, Wurzel ohne ausgehenden Bogen, parallele Bögen, Schleifen, Bögen in die Wurzel, alle Kosten gleich).
- **Alle Zahlen der App-Texte sind als Tests hinterlegt**, über dieselben Auswertungsfunktionen wie die App selbst (`ev.run_config`/`ev.sweep`/`ev.feasibility`/`ev.nested_levels`), NIE über ein Ad-hoc-Skript; Schrittzahlen und Ebenen sind ganzzahlig; AppTest-Rauchtests (Voreinstellung, jedes Preset, jeder Schritt und jede Ebene, alle Instanztypen und Bäume, Extremwerte, Würfel, Permalink-Grenzen, Instanzwechsel, Experimente und Sweeps auf Abruf, Footer). networkx nur als Gegenprobe in `requirements-dev.txt`.

Literatur: Chu, Y. J., & Liu, T. H. (1965). *On the shortest arborescence of a directed graph.* Scientia Sinica 14, 1396-1400. Edmonds, J. (1967). *Optimum branchings.* Journal of Research of the National Bureau of Standards 71B, 233-240. Tarjan, R. E. (1977). *Finding optimum branchings.* Networks 7(1), 25-35. Gabow, H. N., Galil, Z., Spencer, T., & Tarjan, R. E. (1986). *Efficient algorithms for finding minimum spanning trees in undirected and directed graphs.* Combinatorica 6(2), 109-122.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: Instanz, vier Schritte, Aufwand, Experimente auf Abruf, Sweeps, Grenzen, Mathe |
| `arb_algorithm.py` | Chu-Liu/Edmonds (Ebenen, Expansion, Dualwert), Vergleichsverfahren, beste Wurzel |
| `arb_undirected.py`, `arb_unionfind.py` | Kruskal, Prim, Heap, Sortierung, Union-Find (aus den Vorgänger-Demos) für die naive Antwort |
| `arb_scenario.py` | Instanzen (Karte mit Höhenfeld, Lehrbuch, geschachtelt) |
| `arb_constants.py` | Konstanten, Presets, gemessene Werte |
| `arb_evaluation.py` | Kennzahlen, Sweeps, Machbarkeits-Experiment, Worst Case |
| `arb_presets.py`, `arb_visualization.py` | Permalink/Presets (gespeicherte Werte plus Widget-Schlüssel), Plotly-Figuren mit Pfeilspitzen |
| `tests/` | Korrektheitskette (Brute-Force, networkx, Dualwert), Szenario/Auswertung, Aussagen der App, Presets, AppTest |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
