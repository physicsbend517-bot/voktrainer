# -*- coding: utf-8 -*-
"""
Caesar Vokabeltrainer 2.0 – Streamlit-Version
Alle Vokabeln aus "Lernvokabular Caesar Grundwortschatz.pdf"
(Kleine Wörter + Caesar-Wortschatz bis "Caesare imperante").

Start:
    pip install streamlit
    streamlit run caesar_vokabeltrainer_streamlit.py

Funktionen (identisch zur tkinter-Version):
  * Alle Vokabeln der PDF, sortiert nach Kapiteln (frei kombinierbar)
  * Leitner-Karteikasten (5 Boxen) mit Wiederholungsterminen (Spaced Repetition)
  * 3 Lernmodi: Eintippen, Multiple Choice, Karteikarten
  * Falsche Vokabeln kommen in der Sitzung automatisch bald wieder
  * Schrittweise Hinweise, "Als richtig werten", Zeitlimit, Favoriten
  * Vokabelliste mit Suche/Filter, Statistik, 7-Tage-Diagramm, Lerntage-Serie
  * Fortschritt wird in "caesar_fortschritt.json" gespeichert
    (zusätzlich: Export/Import als Datei, z. B. für Streamlit Cloud)
"""

import copy
import html
import inspect
import json
import random
import re
import time
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Caesar Vokabeltrainer", page_icon="📜", layout="wide")

APP_TITLE = "Caesar Vokabeltrainer"
try:
    _BASE_DIR = Path(__file__).resolve().parent
except NameError:
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
# KONSTANTEN & EINSTELLUNGEN
# ----------------------------------------------------------------------------
BOX_DAYS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 21}
MODES = ["Eintippen", "Multiple Choice", "Karteikarten"]
DIRECTIONS = ["Latein → Deutsch", "Deutsch → Latein", "Gemischt"]
STRATEGIES = ["Intelligent (fällige zuerst)", "Zufällig", "Reihenfolge der PDF",
              "Nur neue Vokabeln", "Nur schwierige", "Nur Favoriten"]
COUNTS = ["10", "20", "30", "50", "Alle"]
STATUS_FILTER = ["Alle", "Neu", "Schwierig", "Favoriten", "Gelernt (Box 4–5)", "Fällig"]

DEFAULT_SETTINGS = {
    "tolerance": 0.88, "auto_next": True, "auto_delay": 1100,
    "timer": False, "timer_seconds": 20, "auto_hint": False, "q_size": 30,
    "mode": "Eintippen", "direction": "Latein → Deutsch", "strategy": STRATEGIES[0],
    "count": "20", "cats": None,
}
BY_ID = {i["id"]: i for i in DATA}


def _stretch(fn):
    try:
        return {"width": "stretch"} if "width" in inspect.signature(fn).parameters else {"use_container_width": True}
    except (TypeError, ValueError):
        return {}


W_BTN = _stretch(st.button)
W_FSB = _stretch(st.form_submit_button)
W_DF = _stretch(st.dataframe)
W_DL = _stretch(st.download_button)


# ----------------------------------------------------------------------------
# SPEICHER
# ----------------------------------------------------------------------------
def load_store():
    try:
        return json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def init_state():
    if "store" in st.session_state:
        return
    raw = load_store()
    settings = dict(DEFAULT_SETTINGS)
    settings.update(raw.get("settings", {}))
    st.session_state.store = {
        "cards": raw.get("cards", {}), "favorites": set(raw.get("favorites", [])),
        "daily": raw.get("daily", {}), "best_streak": raw.get("best_streak", 0), "settings": settings,
    }
    st.session_state.view = "setup"
    st.session_state.sess = None


def store():
    return st.session_state.store


def cfg():
    return st.session_state.store["settings"]


def ss():
    return st.session_state.sess


def export_dict():
    S = store()
    return {"cards": S["cards"], "favorites": sorted(S["favorites"]), "daily": S["daily"],
            "best_streak": S["best_streak"], "settings": S["settings"]}


