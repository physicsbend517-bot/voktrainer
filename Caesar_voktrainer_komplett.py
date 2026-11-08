# -*- coding: utf-8 -*-
"""
Caesar Vokabeltrainer 2.0
Alle Vokabeln aus "Lernvokabular Caesar Grundwortschatz.pdf"
(Kleine Wörter + Caesar-Wortschatz bis "Caesare imperante").

Start:
    python caesar_vokabeltrainer.py

Keine externen Pakete nötig (nur Standardbibliothek + tkinter).
Der Lernfortschritt wird in "caesar_fortschritt.json" neben dem Skript gespeichert.

Neu gegenüber Version 1:
  * Alle Vokabeln der PDF, sortiert nach Kapiteln (frei kombinierbar)
  * Leitner-Karteikasten (5 Boxen) mit Wiederholungsterminen (Spaced Repetition)
  * 3 Lernmodi: Eintippen, Multiple Choice, Karteikarten
  * Falsche Vokabeln kommen in der Sitzung automatisch bald wieder
  * Schrittweise Hinweise, "Als richtig werten", Zeitlimit, Favoriten
  * Vokabelliste mit Suche/Filter, Statistik, 7-Tage-Diagramm, Lerntage-Serie
  * Heller und dunkler Modus, dauerhaft gespeicherter Fortschritt
"""

import copy
import json
import random
import re
import time
import tkinter as tk
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from tkinter import ttk, messagebox, filedialog, font as tkfont

APP_TITLE = "Caesar Vokabeltrainer"
try:
    _BASE_DIR = Path(__file__).resolve().parent
except NameError:  # z. B. in Notebooks, IDLE-Shell oder Online-Editoren
    _BASE_DIR = Path.cwd()
SAVE_FILE = _BASE_DIR / "caesar_fortschritt.json"

# ----------------------------------------------------------------------------
# VOKABELN   (Format:  Latein :: Deutsch      Überschriften:  ## Kapitel)
# ----------------------------------------------------------------------------
RAW_DATA = r"""
## 1 Pronomen & Zahlwörter
hic, haec, hoc :: dieser
ille, illa, illud :: jener
iste, ista, istud :: dieser da (immer verächtlich gemeint)
ipse, ipsa, ipsum :: selbst; persönlich; gerade; eben
se (eum, eam, id; eos, eas; ea = nicht refl.), me, te, nos, vos :: Personalpronomina – können auch Subjektsakkusativ beim AcI sein!
sibi (Dat.) :: sich
inter se :: untereinander; einander
is, ea, id :: er; sie; es
eius; eorum, earum, eorum :: Possessivpronomina: sein; ihr; ihre
ea, quae (n. Pl.) :: das, was … (im Deutschen: Singular)
meus, tuus, noster, voster :: mein; dein; unser, euer (Possessivpronomina)
nostri (nominalisiert) :: die Unseren; die Unsrigen (nominalisiert)
sui (nominalisiert) :: die Seinen; die Seinigen (nominalisiert)
idem, eadem, idem :: derselbe, dieselbe, dasselbe
quisque, quaeque, quidque :: jeder, jede, jedes
aliquis, aliquis, aliquid :: jemand (Subst.)
aliqui, aliqua, aliquod :: irgendein (Adj.)
unus – alius – tertius :: der eine – der andere – der dritte
primus – secundus – tertius :: der erste – der zweite – der dritte
una ex parte – altera ex parte – tertia ex parte (= ex una parte …) :: von der einen Seite – von der anderen Seite – von der dritten Seite
una cum :: zusammen mit
primum :: als erstes
deinde :: dann
prima hora, secunda hora, tertia hora :: zur ersten, zweiten, dritten Stunde
prima vigilia, secunda vigilia, tertia vigilia :: zur ersten, zweiten, dritten Nachtwache

## 2 Adjektive & Mengenangaben
finitimus :: der angrenzende; der Nachbar
proximus :: der nächste; der Verwandte
extremus :: der am weitesten entfernte
ulterior :: der jenseitige; der weiter entfernte
reliquus :: der übrige
omnis :: jeder; ganz
omnes :: alle
totus (Gen.: totius; Dat.: toti) :: ganz; alle; sämtliche; das Ganze; insgesamt
ullus (in verneinten Sätzen) – nullus :: irgendein – kein
nonnulli :: einige; manche
celer, celeris, celere :: schnell
certus, certa, certum :: sicher; gewiss; glaubwürdig (Adjektiv)
certe :: sicherlich (Adverb)
certior fieri; certior factus sum :: informiert / benachrichtigt / in Kenntnis gesetzt werden
Caesarem certiorem facere :: Caesar informieren / benachrichtigen
ob eas causas :: aus diesen Gründen

## 3 Verben: sein, gehen, Krieg, Können
adesse – adesse + Dat. :: dasein – jmdn. helfen
abesse; deesse :: nicht dasein: fehlen
exire – inire :: hinausgehen / auswandern – hineingehen
bellum inire – consilium inire :: Krieg beginnen – Beschluss fassen
bellum inferre – bellum gerere :: Krieg beginnen – Krieg führen
pacem / amicitiam confirmare :: Frieden / (polit.) Freundschaft schließen
velle, volo, volui :: wollen
nolle, nolo, nolui :: nicht wollen
malle, malo, malui :: lieber wollen
posse, possum, potui :: können

## 4 Relativsatz, Vergleich & Satzanschluss
qui, quae, quod :: der, die, das / welcher, welche, welches (Relativpronomina)
quibuscum :: mit denen
quam :: Vergleich: … als …
quam maximus :: möglichst groß
non minus … quam :: Vergleich: ebenso sehr … wie …
quoque :: nachgestellt: auch
quantum + Gen. … tantum + Gen. :: so viel an … wie an …
tantum (allein stehend) :: nur
ne … quidem :: nicht einmal
quod + Ind. :: weil
propterea quod :: deswegen, weil
itaque :: deshalb
praeterea :: außerdem
qua de causa (als relativ. Satzanschluß) :: deswegen; deshalb; aus diesem Grund
qua ex parte :: deshalb
ubi + Indikativ (= cum + Konjunktiv) :: als; sobald
nihilominus :: trotzdem; nichtsdestotrotz
cum (+ Konjunktiv) :: als; weil; obwohl
cum primum (+ Konjunktiv) :: sobald

## 5 Präpositionen & Ortsadverbien
usque ad + Akk. :: bis zu / zur …
per + Akk. :: durch …
per fines suos :: durch ihr Gebiet
per eos :: mit ihrer Hilfe
trans + Akk. :: über / hinüber / jenseits von
apud + Akk. :: bei
inter + Akk. :: zwischen
ibi :: dort
inde :: von dort; daher
eo :: dorthin
unde :: woher
undique :: von allen Seiten
hinc :: von hier
ita :: so; auf diese Weise
ad + Akk. (ad eas res …) :: zu (zu diesen Angelegenheiten; Maßnahmen)
ad (=fere) :: ungefähr; circa; etwa
ante + Akk. :: vor
ante :: vorher
ob + Akk. :: wegen
post + Akk. :: nach
contra + Akk. :: gegen
praeter + Akk. :: außer
praeter quod :: außer dem, das …
a / ab + Abl. :: von
cum + Abl. :: mit
pro + Abl. :: für; im Verhältnis zu
ex + Abl. (ex eo oppido); (e finibus suis) :: aus … heraus (aus dieser Stadt heraus); (aus ihrem Gebiet)

## 6 Konjunktionen & Partikeln
utrum … an :: ob … oder
an :: oder
aut :: oder
aut … aut :: entweder … oder
vel :: oder
vel … vel :: entweder … oder
neque; nec :: und nicht; auch nicht
neque … neque; nec … nec :: weder … noch
et :: und; auch
et … et :: sowohl … als auch
at / atque :: aber; doch
sed :: doch; aber; sondern
tamen :: jedoch; dennoch
nam :: denn
dum (+ Konj.) :: bis dass
ut / uti; ne :: dass; dass nicht (oder Infinitivanschluss)
quin :: dass
si (non) :: falls (nicht); wenn (nicht)
-ne (in abhängigen Fragen) :: ob

## 7 Adverbien
minime :: keineswegs
nondum :: noch nicht
fere; circiter :: ungefähr; circa; etwa
vix :: kaum
longe :: bei weitem
item(que) :: ebenso
item … quam :: ebenso … wie
interea :: inzwischen
interim :: inzwischen; in der Zwischenzeit
eo / illo tempore :: zu dieser / jener Zeit
eodem :: zu demselben Ort
omnino :: überhaupt
nuper :: neulich
umquam :: jemals
numquam :: niemals
nonnumquam :: manchmal
simul :: zugleich
saepe – saepius :: oft – öfters
diu - diutius :: lange – länger

## 8 Verben (Grundformen & Deponentien)
incipere, incipio, coepi, inceptum :: beginnen
intellegere :: verstehen; begreifen
neglegere :: vernachlässigen; nicht beachten
cognoscere :: erkennen; kennenlernen
iungere :: verbinden; vereinigen
dicere, dico, dixi, dictum :: sagen
ducere, duco, duxi, ductum :: führen
adducere :: heranführen; veranlassen
appropinquare :: sich nähern
pugnare :: kämpfen
vincere, vinco, vici, victum :: siegen
relinquere, relinquo, reliqui, relictum :: verlassen; zurücklassen
regere :: beherrschen
studere / studium, -i (n.) :: sich bemühen / das Bemühen
admittere, admitto, admisi, admissum :: zulassen; erlauben
facinus admittere :: eine Tat begehen
scelus committere :: ein Verbrechen begehen
promittere :: versprechen
amittere :: verlieren
dimittere :: aufgeben; entlassen; wegschicken
differe, differo, distuli, dilatum :: sich unterscheiden (von)
referre, refero, rettuli, relatum :: berichten
afferre, affero, attuli, allatum :: melden
auferre, aufero, abstuli, ablatum :: rauben
conferre, confero, contuli, collatum :: vergleichen; zusammentragen
polliceri :: versprechen
vereri :: fürchten; (Götter) verehren
videri :: scheinen; gelten (als)
oriri :: entstehen; sich erheben; aufgehen (Sonne)
loqui :: reden; sprechen
proficisci :: reisen; abreisen; aufbrechen
queri :: klagen; sich beklagen (über)
sequi (+ Akk.) :: folgen
uti (+ Abl.) :: benutzen; gebrauchen

## 9 Caesar-Wendungen
inquit :: er sagt / sagte
his rebus fiebat, ut … :: dadurch geschah es, dass …
id fecit, quod … :: dies tat er, weil …
accidit, ut … :: es geschah, dass …
non esse dubium, quin … :: es stehe außer Zweifel, dass …
haec / quod ubi Caesar animadvertit … :: sobald Caesar dies bemerkte …
his rebus adducti :: durch diese Angelegenheiten / Verhältnisse / Maßnahmen veranlasst …
die constituta :: am festgesetzten Tag
his constitutis rebus :: nach Festlegung dieser Angelegenheiten / Maßnahmen
quam maximis potest itineribus :: in so großen Eilmärschen wie er nur kann
eius voluntate :: mit seiner Zustimmung
se invito :: gegen seinen Willen
ut spatium intercedere posset :: um Zeit zu gewinnen
bono animo in populum Romanum esse :: dem römischen Volk wohlgesinnt sein
pericula subire, subeo, subii :: Gefahren auf sich nehmen
eodem consilio uti :: denselben Plan zu folgen
domo exire :: von zuhause / aus der Heimat fortziehen
eo opere perfecto :: nach Fertigstellung des Bauwerks

## 10 Krieg, Heer & Gallien
Gallia citerior / cisalpina :: das diesseitige Gallien (= Norditalien)
Gallia ulterior / transalpina :: das jenseitige Gallien (= Narbonensis)
populus, -i Romanus, -i (m.) :: das römische Volk
hostis, -is (m.) :: Feind
legatus, -i (m.) :: Legat; Gesandter
legatos mittere :: Gesandte schicken
miles, militis (m.) :: Soldat
navis, navis (f.) :: Schiff
navigare :: segeln
legio, -ionis (f.) :: Legion
legionem conscribere :: eine Legion ausheben (= rekrutieren)
convenire :: zusammenkommen
convocare :: zusammenrufen
bellum gerere :: Krieg führen
administrare :: durchführen; (Befehle) ausführen
copia, -ae (f.) :: Menge; Schar
exercitus, -us (m.) :: Heer
equites (m.Pl.) :: Reiterei (Pluralwort)
castra, -orum (n.) :: Lager (Pluralwort)
e castris proficisci (Dep.) / se in castra recipere :: aus dem Lager aufbrechen / sich ins Lager zurückziehen
iter facere :: marschieren (zivil: reisen)
in fines pervenire / transire :: in ein Gebiet gelangen / übersiedeln
exercitum / legiones (e)ducere :: das Heer / die Legionen (hinaus)führen
in proeliis uti (Dep.) :: im Kampf / in der Schlacht benutzen
proelio interesse :: an der Schlacht teilnehmen
proelium committere :: eine Schlacht liefern
arma capere :: zu den Waffen greifen
consilium capere :: einen Entschluss fassen
libertatis causa :: um der Freiheit willen
potestas vitae necisque :: die Gewalt über Leben und Tod
portus, -us (m.) :: Hafen
locus, -i (m.) :: Ort; Gebiet
tempus,-oris (n.); tempestas, tempestatis (f.) :: Zeit; Zeitpunkt; Wetter; Unwetter; Sturm
eodem tempore :: zur selben Zeit
eo tempestate :: zu dieser Zeit
postero die :: am folgenden Tag
subire tempestatem :: den Sturm über sich ergehen lassen
tempestas ad navigandum idonea :: eine zur Seefahrt günstige Witterung
paratus in armis esse :: (als Soldat) in Bereitschaft stehen
armatus, -a, -um :: bewaffnet
idoneus, -a, -um :: geeignet; passend
proelium, -i (n.) :: Kampf; Schlacht
acies, -iei (f.) :: Schlachtreihe
nuntius, -i (m.) :: Bote; Meldung
litterae, -arum (f. Pl.) :: Brief; Nachricht
rumor, -is (m.) :: Gerücht
obses, obsidis (m./f.) :: Geisel

## 11 Partizipial- & Ablativ-Wendungen
cupiditate / invidia inductus :: von Gier / Neid getrieben
quibus / his rebus adductus :: durch diese Dinge veranlasst
auctoritate permotus :: von seinem Ansehen bewegt
e castris profectus :: nach dem Aufbruch aus dem Lager
hostibus (ex)pulsis :: nach der Vertreibung der Feinde
ira / timore captus :: von Zorn / Angst ergriffen
consilio capto :: auf diesen Beschluss hin / nach Beschlussfassung
consilio cognito :: als der Plan durchschaut / erkannt worden war / nach Bekanntwerden des Planes
timore sublato :: nach Beseitigung der Furcht
copiis coactis / coacta manu :: nachdem die Truppen versammelt worden waren
his verbis dictis / his verbis auditis :: nach diesen Worten
eo facto / eo cognito :: aufgrund dieser Tatsache / danach / nachdem dies geschehen war
bello confecto / proelio confecto :: nach Kriegsende / nach dem Ende der Schlacht
Caesare auctore :: auf Veranlassung Caesars
Caesare imperante :: unter dem Kommando Caesars
"""