def save():
    try:
        tmp = SAVE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(export_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(SAVE_FILE)
    except OSError:
        pass


def toast(msg):
    st.session_state.flash_msg = msg


# ----------------------------------------------------------------------------
# KARTEIKASTEN (LEITNER)
# ----------------------------------------------------------------------------
def box_of(cid):
    c = store()["cards"].get(cid)
    return c["box"] if c else 0


def record_result(cid, ok):
    now = time.time()
    cards = store()["cards"]
    c = cards.get(cid)
    if c is None:
        c = cards[cid] = {"box": 1, "due": now, "ok": 0, "bad": 0, "streak": 0, "last": now}
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
    d = store()["daily"].setdefault(date.today().isoformat(), {"asked": 0, "ok": 0})
    d["asked"] += 1
    d["ok"] += 1 if ok else 0
    save()


def undo_record(cid, prev):
    cards = store()["cards"]
    if prev is None:
        cards.pop(cid, None)
    else:
        cards[cid] = prev
    d = store()["daily"].get(date.today().isoformat())
    if d:
        d["asked"] = max(0, d["asked"] - 1)


def cat_stats():
    now = time.time()
    res = {c: {"n": 0, "new": 0, "due": 0, "mastered": 0} for c in CATEGORIES}
    cards = store()["cards"]
    for it in DATA:
        r = res[it["cat"]]
        r["n"] += 1
        c = cards.get(it["id"])
        if c is None:
            r["new"] += 1
        else:
            r["due"] += c["due"] <= now
            r["mastered"] += c["box"] >= 4
    return res


def day_streak():
    daily = store()["daily"]
    d, n = date.today(), 0
    if daily.get(d.isoformat(), {}).get("asked", 0) == 0:
        d -= timedelta(days=1)
    while daily.get(d.isoformat(), {}).get("asked", 0) > 0:
        n += 1
        d -= timedelta(days=1)
    return n


# ----------------------------------------------------------------------------
# SITZUNG
# ----------------------------------------------------------------------------
def build_queue(pool, strategy, n):
    now = time.time()
    cards, favs = store()["cards"], store()["favorites"]
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
        q = [i for i in pool if i["id"] in favs]
    else:
        q = list(pool)
        random.shuffle(q)
    if n:
        q = q[:n]
    if not strategy.startswith("Reihenfolge"):
        random.shuffle(q)
    return q


def collect_setup():
    c, g = cfg(), st.session_state.get
    c["mode"] = g("s_mode", c["mode"])
    c["direction"] = g("s_dir", c["direction"])
    c["strategy"] = g("s_strategy", c["strategy"])
    c["count"] = g("s_count", c["count"])
    if any(f"cat_{i}" in st.session_state for i in range(len(CATEGORIES))):
        c["cats"] = [cat for i, cat in enumerate(CATEGORIES) if g(f"cat_{i}", True)]
    save()


def start_session(ids=None):
    collect_setup()
    c = cfg()
    if ids is None:
        cats = c["cats"] if c["cats"] is not None else CATEGORIES
        if not cats:
            toast("Bitte mindestens ein Kapitel auswählen.")
            return
        pool = [i for i in DATA if i["cat"] in cats]
        n = None if c["count"] == "Alle" else int(c["count"])
        ids = [i["id"] for i in build_queue(pool, c["strategy"], n)]
    if not ids:
        toast("Für diese Auswahl gibt es keine passenden Vokabeln. Wähle eine andere Auswahl oder andere Kapitel.")
        return
    st.session_state.sess = dict(
        queue=list(ids), total=len(ids), done=0, correct_first=0, wrong_first=0, streak=0, best=0,
        attempted=set(), repeats={}, wrong_items=[], start=time.time(), mode=c["mode"], dirsel=c["direction"],
        current=None, direction="la", awaiting=False, revealed=False, hint_level=0, last_info=None,
        fb="", fb_kind="", n=0, mc_options=[], mc_correct="", mc_pick=None, deadline=0.0,
        allow_override=False, auto_pending=False)
    st.session_state.view = "card"
    next_card()


def quick_due():
    now = time.time()
    cards = store()["cards"]
    due = [i for i in DATA if i["id"] in cards and cards[i["id"]]["due"] <= now]
    if not due:
        toast("Aktuell ist nichts fällig 🎉 Starte eine Sitzung mit neuen Vokabeln.")
        return
    due.sort(key=lambda i: (cards[i["id"]]["box"], random.random()))
    start_session([i["id"] for i in due[:30]])


def repeat_wrong():
    ids = list(ss().get("wrong_items", []))
    if ids:
        random.shuffle(ids)
        start_session(ids)


def back_to_setup():
    st.session_state.view = "setup"


def set_all_cats(val):
    for i in range(len(CATEGORIES)):
        st.session_state[f"cat_{i}"] = val


def cats_with_due():
    st_ = cat_stats()
    for i, cat in enumerate(CATEGORIES):
        st.session_state[f"cat_{i}"] = st_[cat]["due"] > 0


def expected_raw():
    s = ss()
    it = BY_ID[s["current"]]
    return it["german"] if s["direction"] == "la" else " | ".join(DE_TO_LA[it["german"]])


def expected_display():
    return expected_raw().replace(" | ", "   oder   ")


def build_mc():
    s = ss()
    it, la = BY_ID[s["current"]], s["direction"] == "la"

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
    opts = wrong + [correct]
    random.shuffle(opts)
    s["mc_options"], s["mc_correct"], s["mc_pick"] = opts, correct, None


def next_card():
    s = ss()
    if not s["queue"]:
        finish_session()
        return
    cid = s["queue"].pop(0)
    s["current"] = cid
    d = s["dirsel"]
    s["direction"] = "la" if d.startswith("Latein") else "de" if d.startswith("Deutsch") else random.choice(("la", "de"))
    s.update(awaiting=False, revealed=False, hint_level=0, last_info=None, fb="", fb_kind="",
             n=s["n"] + 1, allow_override=False, auto_pending=False)
    if s["mode"] == "Multiple Choice":
        build_mc()
    if s["mode"] == "Eintippen" and cfg()["auto_hint"]:
        s["hint_level"] = 1
    if cfg()["timer"] and s["mode"] != "Karteikarten":
        s["deadline"] = time.time() + int(cfg()["timer_seconds"])


def finish_session():
    s = ss()
    if not s:
        st.session_state.view = "setup"
        return
    s["awaiting"] = True
    st.session_state.view = "summary"
    save()


def hint():
    s = ss()
    if s and s["mode"] == "Eintippen" and not s["awaiting"]:
        s["hint_level"] += 1


def check_answer():
    s = ss()
    if s["awaiting"]:
        return
    ans = st.session_state.get(f"ans_{s['n']}", "")
    st_ = evaluate(ans, expected_raw(), cfg()["tolerance"])
    if st_ == "empty":
        s["fb"], s["fb_kind"] = "Bitte zuerst eine Antwort eingeben – oder „Weiß ich nicht“ wählen.", "info"
    elif st_ == "correct":
        grade(True, "✓ Richtig!")
    elif st_ == "almost":
        grade(False, "≈ Fast richtig – kleiner Fehler", allow_override=True)
    elif st_ == "partial":
        grade(False, "≈ Nur ein Teil – es fehlt noch etwas", allow_override=True)
    else:
        grade(False, "✗ Leider falsch")


def give_up():
    if not ss()["awaiting"]:
        grade(False, "Aufgedeckt")


def grade(ok, headline, allow_override=False):
    s = ss()
    if s["awaiting"] or s["current"] is None:
        return
    s["awaiting"] = True
    cid = s["current"]
    first = cid not in s["attempted"]
    s["attempted"].add(cid)
    prev = copy.deepcopy(store()["cards"].get(cid)) if first else None
    if first:
        record_result(cid, ok)
        if ok:
            s["correct_first"] += 1
        else:
            s["wrong_first"] += 1
            s["wrong_items"].append(cid)
    requeued = done_inc = False
    if ok:
        s["streak"] += 1
        s["best"] = max(s["best"], s["streak"])
        store()["best_streak"] = max(store()["best_streak"], s["streak"])
        s["done"] += 1
        done_inc = True
    else:
        s["streak"] = 0
        r = s["repeats"].get(cid, 0)
        if r < 2:
            s["repeats"][cid] = r + 1
            s["queue"].insert(min(len(s["queue"]), 3), cid)
            requeued = True
        else:
            s["done"] += 1
            done_inc = True
    s["last_info"] = dict(cid=cid, first=first, prev=prev, requeued=requeued, done_inc=done_inc, ok=ok)
    text = headline + ("\n" + expected_display() if headline else expected_display())
    user = st.session_state.get(f"ans_{s['n']}", "").strip() if s["mode"] == "Eintippen" else ""
    if not ok and user and headline != "Aufgedeckt":
        text += f"\n(deine Antwort: {user})"
    s["fb"] = text
    s["fb_kind"] = "good" if ok else "warn" if allow_override else "bad"
    s["allow_override"] = allow_override
    s["auto_pending"] = bool(ok and cfg()["auto_next"] and s["mode"] != "Karteikarten")
    save()


def override():
    s = ss()
    info = s["last_info"]
    if not s["awaiting"] or not info or info["ok"]:
        return
    cid = info["cid"]
    if info["first"]:
        undo_record(cid, info["prev"])
        record_result(cid, True)
        s["wrong_first"] -= 1
        s["correct_first"] += 1
        if cid in s["wrong_items"]:
            s["wrong_items"].remove(cid)
    if info["requeued"]:
        if cid in s["queue"]:
            s["queue"].remove(cid)
        s["repeats"][cid] -= 1
    if not info["done_inc"]:
        s["done"] += 1
    s["streak"] += 1
    s["best"] = max(s["best"], s["streak"])
    info["ok"] = True
    s["allow_override"] = False
    s["fb"], s["fb_kind"] = "✓ Als richtig gewertet\n" + expected_display(), "good"
    save()


def choose(i):
    s = ss()
    if s["awaiting"] or i >= len(s["mc_options"]):
        return
    s["mc_pick"] = i
    ok = s["mc_options"][i] == s["mc_correct"]
    grade(ok, "✓ Richtig!" if ok else "✗ Leider falsch")


def flip():
    s = ss()
    if s["revealed"] or s["awaiting"]:
        return
    s["revealed"] = True
    s["fb"], s["fb_kind"] = expected_display(), "accent"


def flash_answer(ok):
    s = ss()
    if not s["revealed"] or s["awaiting"]:
        return
    s["fb"], s["fb_kind"] = "", ""
    grade(ok, "")
    next_card()


def toggle_fav(cid):
    favs = store()["favorites"]
    favs ^= {cid}
    save()


# ----------------------------------------------------------------------------
# OBERFLÄCHE
# ----------------------------------------------------------------------------
def md_escape(text):
    for ch in ("\\", "*", "_", "`", "~", "<", ">", "#", "$"):
        text = text.replace(ch, "\\" + ch)
    return text.replace("\n", "  \n")


def centered(text, size="1rem", color=None, weight="400", mono=False, opacity=None):
    style = f"text-align:center;font-size:{size};font-weight:{weight};"
    if color:
        style += f"color:{color};"
    if opacity:
        style += f"opacity:{opacity};"
    if mono:
        style += "font-family:monospace;"
    st.markdown(f"<div style='{style}'>{html.escape(text)}</div>", unsafe_allow_html=True)


def show_feedback(s):
    if not s["fb"]:
        return
    kind = s["fb_kind"]
    if kind == "accent":
        centered(s["fb"], "1.7rem", "#6c8cff", "700")
        return
    {"good": st.success, "warn": st.warning, "bad": st.error, "info": st.info}.get(kind, st.info)(md_escape(s["fb"]))


def _timer_body():
    s = ss()
    if not s or s["awaiting"] or st.session_state.view != "card":
        return
    rem = int(s["deadline"] - time.time()) + 1
    if rem <= 0:
        grade(False, "⏱ Zeit abgelaufen")
        st.rerun()
    else:
        st.caption(f"⏱ {rem} s")


_timer_fragment = st.fragment(run_every=1)(_timer_body) if hasattr(st, "fragment") else None


def render_setup():
    c = cfg()
    cs = cat_stats()
    tot = {k: sum(v[k] for v in cs.values()) for k in ("n", "new", "due", "mastered")}
    st.caption(f"{tot['n']} Vokabeln  •  {tot['mastered']} gelernt  •  {tot['due']} fällig  •  {tot['new']} neu")
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Kapitel auswählen")
            for i, cat in enumerate(CATEGORIES):
                r = cs[cat]
                st.checkbox(f"{cat}   ({r['n']} • {r['due']} fällig • {r['new']} neu)",
                            value=(c["cats"] is None or cat in c["cats"]), key=f"cat_{i}")
            b1, b2, b3 = st.columns(3)
            b1.button("Alle", on_click=set_all_cats, args=(True,), **W_BTN)
            b2.button("Keine", on_click=set_all_cats, args=(False,), **W_BTN)
            b3.button("Nur mit fälligen", on_click=cats_with_due, **W_BTN)
    with right:
        with st.container(border=True):
            st.subheader("Lernsitzung")

            def pick(label, opts, key, cur):
                st.selectbox(label, opts, index=opts.index(cur) if cur in opts else 0, key=key)

            pick("Modus", MODES, "s_mode", c["mode"])
            pick("Richtung", DIRECTIONS, "s_dir", c["direction"])
            pick("Auswahl", STRATEGIES, "s_strategy", c["strategy"])
            pick("Anzahl Vokabeln", COUNTS, "s_count", c["count"])
            st.button("▶  Lernen starten", type="primary", on_click=start_session, **W_BTN)
            st.button("⏰  Nur fällige Vokabeln wiederholen", on_click=quick_due, **W_BTN)
            st.caption("Tipp: Richtig beantwortete Vokabeln wandern im Karteikasten eine Box höher und kommen "
                       "später wieder (1 → 3 → 7 → 21 Tage). Falsche starten wieder in Box 1.")


def render_card():
    s, c = ss(), cfg()
    cid = s["current"]
    it = BY_ID[cid]
    mode, n, la = s["mode"], s["n"], s["direction"] == "la"
    b = box_of(cid)

    a, m, r = st.columns([2, 3, 2])
    a.markdown("🆕 **Neue Vokabel**" if b == 0 else f"📦 **Box {b} von 5**")
    m.caption(it["cat"])
    r.caption(f"{s['done']} / {s['total']} geschafft  •  {len(s['queue']) + 1} offen")
    st.progress(min(1.0, s["done"] / max(1, s["total"])))

    with st.container(border=True):
        centered("Latein → Deutsch" if la else "Deutsch → Latein", opacity="0.6")
        centered(it["latin"] if la else it["german"], f"{int(c['q_size'])}px", weight="700")
        if s["hint_level"] and not s["awaiting"]:
            centered("Hinweis:  " + hint_text(expected_raw(), s["hint_level"]), "1.3rem", "#ffb454", mono=True)

        if mode == "Eintippen":
            if not s["awaiting"]:
                with st.form(f"form_{n}", clear_on_submit=False):
                    st.text_input("Deine Antwort", key=f"ans_{n}", label_visibility="collapsed",
                                  placeholder="Übersetzung eintippen und Enter drücken …")
                    f1, f2, f3 = st.columns(3)
                    f1.form_submit_button("Prüfen  ↵", type="primary", on_click=check_answer, **W_FSB)
                    f2.form_submit_button("💡 Hinweis", on_click=hint, **W_FSB)
                    f3.form_submit_button("Weiß ich nicht", on_click=give_up, **W_FSB)
        elif mode == "Multiple Choice":
            if not s["awaiting"]:
                for i, o in enumerate(s["mc_options"]):
                    st.button(f"{i + 1}   {o}", key=f"mc_{n}_{i}", on_click=choose, args=(i,), **W_BTN)
            else:
                for i, o in enumerate(s["mc_options"]):
                    mark = "✅" if o == s["mc_correct"] else "❌" if i == s["mc_pick"] else "▫️"
                    st.markdown(f"{mark}  {md_escape(o)}")
        elif not s["revealed"]:
            centered("Überlege dir die Antwort – dann „Umdrehen“.", opacity="0.6")

        show_feedback(s)
        if c["timer"] and mode != "Karteikarten" and not s["awaiting"]:
            if _timer_fragment:
                _timer_fragment()

    # Aktionsleiste
    names = []
    if mode == "Karteikarten":
        names = ["flip"] if not s["revealed"] else ["know", "dont"]
    elif s["awaiting"]:
        if s["allow_override"] and not s["last_info"]["ok"]:
            names.append("override")
        names.append("next")
    elif mode == "Multiple Choice":
        names.append("giveup")
    names += ["fav", "stop"]
    cols = st.columns(len(names))
    for col, name in zip(cols, names):
        with col:
            if name == "flip":
                st.button("Umdrehen", key=f"b_flip_{n}", type="primary", on_click=flip, **W_BTN)
            elif name == "know":
                st.button("✓ Gewusst", key=f"b_know_{n}", type="primary", on_click=flash_answer, args=(True,), **W_BTN)
            elif name == "dont":
                st.button("✗ Nicht gewusst", key=f"b_dont_{n}", on_click=flash_answer, args=(False,), **W_BTN)
            elif name == "override":
                st.button("✔ Als richtig werten", key=f"b_ov_{n}", on_click=override, **W_BTN)
            elif name == "next":
                st.button("Weiter  ↵", key=f"b_next_{n}", type="primary", on_click=next_card, **W_BTN)
            elif name == "giveup":
                st.button("Weiß ich nicht", key=f"b_gu_{n}", on_click=give_up, **W_BTN)
            elif name == "fav":
                st.button("★ Favorit" if cid in store()["favorites"] else "☆ Favorit", key=f"b_fav_{n}",
                          on_click=toggle_fav, args=(cid,), **W_BTN)
            else:
                st.button("Beenden", key=f"b_stop_{n}", on_click=finish_session, **W_BTN)

    if s.get("auto_pending"):
        time.sleep(int(c["auto_delay"]) / 1000)
        s["auto_pending"] = False
        next_card()
        st.rerun()


def render_summary():
    s = ss()
    first = s["correct_first"] + s["wrong_first"]
    pct = (s["correct_first"] / first * 100) if first else 0
    mins, secs = divmod(int(time.time() - s["start"]), 60)
    title = ("Sitzung beendet" if first == 0 else "🏆 Hervorragend!" if pct >= 90 else
             "👍 Gut gemacht!" if pct >= 70 else "💪 Dranbleiben – Übung macht den Meister!")
    with st.container(border=True):
        st.subheader(title)
        st.markdown(f"Beim ersten Versuch richtig: **{s['correct_first']} von {first}** ({pct:.0f} %)  \n"
                    f"Beste Serie: **{s['best']}**   •   Dauer: **{mins} min {secs:02d} s**")
        st.caption("Diese Vokabeln solltest du nochmal ansehen:")
        if s["wrong_items"]:
            st.dataframe(pd.DataFrame([{"Latein": BY_ID[i]["latin"], "Deutsch": BY_ID[i]["german"]}
                                       for i in s["wrong_items"]]), hide_index=True, **W_DF)
        else:
            st.success("Keine Fehler – stark! 🎉")
        b1, b2 = st.columns(2)
        b1.button("🔁 Fehler wiederholen", type="primary", on_click=repeat_wrong,
                  disabled=not s["wrong_items"], **W_BTN)
        b2.button("Neue Sitzung", on_click=back_to_setup, **W_BTN)


def render_learn():
    v = st.session_state.view
    if v == "card" and ss() and ss()["current"] is not None:
        render_card()
    elif v == "summary" and ss():
        render_summary()
    else:
        render_setup()


# --------------------------------------------------------------- Vokabelliste
def list_action(what, ids):
    S = store()
    now = time.time()
    for cid in ids:
        if what == "fav":
            S["favorites"] ^= {cid}
        elif what == "learned":
            c = S["cards"].setdefault(cid, {"box": 5, "due": now, "ok": 0, "bad": 0, "streak": 0, "last": now})
            c["box"], c["due"] = 5, now + BOX_DAYS[5] * 86400
        elif what == "reset":
            S["cards"].pop(cid, None)
    save()


def render_list():
    S = store()
    c1, c2, c3 = st.columns([2, 2, 1.5])
    q = norm(c1.text_input("Suche", key="list_q"))
    cat = c2.selectbox("Kapitel", ["Alle Kapitel"] + CATEGORIES, key="list_cat")
    stat = c3.selectbox("Status", STATUS_FILTER, key="list_stat")
    now = time.time()
    rows, ids = [], []
    for it in DATA:
        c = S["cards"].get(it["id"])
        is_new, due = c is None, (c is not None and c["due"] <= now)
        hard = bool(c and c["bad"] > c["ok"])
        if cat != "Alle Kapitel" and it["cat"] != cat:
            continue
        if q and q not in norm(it["latin"]) and q not in norm(it["german"]):
            continue
        if stat == "Neu" and not is_new:
            continue
        if stat == "Schwierig" and not hard:
            continue
        if stat == "Favoriten" and it["id"] not in S["favorites"]:
            continue
        if stat.startswith("Gelernt") and not (c and c["box"] >= 4):
            continue
        if stat == "Fällig" and not due:
            continue
        status = "🆕 neu" if is_new else "✅ gelernt" if c["box"] >= 4 else "⚠️ schwierig" if hard else ""
        rows.append({"★": "★" if it["id"] in S["favorites"] else "", "Latein": it["latin"], "Deutsch": it["german"],
                     "Kapitel": it["cat"], "Box": "–" if is_new else c["box"],
                     "✓/✗": "" if is_new else f'{c["ok"]}/{c["bad"]}', "Status": status})
        ids.append(it["id"])
    st.caption(f"{len(rows)} von {len(DATA)} Vokabeln  •  Zeilen anklicken zum Auswählen")
    sel_ids = []
    if rows:
        df = pd.DataFrame(rows)
        try:
            ev = st.dataframe(df, hide_index=True, height=480, on_select="rerun", selection_mode="multi-row",
                              key="list_df", **W_DF)
            sel_ids = [ids[i] for i in ev.selection.rows if i < len(ids)]
        except TypeError:
            st.dataframe(df, hide_index=True, height=480, **W_DF)
            st.info("Für die Auswahl von Zeilen bitte Streamlit aktualisieren (pip install -U streamlit).")
    b1, b2, b3, _ = st.columns([1.3, 1.6, 1.3, 2])
    b1.button("★ Favorit umschalten", on_click=list_action, args=("fav", sel_ids), disabled=not sel_ids, **W_BTN)
    b2.button("Als gelernt markieren (Box 5)", on_click=list_action, args=("learned", sel_ids),
              disabled=not sel_ids, **W_BTN)
    b3.button("Zurücksetzen (neu)", on_click=list_action, args=("reset", sel_ids), disabled=not sel_ids, **W_BTN)


# ------------------------------------------------------------------ Statistik
def render_stats():
    S = store()
    cards = S["cards"]
    now = time.time()
    ok = sum(c["ok"] for c in cards.values())
    bad = sum(c["bad"] for c in cards.values())
    mastered = sum(c["box"] >= 4 for c in cards.values())
    due = sum(c["due"] <= now for c in cards.values())
    seen = len(cards)
    acc = (ok / (ok + bad) * 100) if ok + bad else 0

    m = st.columns(6)
    m[0].metric("Vokabeln gesamt", len(DATA))
    m[1].metric("Schon gesehen", seen)
    m[2].metric("Gelernt (Box 4–5)", mastered)
    m[3].metric("Jetzt fällig", due)
    m[4].metric("Trefferquote", f"{acc:.0f} %")
    m[5].metric("Lerntage in Folge", day_streak())
    st.caption(f"Antworten gesamt: {ok + bad}   •   Beste Serie richtig: {S['best_streak']}   •   "
               f"Favoriten: {len(S['favorites'])}")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Karteikasten")
            counts = {b: 0 for b in range(6)}
            counts[0] = len(DATA) - seen
            for c in cards.values():
                counts[c["box"]] += 1
            for b in range(6):
                a, p, n_ = st.columns([1, 6, 1])
                a.write("Neu" if b == 0 else f"Box {b}")
                p.progress(counts[b] / max(1, len(DATA)))
                n_.write(str(counts[b]))
        with st.container(border=True):
            st.subheader("Letzte 7 Tage")
            days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
            vals = [S["daily"].get(d.isoformat(), {"asked": 0, "ok": 0}) for d in days]
            df = pd.DataFrame({"Richtig": [v["ok"] for v in vals],
                               "Falsch": [v["asked"] - v["ok"] for v in vals]},
                              index=[d.strftime("%d.%m.") for d in days])
            st.bar_chart(df, color=["#34c88a", "#ff6b6b"])
    with right:
        with st.container(border=True):
            st.subheader("Fortschritt je Kapitel")
            st.caption("Gelernt = Box 4–5")
            for cat, r in cat_stats().items():
                a, p, n_ = st.columns([4, 3, 1])
                a.write(cat)
                p.progress(r["mastered"] / max(1, r["n"]))
                n_.write(f"{r['mastered']}/{r['n']}")
        with st.container(border=True):
            st.subheader("Die schwierigsten Vokabeln")
            hard = sorted((it for it in DATA if it["id"] in cards and cards[it["id"]]["bad"] > 0),
                          key=lambda it: -cards[it["id"]]["bad"])[:6]
            if hard:
                st.dataframe(pd.DataFrame([{"Latein": it["latin"], "Deutsch": it["german"],
                                            "✗": cards[it["id"]]["bad"]} for it in hard]),
                             hide_index=True, **W_DF)
            else:
                st.caption("Noch keine Fehler – weiter so!")


# ------------------------------------------------------------- Einstellungen
def on_setting():
    c, g = cfg(), st.session_state.get
    c["q_size"] = int(g("set_q", c["q_size"]))
    c["tolerance"] = float(g("set_tol", c["tolerance"]))
    c["auto_hint"] = bool(g("set_hint", c["auto_hint"]))
    c["auto_next"] = bool(g("set_next", c["auto_next"]))
    c["timer"] = bool(g("set_timer", c["timer"]))
    c["timer_seconds"] = int(g("set_tsec", c["timer_seconds"]))
    c["auto_delay"] = int(g("set_delay", c["auto_delay"]))
    save()


def import_progress():
    f = st.session_state.get("imp_file")
    if not f:
        return
    try:
        d = json.loads(f.getvalue().decode("utf-8"))
        S = store()
        S["cards"], S["favorites"] = d.get("cards", {}), set(d.get("favorites", []))
        S["daily"], S["best_streak"] = d.get("daily", {}), d.get("best_streak", 0)
        save()
        toast("Fortschritt importiert ✅")
    except Exception:
        toast("Die Datei konnte nicht gelesen werden.")


def reset_all():
    S = store()
    S["cards"], S["daily"], S["best_streak"], S["favorites"] = {}, {}, 0, set()
    st.session_state.reset_ok = False
    save()
    toast("Fortschritt zurückgesetzt.")


def render_settings():
    c = cfg()
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("Darstellung")
            st.caption("Hell/Dunkel: oben rechts ⋮ → Settings → Theme.")
            st.number_input("Schriftgröße der Frage", 18, 50, int(c["q_size"]), key="set_q", on_change=on_setting)
            st.slider("Tippfehler-Toleranz (höher = strenger)", 0.80, 0.98, float(c["tolerance"]), 0.01,
                      key="set_tol", on_change=on_setting)
    with right:
        with st.container(border=True):
            st.subheader("Lernhilfen")
            st.checkbox("Anfangsbuchstaben automatisch anzeigen", value=c["auto_hint"], key="set_hint", on_change=on_setting)
            st.checkbox("Nach richtiger Antwort automatisch weiter", value=c["auto_next"], key="set_next", on_change=on_setting)
            st.checkbox("Zeitlimit pro Vokabel", value=c["timer"], key="set_timer", on_change=on_setting)
            st.number_input("Zeitlimit (Sekunden)", 5, 120, int(c["timer_seconds"]), key="set_tsec", on_change=on_setting)
            st.number_input("Pause nach richtiger Antwort (ms)", 300, 5000, int(c["auto_delay"]), 100,
                            key="set_delay", on_change=on_setting)
    with st.container(border=True):
        st.subheader("Daten")
        S = store()
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("⬇ Fortschritt sichern (JSON)", json.dumps(export_dict(), ensure_ascii=False, indent=1),
                               file_name="caesar_fortschritt.json", mime="application/json", **W_DL)
            hard = [it for it in DATA if it["id"] in S["cards"] and S["cards"][it["id"]]["bad"] > S["cards"][it["id"]]["ok"]]
            if hard:
                st.download_button("⬇ Schwierige Vokabeln (TXT)", "\n".join(f'{i["latin"]}  –  {i["german"]}' for i in hard),
                                   file_name="schwierige_vokabeln.txt", **W_DL)
            else:
                st.caption("Es gibt noch keine schwierigen Vokabeln.")
        with d2:
            st.file_uploader("Fortschritt importieren", type=["json"], key="imp_file")
            st.button("Importieren", on_click=import_progress, disabled=not st.session_state.get("imp_file"), **W_BTN)
        with d3:
            st.checkbox("Ja, wirklich alles löschen", key="reset_ok")
            st.button("Gesamten Fortschritt zurücksetzen", type="primary", on_click=reset_all,
                      disabled=not st.session_state.get("reset_ok"), **W_BTN)
        st.caption("Hinweis: Auf Streamlit Cloud geht die gespeicherte Datei bei einem Neustart verloren – "
                   "sichere deinen Fortschritt dort regelmäßig über den Export.")


# ----------------------------------------------------------------------------
# HAUPTPROGRAMM
# ----------------------------------------------------------------------------
def main():
    init_state()
    msg = st.session_state.pop("flash_msg", None)
    if msg:
        st.toast(msg)
    S = store()
    d = S["daily"].get(date.today().isoformat(), {"asked": 0, "ok": 0})
    s = ss()
    streak = s["streak"] if (s and st.session_state.view == "card") else 0
    h1, h2 = st.columns([2, 3])
    h1.title("📜 Caesar Vokabeltrainer")
    h2.markdown(f"<div style='text-align:right;padding-top:1.4rem'>🔥 Serie: {streak} &nbsp;&nbsp; Heute: "
               f"{d['ok']} / {d['asked']} richtig &nbsp;&nbsp; Lerntage in Folge: {day_streak()}</div>",
               unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["Lernen", "Vokabelliste", "Statistik", "Einstellungen"])
    with t1:
        render_learn()
    with t2:
        render_list()
    with t3:
        render_stats()
    with t4:
        render_settings()


main()