def load_data():
    items, cat, seen = [], "Allgemein", set()
    for line in RAW_DATA.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            cat = line[3:].strip()
            continue
        if " :: " not in line:
            continue
        la, de = [p.strip() for p in line.split(" :: ", 1)]
        key, n = la, 2
        while key in seen:
            key = f"{la} #{n}"
            n += 1
        seen.add(key)
        items.append({"id": key, "latin": la, "german": de, "cat": cat})
    return items


DATA = load_data()
CATEGORIES = list(dict.fromkeys(i["cat"] for i in DATA))
DE_TO_LA = {}
for _it in DATA:
    DE_TO_LA.setdefault(_it["german"], []).append(_it["latin"])

# ----------------------------------------------------------------------------
# ANTWORT-AUSWERTUNG
# ----------------------------------------------------------------------------


def norm(s):
    s = s.lower().replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    s = s.replace("…", " ")
    s = re.sub(r"[\u2010-\u2015\-]", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def compact(s):
    return norm(s).replace(" ", "")


def answer_variants(text):
    """Zerlegt eine Bedeutung in akzeptierte Teilantworten.
    full    = vollständig gültige Antworten (getrennt durch ; / | oder :)
    partial = nur ein Teil einer Aufzählung mit ' – ' (zählt als 'teilweise')"""
    raw = text.strip()
    full = {raw}
    for p in re.split(r"\s*[;/|]\s*", raw):
        if p.strip():
            full.add(p.strip())
    if ":" in raw:
        for p in raw.split(":"):
            if p.strip():
                full.add(p.strip())
    for v in list(full):
        v2 = re.sub(r"\([^)]*\)", "", v)
        v2 = re.sub(r"\s+", " ", v2).strip()
        if v2:
            full.add(v2)
    partial = set()
    for v in list(full):
        parts = re.split(r"\s+[–—-]\s+", v)
        if len(parts) > 1:
            for p in parts:
                if p.strip():
                    partial.add(p.strip())
    return full, partial - full


def evaluate(user, expected, tol=0.88):
    """Rückgabe: 'empty' | 'correct' | 'almost' | 'partial' | 'wrong'"""
    u = compact(user)
    if not u:
        return "empty"
    full, partial = answer_variants(expected)
    best = 0.0
    for c in full:
        cc = compact(c)
        if not cc:
            continue
        if u == cc:
            return "correct"
        best = max(best, SequenceMatcher(None, u, cc).ratio())
    for c in partial:
        if u == compact(c):
            return "partial"
    thr = tol if len(u) > 5 else max(tol, 0.92)
    if best >= 0.96:
        return "correct"
    if best >= thr:
        return "almost"
    return "wrong"


def hint_text(text, level):
    first = re.split(r"\s*[;/|]\s*", text)[0]
    first = re.sub(r"\([^)]*\)", "", first)
    out = []
    for tok in first.split():
        if not any(ch.isalpha() for ch in tok):
            out.append(tok)
            continue
        shown, res = 0, ""
        for ch in tok:
            if ch.isalpha():
                res += ch if shown < level else "_"
                shown += 1
            else:
                res += ch
        out.append(res)
    return " ".join(out)


# ----------------------------------------------------------------------------
# DESIGN & EINSTELLUNGEN
# ----------------------------------------------------------------------------
THEMES = {
    "Dunkel": dict(bg="#12141a", panel="#1b1e27", card="#232735", fg="#e9ebf2", muted="#8f95a9",
                   accent="#6c8cff", accent_h="#8aa2ff", accent_fg="#ffffff", good="#34c88a",
                   bad="#ff6b6b", warn="#ffb454", border="#343a52", entry="#181b24"),
    "Hell": dict(bg="#eef1f8", panel="#ffffff", card="#ffffff", fg="#1c2234", muted="#6a728f",
                 accent="#3b5bdb", accent_h="#2f4bbd", accent_fg="#ffffff", good="#1b9a62",
                 bad="#d64545", warn="#cf8200", border="#d5dbea", entry="#f5f7fc"),
}

BOX_DAYS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 21}
MODES = ["Eintippen", "Multiple Choice", "Karteikarten"]
DIRECTIONS = ["Latein → Deutsch", "Deutsch → Latein", "Gemischt"]
STRATEGIES = ["Intelligent (fällige zuerst)", "Zufällig", "Reihenfolge der PDF",
              "Nur neue Vokabeln", "Nur schwierige", "Nur Favoriten"]
COUNTS = ["10", "20", "30", "50", "Alle"]
STATUS_FILTER = ["Alle", "Neu", "Schwierig", "Favoriten", "Gelernt (Box 4–5)", "Fällig"]

DEFAULT_SETTINGS = {
    "theme": "Dunkel", "tolerance": 0.88, "auto_next": True, "auto_delay": 1100,
    "timer": False, "timer_seconds": 20, "auto_hint": False, "q_size": 30,
    "mode": "Eintippen", "direction": "Latein → Deutsch", "strategy": STRATEGIES[0],
    "count": "20", "cats": None,
}


def load_store():
    try:
        return json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ----------------------------------------------------------------------------
# APP
# ----------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x860")
        self.minsize(1020, 740)

        self.store = load_store()
        self.settings = dict(DEFAULT_SETTINGS)
        self.settings.update(self.store.get("settings", {}))
        if self.settings["theme"] not in THEMES:
            self.settings["theme"] = "Dunkel"
        self.cards = self.store.get("cards", {})
        self.favorites = set(self.store.get("favorites", []))
        self.daily = self.store.get("daily", {})
        self.best_streak = self.store.get("best_streak", 0)

        self.queue, self.current, self.direction = [], None, "la"
        self.sess, self.last_info = {}, None
        self.session_active = self.awaiting_next = self.revealed = False
        self.hint_level = 0
        self.after_job = self.timer_job = None
        self.mc_options, self.mc_buttons = [], []
        self.cat_vars, self.cat_checks = {}, {}

        fams = set(tkfont.families())
        self.fam = next((f for f in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu",
                                     "DejaVu Sans", "Arial") if f in fams), "TkDefaultFont")
        self.style = ttk.Style(self)
        self.pal = THEMES[self.settings["theme"]]

        self.build_ui()
        self.apply_theme()
        self.refresh_all()
        self.bind("<Key>", self.on_key)
        self.bind("<Control-h>", lambda e: self.hint())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------ speichern
    def save(self):
        self.store.update(cards=self.cards, favorites=sorted(self.favorites), daily=self.daily,
                          best_streak=self.best_streak, settings=self.settings)
        try:
            tmp = SAVE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.store, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(SAVE_FILE)
        except OSError:
            pass

    def on_close(self):
        self.save_setup()
        self.save()
        self.destroy()

    # --------------------------------------------------------------- Theme
    def apply_theme(self):
        p = self.pal = THEMES[self.settings["theme"]]
        s, f = self.style, self.fam
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        self.configure(bg=p["bg"])
        self.option_add("*TCombobox*Listbox.background", p["entry"])
        self.option_add("*TCombobox*Listbox.foreground", p["fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", p["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", p["accent_fg"])
        s.configure(".", background=p["bg"], foreground=p["fg"], fieldbackground=p["entry"],
                    bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"],
                    troughcolor=p["panel"], font=(f, 11), focuscolor=p["bg"])
        for name, bg in (("TFrame", p["bg"]), ("Panel.TFrame", p["panel"]), ("Card.TFrame", p["card"])):
            s.configure(name, background=bg)
        s.configure("TLabel", background=p["bg"], foreground=p["fg"])
        s.configure("Muted.TLabel", foreground=p["muted"])
        s.configure("Head.TLabel", font=(f, 15, "bold"))
        s.configure("Panel.TLabel", background=p["panel"])
        s.configure("Title.Panel.TLabel", font=(f, 20, "bold"))
        s.configure("Muted.Panel.TLabel", foreground=p["muted"])
        s.configure("Card.TLabel", background=p["card"])
        s.configure("Muted.Card.TLabel", foreground=p["muted"])
        s.configure("Head.Card.TLabel", font=(f, 15, "bold"))
        s.configure("Question.Card.TLabel", font=(f, int(self.settings["q_size"]), "bold"))
        s.configure("Hint.Card.TLabel", foreground=p["warn"], font=("Consolas" if f == "Segoe UI" else f, 15))
        s.configure("Good.Card.TLabel", foreground=p["good"], font=(f, 16, "bold"))
        s.configure("Bad.Card.TLabel", foreground=p["bad"], font=(f, 16, "bold"))
        s.configure("Warn.Card.TLabel", foreground=p["warn"], font=(f, 16, "bold"))
        s.configure("Accent.Card.TLabel", foreground=p["accent"], font=(f, 20, "bold"))
        s.configure("TButton", background=p["panel"], foreground=p["fg"], padding=(14, 9),
                    borderwidth=1, relief="flat")
        s.map("TButton", background=[("active", p["border"])])
        for name, col, hov in (("Accent", p["accent"], p["accent_h"]), ("Good", p["good"], p["good"]),
                               ("Bad", p["bad"], p["bad"])):
            s.configure(f"{name}.TButton", background=col, foreground="#ffffff",
                        font=(f, 11, "bold"), padding=(18, 10))
            s.map(f"{name}.TButton", background=[("active", hov)])
        for name in ("TCheckbutton", "TRadiobutton"):
            s.configure(name, background=p["bg"], foreground=p["fg"])
            s.configure(f"Card.{name}", background=p["card"], foreground=p["fg"])
            s.map(f"Card.{name}", background=[("active", p["card"])])
            s.map(name, background=[("active", p["bg"])])
        s.configure("TEntry", fieldbackground=p["entry"], foreground=p["fg"], insertcolor=p["fg"], padding=8)
        s.configure("TSpinbox", fieldbackground=p["entry"], foreground=p["fg"], arrowcolor=p["fg"])
        s.configure("TCombobox", fieldbackground=p["entry"], foreground=p["fg"], arrowcolor=p["fg"],
                    background=p["panel"], padding=6)
        s.map("TCombobox", fieldbackground=[("readonly", p["entry"])], foreground=[("readonly", p["fg"])],
              selectbackground=[("readonly", p["entry"])], selectforeground=[("readonly", p["fg"])])
        s.configure("TNotebook", background=p["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=p["panel"], foreground=p["muted"], padding=(22, 10), borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected", p["card"])], foreground=[("selected", p["fg"])])
        s.configure("Horizontal.TProgressbar", background=p["accent"], troughcolor=p["panel"],
                    borderwidth=0, thickness=10)
        s.configure("Good.Horizontal.TProgressbar", background=p["good"], troughcolor=p["entry"],
                    borderwidth=0, thickness=10)
        s.configure("Card.Horizontal.TScale", background=p["card"], troughcolor=p["entry"])
        s.configure("Treeview", background=p["entry"], fieldbackground=p["entry"], foreground=p["fg"],
                    rowheight=26, borderwidth=0)
        s.map("Treeview", background=[("selected", p["accent"])], foreground=[("selected", p["accent_fg"])])
        s.configure("Treeview.Heading", background=p["panel"], foreground=p["fg"], relief="flat",
                    font=(f, 10, "bold"), padding=6)
        s.map("Treeview.Heading", background=[("active", p["border"])])
        s.configure("Vertical.TScrollbar", background=p["panel"], troughcolor=p["bg"], arrowcolor=p["fg"])
        if hasattr(self, "tree"):
            for tag, col in (("mastered", p["good"]), ("hard", p["bad"]), ("new", p["muted"])):
                self.tree.tag_configure(tag, foreground=col)
        if hasattr(self, "theme_btn"):
            self.theme_btn.configure(text="☀ Hell" if self.settings["theme"] == "Dunkel" else "☾ Dunkel")

    def toggle_theme(self):
        self.settings["theme"] = "Hell" if self.settings["theme"] == "Dunkel" else "Dunkel"
        self.theme_var.set(self.settings["theme"])
        self.apply_theme()
        self.refresh_stats()
        self.save()

    # ------------------------------------------------------------------ UI
    def build_ui(self):
        head = ttk.Frame(self, style="Panel.TFrame", padding=(24, 14))
        head.pack(fill="x")
        ttk.Label(head, text="📜 Caesar Vokabeltrainer", style="Title.Panel.TLabel").pack(side="left")
        self.theme_btn = ttk.Button(head, command=self.toggle_theme)
        self.theme_btn.pack(side="right")
        self.head_info = tk.StringVar()
        ttk.Label(head, textvariable=self.head_info, style="Muted.Panel.TLabel").pack(side="right", padx=18)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=16, pady=(12, 16))
        self.tab_learn = ttk.Frame(self.nb, padding=16)
        self.tab_list = ttk.Frame(self.nb, padding=16)
        self.tab_stats = ttk.Frame(self.nb, padding=16)
        self.tab_set = ttk.Frame(self.nb, padding=16)
        for tab, name in ((self.tab_learn, "  Lernen  "), (self.tab_list, "  Vokabelliste  "),
                          (self.tab_stats, "  Statistik  "), (self.tab_set, "  Einstellungen  ")):
            self.nb.add(tab, text=name)
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

        self.build_setup()
        self.build_card()
        self.build_summary()
        self.build_list()
        self.build_stats()
        self.build_settings()
        self.show_frame("setup")

    def show_frame(self, which):
        for name in ("setup", "card", "summary"):
            getattr(self, f"{name}_frame").pack_forget()
        getattr(self, f"{which}_frame").pack(fill="both", expand=True)

    # ------------------------------------------------------ Setup (Auswahl)
    def build_setup(self):
        self.setup_frame = ttk.Frame(self.tab_learn)
        self.setup_info = tk.StringVar()
        ttk.Label(self.setup_frame, textvariable=self.setup_info, style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        body = ttk.Frame(self.setup_frame)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, style="Card.TFrame", padding=22)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        ttk.Label(left, text="Kapitel auswählen", style="Head.Card.TLabel").pack(anchor="w", pady=(0, 10))
        saved = self.settings.get("cats")
        for cat in CATEGORIES:
            var = tk.BooleanVar(value=True if saved is None else cat in saved)
            cb = ttk.Checkbutton(left, variable=var, style="Card.TCheckbutton", text=cat)
            cb.pack(anchor="w", pady=3)
            self.cat_vars[cat], self.cat_checks[cat] = var, cb
        row = ttk.Frame(left, style="Card.TFrame")
        row.pack(anchor="w", pady=(14, 0))
        ttk.Button(row, text="Alle", command=lambda: self.set_all_cats(True)).pack(side="left", padx=(0, 6))
        ttk.Button(row, text="Keine", command=lambda: self.set_all_cats(False)).pack(side="left", padx=6)
        ttk.Button(row, text="Nur Kapitel mit fälligen", command=self.cats_with_due).pack(side="left", padx=6)

        right = ttk.Frame(body, style="Card.TFrame", padding=22)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Lernsitzung", style="Head.Card.TLabel").pack(anchor="w", pady=(0, 10))
        self.s_mode = self.combo(right, "Modus", MODES, self.settings["mode"])
        self.s_dir = self.combo(right, "Richtung", DIRECTIONS, self.settings["direction"])
        self.s_strategy = self.combo(right, "Auswahl", STRATEGIES, self.settings["strategy"])
        self.s_count = self.combo(right, "Anzahl Vokabeln", COUNTS, self.settings["count"])
        ttk.Button(right, text="▶  Lernen starten", style="Accent.TButton",
                   command=self.start_session).pack(fill="x", pady=(22, 8))
        ttk.Button(right, text="⏰  Nur fällige Vokabeln wiederholen",
                   command=self.quick_due).pack(fill="x")
        ttk.Label(right, style="Muted.Card.TLabel", wraplength=380, justify="left",
                  text="Tipp: Richtig beantwortete Vokabeln wandern im Karteikasten eine Box höher und "
                       "kommen später wieder (1 → 3 → 7 → 21 Tage). Falsche starten wieder in Box 1.").pack(
            anchor="w", pady=(22, 0))

    def combo(self, parent, label, values, value):
        ttk.Label(parent, text=label, style="Muted.Card.TLabel").pack(anchor="w", pady=(8, 2))
        cb = ttk.Combobox(parent, values=values, state="readonly", width=34)
        cb.set(value if value in values else values[0])
        cb.pack(anchor="w")
        return cb

    def set_all_cats(self, val):
        for v in self.cat_vars.values():
            v.set(val)

    def cats_with_due(self):
        st = self.cat_stats()
        for cat, v in self.cat_vars.items():
            v.set(st[cat]["due"] > 0)

    def save_setup(self):
        if not hasattr(self, "s_mode"):
            return
        self.settings.update(mode=self.s_mode.get(), direction=self.s_dir.get(),
                             strategy=self.s_strategy.get(), count=self.s_count.get(),
                             cats=[c for c, v in self.cat_vars.items() if v.get()])

    # ---------------------------------------------------------- Lernkarte
    def build_card(self):
        self.card_frame = ttk.Frame(self.tab_learn)
        top = ttk.Frame(self.card_frame)
        top.pack(fill="x")
        self.box_var, self.prog_var, self.cat_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(top, textvariable=self.box_var).pack(side="left")
        ttk.Label(top, textvariable=self.cat_var, style="Muted.TLabel").pack(side="left", padx=18)
        ttk.Label(top, textvariable=self.prog_var, style="Muted.TLabel").pack(side="right")
        self.pbar = ttk.Progressbar(self.card_frame, maximum=1, value=0)
        self.pbar.pack(fill="x", pady=(8, 12))

        self.card = ttk.Frame(self.card_frame, style="Card.TFrame", padding=(34, 26))
        self.card.pack(fill="both", expand=True)
        self.dir_var, self.q_var = tk.StringVar(), tk.StringVar()
        self.hint_var, self.fb_var, self.timer_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(self.card, textvariable=self.dir_var, style="Muted.Card.TLabel").pack()
        self.q_label = ttk.Label(self.card, textvariable=self.q_var, style="Question.Card.TLabel",
                                 anchor="center", justify="center", wraplength=900)
        self.q_label.pack(fill="x", pady=(16, 8))
        self.hint_label = ttk.Label(self.card, textvariable=self.hint_var, style="Hint.Card.TLabel",
                                    anchor="center", justify="center")
        self.hint_label.pack(pady=4)

        self.input_area = ttk.Frame(self.card, style="Card.TFrame")
        self.input_area.pack(fill="x", pady=10)
        self.answer_var = tk.StringVar()
        self.entry = ttk.Entry(self.input_area, textvariable=self.answer_var, font=(self.fam, 18), justify="center")
        self.mc_frame = ttk.Frame(self.input_area, style="Card.TFrame")
        self.flash_lbl = ttk.Label(self.input_area, style="Muted.Card.TLabel", justify="center",
                                   text="Überlege dir die Antwort – dann Leertaste oder „Umdrehen“.")

        self.fb_label = ttk.Label(self.card, textvariable=self.fb_var, style="Card.TLabel",
                                  anchor="center", justify="center", wraplength=900)
        self.fb_label.pack(fill="x", pady=10)
        ttk.Label(self.card, textvariable=self.timer_var, style="Muted.Card.TLabel").pack()
        self.card.bind("<Configure>", lambda e: (self.q_label.configure(wraplength=max(300, e.width - 120)),
                                                 self.fb_label.configure(wraplength=max(300, e.width - 120))))

        self.btn_row = ttk.Frame(self.card_frame)
        self.btn_row.pack(pady=(14, 0))
        self.btns = {
            "hint": ttk.Button(self.btn_row, text="💡 Hinweis (Strg+H)", command=self.hint),
            "check": ttk.Button(self.btn_row, text="Prüfen  ↵", style="Accent.TButton", command=self.check_answer),
            "reveal": ttk.Button(self.btn_row, text="Weiß ich nicht", command=self.give_up),
            "override": ttk.Button(self.btn_row, text="✔ Als richtig werten", command=self.override),
            "next": ttk.Button(self.btn_row, text="Weiter  ↵", style="Accent.TButton", command=self.next_card),
            "flip": ttk.Button(self.btn_row, text="Umdrehen  ␣", style="Accent.TButton", command=self.flip),
            "know": ttk.Button(self.btn_row, text="✓ Gewusst (1)", style="Good.TButton",
                               command=lambda: self.flash_answer(True)),
            "dont": ttk.Button(self.btn_row, text="✗ Nicht gewusst (2)", style="Bad.TButton",
                               command=lambda: self.flash_answer(False)),
            "fav": ttk.Button(self.btn_row, text="☆ Favorit", command=self.toggle_fav),
            "stop": ttk.Button(self.btn_row, text="Beenden", command=self.finish_session),
        }

    def show_buttons(self, *names):
        for b in self.btns.values():
            b.pack_forget()
        for n in names:
            self.btns[n].pack(side="left", padx=5)

    # --------------------------------------------------------- Zusammenfassung
    def build_summary(self):
        self.summary_frame = ttk.Frame(self.tab_learn)
        c = ttk.Frame(self.summary_frame, style="Card.TFrame", padding=28)
        c.pack(fill="both", expand=True)
        self.sum_title = tk.StringVar()
        self.sum_text = tk.StringVar()
        ttk.Label(c, textvariable=self.sum_title, style="Head.Card.TLabel").pack(anchor="w")
        ttk.Label(c, textvariable=self.sum_text, style="Card.TLabel", justify="left").pack(anchor="w", pady=12)
        ttk.Label(c, text="Diese Vokabeln solltest du nochmal ansehen:", style="Muted.Card.TLabel").pack(anchor="w")
        wrap = ttk.Frame(c, style="Card.TFrame")
        wrap.pack(fill="both", expand=True, pady=8)
        self.sum_tree = ttk.Treeview(wrap, columns=("la", "de"), show="headings", height=9)
        self.sum_tree.heading("la", text="Latein")
        self.sum_tree.heading("de", text="Deutsch")
        self.sum_tree.column("la", width=380)
        self.sum_tree.column("de", width=520)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.sum_tree.yview)
        self.sum_tree.configure(yscrollcommand=sb.set)
        self.sum_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        row = ttk.Frame(c, style="Card.TFrame")
        row.pack(pady=(10, 0))
        self.btn_repeat = ttk.Button(row, text="🔁 Fehler wiederholen", style="Accent.TButton",
                                     command=self.repeat_wrong)
        self.btn_repeat.pack(side="left", padx=6)
        ttk.Button(row, text="Neue Sitzung", command=self.back_to_setup).pack(side="left", padx=6)

    # ----------------------------------------------------------- Vokabelliste
    def build_list(self):
        bar = ttk.Frame(self.tab_list)
        bar.pack(fill="x", pady=(0, 10))
        self.search_var = tk.StringVar()
        ttk.Label(bar, text="Suche:").pack(side="left")
        e = ttk.Entry(bar, textvariable=self.search_var, width=26)
        e.pack(side="left", padx=(6, 14))
        self.search_var.trace_add("write", lambda *a: self.refresh_list())
        self.list_cat = ttk.Combobox(bar, values=["Alle Kapitel"] + CATEGORIES, state="readonly", width=34)
        self.list_cat.set("Alle Kapitel")
        self.list_cat.pack(side="left", padx=6)
        self.list_cat.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())
        self.list_status = ttk.Combobox(bar, values=STATUS_FILTER, state="readonly", width=20)
        self.list_status.set("Alle")
        self.list_status.pack(side="left", padx=6)
        self.list_status.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        wrap = ttk.Frame(self.tab_list)
        wrap.pack(fill="both", expand=True)
        cols = ("fav", "la", "de", "cat", "box", "score")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="extended")
        for col, text, w in (("fav", "★", 40), ("la", "Latein", 310), ("de", "Deutsch", 380),
                             ("cat", "Kapitel", 210), ("box", "Box", 70), ("score", "✓/✗", 70)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="w" if col in ("la", "de", "cat") else "center")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.bind("<Double-1>", lambda e: self.list_action("fav"))

        row = ttk.Frame(self.tab_list)
        row.pack(fill="x", pady=(10, 0))
        ttk.Button(row, text="★ Favorit umschalten", command=lambda: self.list_action("fav")).pack(side="left", padx=(0, 6))
        ttk.Button(row, text="Als gelernt markieren (Box 5)", command=lambda: self.list_action("learned")).pack(side="left", padx=6)
        ttk.Button(row, text="Zurücksetzen (neu)", command=lambda: self.list_action("reset")).pack(side="left", padx=6)
        self.list_count = tk.StringVar()
        ttk.Label(row, textvariable=self.list_count, style="Muted.TLabel").pack(side="right")

    def status_of(self, it, now=None):
        now = now or time.time()
        c = self.cards.get(it["id"])
        return c, (c is None), (c is not None and c["due"] <= now)

    def refresh_list(self):
        if not hasattr(self, "tree"):
            return
        q = norm(self.search_var.get())
        cat = self.list_cat.get()
        stat = self.list_status.get()
        now = time.time()
        self.tree.delete(*self.tree.get_children())
        n = 0
        for idx, it in enumerate(DATA):
            c, is_new, due = self.status_of(it, now)
            if cat != "Alle Kapitel" and it["cat"] != cat:
                continue
            if q and q not in norm(it["latin"]) and q not in norm(it["german"]):
                continue
            hard = bool(c and c["bad"] > c["ok"])
            if stat == "Neu" and not is_new:
                continue
            if stat == "Schwierig" and not hard:
                continue
            if stat == "Favoriten" and it["id"] not in self.favorites:
                continue
            if stat.startswith("Gelernt") and not (c and c["box"] >= 4):
                continue
            if stat == "Fällig" and not due:
                continue
            tag = "new" if is_new else "mastered" if c["box"] >= 4 else "hard" if hard else ""
            self.tree.insert("", "end", iid=str(idx), tags=(tag,), values=(
                "★" if it["id"] in self.favorites else "", it["latin"], it["german"], it["cat"],
                "–" if is_new else c["box"], "" if is_new else f'{c["ok"]}/{c["bad"]}'))
            n += 1
        self.list_count.set(f"{n} von {len(DATA)} Vokabeln")

    def list_action(self, what):
        for iid in self.tree.selection():
            it = DATA[int(iid)]
            if what == "fav":
                self.favorites ^= {it["id"]}
            elif what == "learned":
                now = time.time()
                c = self.cards.setdefault(it["id"], {"box": 5, "due": now, "ok": 0, "bad": 0, "streak": 0, "last": now})
                c["box"], c["due"] = 5, now + BOX_DAYS[5] * 86400
            elif what == "reset":
                self.cards.pop(it["id"], None)
        self.save()
        self.refresh_list()
        self.refresh_stats()

    # -------------------------------------------------------------- Statistik
    def build_stats(self):
        left = ttk.Frame(self.tab_stats, style="Card.TFrame", padding=20)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right = ttk.Frame(self.tab_stats, style="Card.TFrame", padding=20)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Überblick", style="Head.Card.TLabel").pack(anchor="w")
        self.stats_text = tk.StringVar()
        ttk.Label(left, textvariable=self.stats_text, style="Card.TLabel", justify="left").pack(anchor="w", pady=(8, 12))
        ttk.Label(left, text="Karteikasten", style="Head.Card.TLabel").pack(anchor="w", pady=(4, 6))
        self.box_bars = {}
        for b in range(0, 6):
            r = ttk.Frame(left, style="Card.TFrame")
            r.pack(fill="x", pady=2)
            ttk.Label(r, text="Neu" if b == 0 else f"Box {b}", style="Card.TLabel", width=7).pack(side="left")
            pb = ttk.Progressbar(r, maximum=max(1, len(DATA)), style="Horizontal.TProgressbar")
            pb.pack(side="left", fill="x", expand=True, padx=8)
            lab = ttk.Label(r, text="0", style="Muted.Card.TLabel", width=5)
            lab.pack(side="left")
            self.box_bars[b] = (pb, lab)
        ttk.Label(left, text="Letzte 7 Tage  (grün = richtig, rot = falsch)", style="Head.Card.TLabel").pack(anchor="w", pady=(16, 4))
        self.chart = tk.Canvas(left, width=520, height=150, highlightthickness=0, bd=0)
        self.chart.pack(anchor="w")

        ttk.Label(right, text="Fortschritt je Kapitel (Box 4–5 = gelernt)", style="Head.Card.TLabel").pack(anchor="w", pady=(0, 6))
        self.cat_bars = {}
        for cat in CATEGORIES:
            r = ttk.Frame(right, style="Card.TFrame")
            r.pack(fill="x", pady=2)
            ttk.Label(r, text=cat, style="Card.TLabel", width=36).pack(side="left")
            pb = ttk.Progressbar(r, maximum=100, style="Good.Horizontal.TProgressbar")
            pb.pack(side="left", fill="x", expand=True, padx=8)
            lab = ttk.Label(r, text="", style="Muted.Card.TLabel", width=8)
            lab.pack(side="left")
            self.cat_bars[cat] = (pb, lab)
        ttk.Label(right, text="Die schwierigsten Vokabeln", style="Head.Card.TLabel").pack(anchor="w", pady=(16, 6))
        self.hard_tree = ttk.Treeview(right, columns=("la", "de", "n"), show="headings", height=6)
        for col, text, w in (("la", "Latein", 210), ("de", "Deutsch", 250), ("n", "✗", 50)):
            self.hard_tree.heading(col, text=text)
            self.hard_tree.column(col, width=w)
        self.hard_tree.pack(fill="x")

    def cat_stats(self):
        now = time.time()
        res = {c: {"n": 0, "new": 0, "due": 0, "mastered": 0} for c in CATEGORIES}
        for it in DATA:
            r = res[it["cat"]]
            r["n"] += 1
            c = self.cards.get(it["id"])
            if c is None:
                r["new"] += 1
            else:
                r["due"] += c["due"] <= now
                r["mastered"] += c["box"] >= 4
        return res

    def day_streak(self):
        d, n = date.today(), 0
        if self.daily.get(d.isoformat(), {}).get("asked", 0) == 0:
            d -= timedelta(days=1)
        while self.daily.get(d.isoformat(), {}).get("asked", 0) > 0:
            n += 1
            d -= timedelta(days=1)
        return n

    def refresh_stats(self):
        if not hasattr(self, "chart"):
            return
        now = time.time()
        ok = sum(c["ok"] for c in self.cards.values())
        bad = sum(c["bad"] for c in self.cards.values())
        mastered = sum(c["box"] >= 4 for c in self.cards.values())
        due = sum(c["due"] <= now for c in self.cards.values())
        seen = len(self.cards)
        acc = (ok / (ok + bad) * 100) if ok + bad else 0
        self.stats_text.set(
            f"Vokabeln gesamt: {len(DATA)}      Schon gesehen: {seen}      Gelernt (Box 4–5): {mastered}\n"
            f"Jetzt fällig: {due}      Favoriten: {len(self.favorites)}\n"
            f"Antworten gesamt: {ok + bad}      Trefferquote: {acc:.0f} %\n"
            f"Lerntage in Folge: {self.day_streak()}      Beste Serie richtig: {self.best_streak}")
        counts = {b: 0 for b in range(6)}
        counts[0] = len(DATA) - seen
        for c in self.cards.values():
            counts[c["box"]] += 1
        for b, (pb, lab) in self.box_bars.items():
            pb.configure(value=counts[b])
            lab.configure(text=str(counts[b]))
        for cat, r in self.cat_stats().items():
            pb, lab = self.cat_bars[cat]
            pb.configure(value=r["mastered"] / r["n"] * 100)
            lab.configure(text=f'{r["mastered"]}/{r["n"]}')
        self.hard_tree.delete(*self.hard_tree.get_children())
        hard = sorted((it for it in DATA if it["id"] in self.cards and self.cards[it["id"]]["bad"] > 0),
                      key=lambda it: -self.cards[it["id"]]["bad"])[:6]
        for it in hard:
            self.hard_tree.insert("", "end", values=(it["latin"], it["german"], self.cards[it["id"]]["bad"]))
        self.draw_chart()

    def draw_chart(self):
        cv, p = self.chart, self.pal
        cv.delete("all")
        cv.configure(bg=p["card"])
        days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
        vals = [self.daily.get(d.isoformat(), {"asked": 0, "ok": 0}) for d in days]
        mx = max([v["asked"] for v in vals] + [1])
        bw, base = 520 / 7, 112
        for i, (d, v) in enumerate(zip(days, vals)):
            x0, x1 = i * bw + 16, (i + 1) * bw - 16
            hh, okh = v["asked"] / mx * 85, v["ok"] / mx * 85
            if v["asked"]:
                cv.create_rectangle(x0, base - hh, x1, base, fill=p["bad"], outline="")
                if v["ok"]:
                    cv.create_rectangle(x0, base - okh, x1, base, fill=p["good"], outline="")
                cv.create_text((x0 + x1) / 2, base - hh - 9, text=str(v["asked"]), fill=p["fg"], font=(self.fam, 9))
            cv.create_text((x0 + x1) / 2, base + 16, text=d.strftime("%d.%m."), fill=p["muted"], font=(self.fam, 9))

    # ----------------------------------------------------------- Einstellungen
    def build_settings(self):
        c = ttk.Frame(self.tab_set, style="Card.TFrame", padding=26)
        c.pack(fill="both", expand=True)
        L = ttk.Frame(c, style="Card.TFrame")
        L.pack(side="left", fill="both", expand=True, padx=(0, 30))
        R = ttk.Frame(c, style="Card.TFrame")
        R.pack(side="left", fill="both", expand=True)
        s = self.settings

        ttk.Label(L, text="Darstellung", style="Head.Card.TLabel").pack(anchor="w", pady=(0, 8))
        self.theme_var = tk.StringVar(value=s["theme"])
        for th in THEMES:
            ttk.Radiobutton(L, text=th, value=th, variable=self.theme_var, style="Card.TRadiobutton",
                            command=self.on_theme).pack(anchor="w", pady=2)
        ttk.Label(L, text="Schriftgröße der Frage", style="Muted.Card.TLabel").pack(anchor="w", pady=(14, 2))
        self.qsize_var = tk.IntVar(value=s["q_size"])
        ttk.Spinbox(L, from_=18, to=50, textvariable=self.qsize_var, width=6,
                    command=self.on_setting).pack(anchor="w")
        ttk.Label(L, text="Tippfehler-Toleranz (höher = strenger)", style="Muted.Card.TLabel").pack(anchor="w", pady=(18, 2))
        self.tol_var = tk.DoubleVar(value=s["tolerance"])
        ttk.Scale(L, from_=0.80, to=0.98, variable=self.tol_var, length=300, style="Card.Horizontal.TScale",
                  command=lambda v: self.on_setting()).pack(anchor="w")
        self.tol_lab = ttk.Label(L, text="", style="Muted.Card.TLabel")
        self.tol_lab.pack(anchor="w")

        ttk.Label(R, text="Lernhilfen", style="Head.Card.TLabel").pack(anchor="w", pady=(0, 8))
        self.auto_hint_var = tk.BooleanVar(value=s["auto_hint"])
        self.auto_next_var = tk.BooleanVar(value=s["auto_next"])
        self.timer_var_s = tk.BooleanVar(value=s["timer"])
        for text, var in (("Anfangsbuchstaben automatisch anzeigen", self.auto_hint_var),
                          ("Nach richtiger Antwort automatisch weiter", self.auto_next_var),
                          ("Zeitlimit pro Vokabel", self.timer_var_s)):
            ttk.Checkbutton(R, text=text, variable=var, style="Card.TCheckbutton",
                            command=self.on_setting).pack(anchor="w", pady=3)
        r1 = ttk.Frame(R, style="Card.TFrame")
        r1.pack(anchor="w", pady=(8, 0))
        ttk.Label(r1, text="Zeitlimit (Sekunden):", style="Card.TLabel").pack(side="left")
        self.tsec_var = tk.IntVar(value=s["timer_seconds"])
        ttk.Spinbox(r1, from_=5, to=120, textvariable=self.tsec_var, width=6, command=self.on_setting).pack(side="left", padx=8)
        r2 = ttk.Frame(R, style="Card.TFrame")
        r2.pack(anchor="w", pady=(8, 0))
        ttk.Label(r2, text="Pause nach richtiger Antwort (ms):", style="Card.TLabel").pack(side="left")
        self.delay_var = tk.IntVar(value=s["auto_delay"])
        ttk.Spinbox(r2, from_=300, to=5000, increment=100, textvariable=self.delay_var, width=7,
                    command=self.on_setting).pack(side="left", padx=8)

        ttk.Label(R, text="Daten", style="Head.Card.TLabel").pack(anchor="w", pady=(26, 8))
        ttk.Button(R, text="Schwierige Vokabeln als Textdatei exportieren", command=self.export_hard).pack(anchor="w", pady=3)
        ttk.Button(R, text="Gesamten Fortschritt zurücksetzen", style="Bad.TButton", command=self.reset_all).pack(anchor="w", pady=10)
        self.on_setting()

    def on_theme(self):
        self.settings["theme"] = self.theme_var.get()
        self.apply_theme()
        self.refresh_stats()
        self.save()

    def on_setting(self):
        s = self.settings
        try:
            s["q_size"] = int(self.qsize_var.get())
            s["timer_seconds"] = int(self.tsec_var.get())
            s["auto_delay"] = int(self.delay_var.get())
        except (tk.TclError, ValueError):
            pass
        s["tolerance"] = float(self.tol_var.get())
        s["auto_hint"] = self.auto_hint_var.get()
        s["auto_next"] = self.auto_next_var.get()
        s["timer"] = self.timer_var_s.get()
        self.tol_lab.configure(text=f"{s['tolerance']:.0%} Ähnlichkeit")
        self.style.configure("Question.Card.TLabel", font=(self.fam, s["q_size"], "bold"))
        self.save()

    def export_hard(self):
        hard = [it for it in DATA if it["id"] in self.cards and self.cards[it["id"]]["bad"] > self.cards[it["id"]]["ok"]]
        if not hard:
            messagebox.showinfo("Export", "Es gibt noch keine schwierigen Vokabeln.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="schwierige_vokabeln.txt")
        if path:
            Path(path).write_text("\n".join(f'{i["latin"]}  –  {i["german"]}' for i in hard), encoding="utf-8")

    def reset_all(self):
        if messagebox.askyesno("Zurücksetzen", "Wirklich den gesamten Lernfortschritt löschen?"):
            self.cards, self.daily, self.best_streak = {}, {}, 0
            self.favorites = set()
            self.save()
            self.refresh_all()

    # ------------------------------------------------------------ Aktualisieren
    def refresh_all(self):
        self.refresh_setup()
        self.refresh_list()
        self.refresh_stats()
        self.update_head()

    def update_head(self):
        d = self.daily.get(date.today().isoformat(), {"asked": 0, "ok": 0})
        streak = self.sess.get("streak", 0) if self.session_active else 0
        self.head_info.set(f"🔥 Serie: {streak}     Heute: {d['ok']} / {d['asked']} richtig     "
                           f"Lerntage in Folge: {self.day_streak()}")

    def refresh_setup(self):
        st = self.cat_stats()
        tot = {k: sum(v[k] for v in st.values()) for k in ("n", "new", "due", "mastered")}
        self.setup_info.set(f"{tot['n']} Vokabeln  •  {tot['mastered']} gelernt  •  {tot['due']} fällig  •  {tot['new']} neu")
        for cat, cb in self.cat_checks.items():
            r = st[cat]
            cb.configure(text=f"{cat}   ({r['n']} • {r['due']} fällig • {r['new']} neu)")

    # ------------------------------------------------------------ Sitzung
    def box_of(self, cid):
        c = self.cards.get(cid)
        return c["box"] if c else 0

    def build_queue(self, pool, strategy, n):
        now = time.time()
        cards = self.cards
        if strategy.startswith("Intelligent"):
            due = [i for i in pool if i["id"] in cards and cards[i["id"]]["due"] <= now]
            due.sort(key=lambda i: (cards[i["id"]]["box"], random.random()))
            new = [i for i in pool if i["id"] not in cards]
            random.shuffle(new)
            rest = sorted((i for i in pool if i["id"] in cards and cards[i["id"]]["due"] > now),
                          key=lambda i: cards[i["id"]]["due"])
            q = due + new + rest
        elif strategy.startswith("Reihenfolge"):
            q = list(pool)
        elif strategy.startswith("Nur neue"):
            q = [i for i in pool if i["id"] not in cards]
        elif strategy.startswith("Nur schwierige"):
            q = [i for i in pool if i["id"] in cards and cards[i["id"]]["bad"] > 0]
            q.sort(key=lambda i: -(cards[i["id"]]["bad"] - cards[i["id"]]["ok"]))
        elif strategy.startswith("Nur Favoriten"):
            q = [i for i in pool if i["id"] in self.favorites]
        else:
            q = list(pool)
            random.shuffle(q)
        if n:
            q = q[:n]
        if not strategy.startswith("Reihenfolge"):
            random.shuffle(q)
        return q

    def start_session(self, items=None):
        self.save_setup()
        if items is None:
            cats = [c for c, v in self.cat_vars.items() if v.get()]
            if not cats:
                messagebox.showinfo("Auswahl", "Bitte mindestens ein Kapitel auswählen.")
                return
            pool = [i for i in DATA if i["cat"] in cats]
            n = None if self.s_count.get() == "Alle" else int(self.s_count.get())
            items = self.build_queue(pool, self.s_strategy.get(), n)
        if not items:
            messagebox.showinfo("Keine Vokabeln", "Für diese Auswahl gibt es keine passenden Vokabeln.\n"
                                "Wähle eine andere Auswahl oder andere Kapitel.")
            return
        self.queue = list(items)
        self.sess = dict(total=len(items), done=0, correct_first=0, wrong_first=0, streak=0, best=0,
                         attempted=set(), repeats={}, wrong_items=[], start=time.time(),
                         mode=self.s_mode.get(), direction=self.s_dir.get())
        self.session_active = True
        self.show_frame("card")
        self.next_card()

    def quick_due(self):
        now = time.time()
        due = [i for i in DATA if i["id"] in self.cards and self.cards[i["id"]]["due"] <= now]
        if not due:
            messagebox.showinfo("Fällige Vokabeln", "Aktuell ist nichts fällig 🎉\nStarte eine Sitzung mit neuen Vokabeln.")
            return
        due.sort(key=lambda i: (self.cards[i["id"]]["box"], random.random()))
        self.start_session(items=due[:30])

    def repeat_wrong(self):
        items = list(self.sess.get("wrong_items", []))
        if items:
            random.shuffle(items)
            self.start_session(items=items)

    def back_to_setup(self):
        self.session_active = False
        self.show_frame("setup")
        self.refresh_all()

    def cancel_jobs(self):
        for attr in ("after_job", "timer_job"):
            job = getattr(self, attr)
            if job:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, attr, None)
        self.timer_var.set("")

    def next_card(self):
        self.cancel_jobs()
        if not self.queue:
            self.finish_session()
            return
        it = self.current = self.queue.pop(0)
        d = self.sess["direction"]
        self.direction = "la" if d.startswith("Latein") else "de" if d.startswith("Deutsch") else random.choice(("la", "de"))
        self.awaiting_next = self.revealed = False
        self.hint_level, self.last_info = 0, None
        self.q_var.set(it["latin"] if self.direction == "la" else it["german"])
        self.dir_var.set("Latein → Deutsch" if self.direction == "la" else "Deutsch → Latein")
        self.hint_var.set("")
        self.fb_var.set("")
        self.fb_label.configure(style="Card.TLabel")
        b = self.box_of(it["id"])
        self.box_var.set("🆕 Neue Vokabel" if b == 0 else f"📦 Box {b} von 5")
        self.cat_var.set(it["cat"])
        self.update_progress()
        self.update_fav_button()
        for w in (self.entry, self.mc_frame, self.flash_lbl):
            w.pack_forget()
        mode = self.sess["mode"]
        if mode == "Eintippen":
            self.answer_var.set("")
            self.entry.pack(fill="x", padx=60)
            self.entry.focus_set()
            self.show_buttons("hint", "check", "reveal", "fav", "stop")
            if self.settings["auto_hint"]:
                self.hint()
        elif mode == "Multiple Choice":
            self.build_mc()
            self.mc_frame.pack(fill="x", padx=40)
            self.show_buttons("reveal", "fav", "stop")
        else:
            self.flash_lbl.pack()
            self.show_buttons("flip", "fav", "stop")
        if self.settings["timer"] and mode != "Karteikarten":
            self.remaining = int(self.settings["timer_seconds"])
            self.tick()
        self.update_head()

    def update_progress(self):
        s = self.sess
        self.pbar.configure(maximum=max(1, s["total"]), value=s["done"])
        self.prog_var.set(f"{s['done']} / {s['total']} geschafft  •  {len(self.queue) + 1} offen")

    def tick(self):
        if self.awaiting_next:
            return
        if self.remaining <= 0:
            self.timer_var.set("⏱ Zeit abgelaufen")
            self.grade(False, "⏱ Zeit abgelaufen")
            return
        self.timer_var.set(f"⏱ {self.remaining} s")
        self.remaining -= 1
        self.timer_job = self.after(1000, self.tick)

    # ------------------------------------------------------- Erwartete Antwort
    def expected_raw(self):
        it = self.current
        return it["german"] if self.direction == "la" else " | ".join(DE_TO_LA[it["german"]])

    def expected_display(self):
        return self.expected_raw().replace(" | ", "   oder   ")

    # ------------------------------------------------------------- Hinweis
    def hint(self):
        if not self.current or self.sess.get("mode") != "Eintippen" or self.awaiting_next:
            return
        self.hint_level += 1
        self.hint_var.set("Hinweis:  " + hint_text(self.expected_raw(), self.hint_level))

    # ------------------------------------------------------------- Prüfen
    def check_answer(self):
        if self.awaiting_next or not self.current:
            return
        st = evaluate(self.answer_var.get(), self.expected_raw(), self.settings["tolerance"])
        if st == "empty":
            self.fb_var.set("Bitte zuerst eine Antwort eingeben – oder „Weiß ich nicht“ wählen.")
            self.fb_label.configure(style="Muted.Card.TLabel")
            return
        if st == "correct":
            self.grade(True, "✓ Richtig!")
        elif st == "almost":
            self.grade(False, "≈ Fast richtig – kleiner Fehler", allow_override=True)
        elif st == "partial":
            self.grade(False, "≈ Nur ein Teil – es fehlt noch etwas", allow_override=True)
        else:
            self.grade(False, "✗ Leider falsch")

    def give_up(self):
        if not self.awaiting_next:
            self.grade(False, "Aufgedeckt")

    def grade(self, ok, headline, allow_override=False):
        if self.awaiting_next or not self.current:
            return
        self.cancel_jobs()
        self.awaiting_next = True
        it, s = self.current, self.sess
        cid = it["id"]
        first = cid not in s["attempted"]
        s["attempted"].add(cid)
        prev = copy.deepcopy(self.cards.get(cid)) if first else None
        if first:
            self.record_result(cid, ok)
            if ok:
                s["correct_first"] += 1
            else:
                s["wrong_first"] += 1
                s["wrong_items"].append(it)
        requeued = done_inc = False
        if ok:
            s["streak"] += 1
            s["best"] = max(s["best"], s["streak"])
            self.best_streak = max(self.best_streak, s["streak"])
            s["done"] += 1
            done_inc = True
        else:
            s["streak"] = 0
            r = s["repeats"].get(cid, 0)
            if r < 2:
                s["repeats"][cid] = r + 1
                self.queue.insert(min(len(self.queue), 3), it)
                requeued = True
            else:
                s["done"] += 1
                done_inc = True
        self.last_info = dict(cid=cid, first=first, prev=prev, requeued=requeued, done_inc=done_inc, ok=ok)

        text = headline + ("\n" + self.expected_display() if headline else self.expected_display())
        if not ok and self.sess["mode"] == "Eintippen" and self.answer_var.get().strip() and headline != "Aufgedeckt":
            text += f"\n(deine Antwort: {self.answer_var.get().strip()})"
        self.fb_var.set(text)
        self.fb_label.configure(style="Good.Card.TLabel" if ok else "Warn.Card.TLabel" if allow_override else "Bad.Card.TLabel")
        self.update_progress()
        self.update_head()
        if self.sess["mode"] != "Karteikarten":
            names = (["override"] if allow_override else []) + ["next", "fav", "stop"]
            self.show_buttons(*names)
            if ok and self.settings["auto_next"]:
                self.after_job = self.after(int(self.settings["auto_delay"]), self.next_card)

    def override(self):
        info = self.last_info
        if not self.awaiting_next or not info or info["ok"]:
            return
        s, it, cid = self.sess, self.current, info["cid"]
        if info["first"]:
            self.undo_record(cid, info["prev"])
            self.record_result(cid, True)
            s["wrong_first"] -= 1
            s["correct_first"] += 1
            if it in s["wrong_items"]:
                s["wrong_items"].remove(it)
        if info["requeued"]:
            if it in self.queue:
                self.queue.remove(it)
            s["repeats"][cid] -= 1
        if not info["done_inc"]:
            s["done"] += 1
        s["streak"] += 1
        s["best"] = max(s["best"], s["streak"])
        info["ok"] = True
        self.fb_var.set("✓ Als richtig gewertet\n" + self.expected_display())
        self.fb_label.configure(style="Good.Card.TLabel")
        self.show_buttons("next", "fav", "stop")
        self.update_progress()
        self.update_head()

    # ------------------------------------------------------ Karteikasten (Leitner)
    def record_result(self, cid, ok):
        now = time.time()
        c = self.cards.get(cid)
        if c is None:
            c = self.cards[cid] = {"box": 1, "due": now, "ok": 0, "bad": 0, "streak": 0, "last": now}
        if ok:
            c["ok"] += 1
            c["streak"] += 1
            c["box"] = min(5, c["box"] + 1)
        else:
            c["bad"] += 1
            c["streak"] = 0
            c["box"] = 1
        c["last"] = now
        c["due"] = now + BOX_DAYS[c["box"]] * 86400
        d = self.daily.setdefault(date.today().isoformat(), {"asked": 0, "ok": 0})
        d["asked"] += 1
        d["ok"] += 1 if ok else 0
        self.save()

    def undo_record(self, cid, prev):
        if prev is None:
            self.cards.pop(cid, None)
        else:
            self.cards[cid] = prev
        d = self.daily.get(date.today().isoformat())
        if d:
            d["asked"] = max(0, d["asked"] - 1)

    # --------------------------------------------------------- Multiple Choice
    def build_mc(self):
        for w in self.mc_frame.winfo_children():
            w.destroy()
        it, la, p = self.current, self.direction == "la", self.pal

        def ans(x):
            return x["german"] if la else "   oder   ".join(DE_TO_LA[x["german"]])

        correct = ans(it)
        same = [x for x in DATA if x["cat"] == it["cat"] and x["german"] != it["german"]]
        other = [x for x in DATA if x["german"] != it["german"]]
        random.shuffle(same)
        random.shuffle(other)
        wrong = []
        for x in same + other:
            a = ans(x)
            if a != correct and a not in wrong:
                wrong.append(a)
            if len(wrong) == 3:
                break
        self.mc_options = wrong + [correct]
        random.shuffle(self.mc_options)
        self.mc_correct = correct
        self.mc_buttons = []
        for i, o in enumerate(self.mc_options):
            b = tk.Button(self.mc_frame, text=f"{i + 1}   {o}", anchor="w", justify="left", wraplength=820,
                          bg=p["panel"], fg=p["fg"], activebackground=p["border"], activeforeground=p["fg"],
                          relief="flat", bd=0, padx=16, pady=10, font=(self.fam, 12), cursor="hand2",
                          command=lambda i=i: self.choose(i))
            b.pack(fill="x", pady=4)
            self.mc_buttons.append(b)

    def choose(self, i):
        if self.awaiting_next or i >= len(self.mc_options):
            return
        p = self.pal
        ok = self.mc_options[i] == self.mc_correct
        for b, o in zip(self.mc_buttons, self.mc_options):
            if o == self.mc_correct:
                b.configure(bg=p["good"], fg="#ffffff")
            elif b is self.mc_buttons[i]:
                b.configure(bg=p["bad"], fg="#ffffff")
        self.grade(ok, "✓ Richtig!" if ok else "✗ Leider falsch")

    # --------------------------------------------------------------- Karteikarte
    def flip(self):
        if self.revealed or self.awaiting_next or not self.current:
            return
        self.revealed = True
        self.fb_var.set(self.expected_display())
        self.fb_label.configure(style="Accent.Card.TLabel")
        self.show_buttons("know", "dont", "fav", "stop")

    def flash_answer(self, ok):
        if not self.revealed or self.awaiting_next:
            return
        self.grade(ok, "")
        self.next_card()

    # ------------------------------------------------------------------ Favoriten
    def toggle_fav(self):
        if not self.current:
            return
        self.favorites ^= {self.current["id"]}
        self.update_fav_button()
        self.save()

    def update_fav_button(self):
        if self.current:
            self.btns["fav"].configure(text="★ Favorit" if self.current["id"] in self.favorites else "☆ Favorit")

    # --------------------------------------------------------------- Tastatur
    def on_key(self, e):
        if not self.session_active or self.nb.index("current") != 0 or not self.current:
            return
        mode = self.sess["mode"]
        if e.keysym in ("Return", "KP_Enter"):
            if self.awaiting_next:
                self.next_card()
            elif mode == "Eintippen":
                self.check_answer()
            elif mode == "Karteikarten":
                self.flip()
        elif mode == "Karteikarten":
            if e.keysym == "space":
                self.flip()
            elif self.revealed and e.char in ("1", "2"):
                self.flash_answer(e.char == "1")
        elif mode == "Multiple Choice" and e.char in ("1", "2", "3", "4") and not self.awaiting_next:
            self.choose(int(e.char) - 1)

    # ------------------------------------------------------------------- Ende
    def finish_session(self):
        self.cancel_jobs()
        was_active = self.session_active
        self.session_active = False
        s = self.sess
        if not was_active or not s:
            self.show_frame("setup")
            return
        first = s["correct_first"] + s["wrong_first"]
        pct = (s["correct_first"] / first * 100) if first else 0
        mins, secs = divmod(int(time.time() - s["start"]), 60)
        if first == 0:
            title = "Sitzung beendet"
        elif pct >= 90:
            title = "🏆 Hervorragend!"
        elif pct >= 70:
            title = "👍 Gut gemacht!"
        else:
            title = "💪 Dranbleiben – Übung macht den Meister!"
        self.sum_title.set(title)
        self.sum_text.set(f"Beim ersten Versuch richtig: {s['correct_first']} von {first}  ({pct:.0f} %)\n"
                          f"Beste Serie: {s['best']}      Dauer: {mins} min {secs:02d} s")
        self.sum_tree.delete(*self.sum_tree.get_children())
        for it in s["wrong_items"]:
            self.sum_tree.insert("", "end", values=(it["latin"], it["german"]))
        self.btn_repeat.configure(state="normal" if s["wrong_items"] else "disabled")
        self.save()
        self.show_frame("summary")
        self.refresh_all()


if __name__ == "__main__":
    App().mainloop()