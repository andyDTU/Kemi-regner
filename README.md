# 🧪 Kemilommeregner

En interaktiv kemiregner til gymnasiet og HF, bygget med Python og Streamlit.  
Giver trin-for-trin løsninger på de mest almindelige eksamensopgaver.

---

## 🚀 Kom i gang (Mac)

### Trin 1 – Hent programmet

Åbn **Terminal** (søg efter "Terminal" i Spotlight med ⌘ + mellemrum) og kør:

```bash
cd ~/Desktop
git clone https://github.com/andyDTU/Kemi-regner.git
cd Kemi-regner
```

> **Har du ikke Git?**  
> Gå til [github.com/andyDTU/Kemi-regner](https://github.com/andyDTU/Kemi-regner), klik på den grønne **Code**-knap → **Download ZIP**, pak filen ud på Skrivebordet og åbn Terminal i den mappe.

---

### Trin 2 – Start appen

```bash
bash run.sh
```

Det er det! Scriptet installerer automatisk alt det nødvendige og åbner appen i din browser på **http://localhost:8501**.

> Første gang tager det 1–2 minutter mens pakkerne installeres. Næste gang starter den på få sekunder.

---

### Trin 3 – Opdatér til nyeste version

Når der er kommet nye funktioner:

```bash
cd ~/Desktop/Kemi-regner
git pull
bash run.sh
python3 scripts/download_structure_images.py
```

> `download_structure_images.py` springer automatisk allerede hentede billeder over – kun nye stoffer hentes.

---

## 💻 Kom i gang (Windows)

### Forudsætninger
1. Installér [Python 3.10+](https://www.python.org/downloads/) – sæt flueben ved **"Add Python to PATH"** under installationen
2. Installér [Git](https://git-scm.com/download/win)

### Start

Åbn **Kommandoprompt** eller **PowerShell** og kør:

```bash
cd %USERPROFILE%\Desktop
git clone https://github.com/andyDTU/Kemi-regner.git
cd Kemi-regner
pip install -r requirements.txt
streamlit run app.py
```

### Opdatér til nyeste version (Windows)

```bash
cd %USERPROFILE%\Desktop\Kemi-regner
git pull
pip install -r requirements.txt
python scripts/download_structure_images.py
streamlit run app.py
```

---

## 📝 Exam-mode (begrænset netværk)

Appen kører **100% offline** – den forsøger aldrig at kontakte internet under brug.  
Forbered følgende **inden** eksamen (med internet):

```bash
cd ~/Desktop/Kemi-regner
git pull
python3 scripts/download_structure_images.py
```

Til eksamen:

```bash
bash run.sh
```

Åbn **http://localhost:8501** i din browser. Alt virker uden internet.

> `download_structure_images.py` henter strukturbilleder for alle stoffer (~20 MB, ~5–10 min).  
> Billederne gemmes lokalt og skal kun hentes **én gang** per computer.

---

## 📝 Sådan bruger du lommeregneren

### Find den rigtige beregner
Der er tre måder at finde den rigtige beregner til din opgave:

**1. Eksamensguide** (anbefalet)  
Klik på **📝 Eksamensguide** i menuen til venstre. Her finder du typiske eksamensopgaver – fx *"Beregn pH af 0,10 M HCl"* – med direkte link til den rigtige beregner.

**2. Søgefelt**  
Skriv i søgefeltet øverst i sidepanelet. Du kan søge på opgave-sprog:
- `beregn pH` → Syre/base-beregner
- `er reaktionen spontan` → Gibbs fri energi
- `ICE-tabel` → Ligevægt
- `begrænsende reaktant` → Stofmængder

**3. Forsiden**  
Klik på **🏠 Fundamentals** for at se alle beregnere som opgavekort.

---

## 🧮 Hvad kan den beregne?

| Emne | Indeholder bl.a. |
|------|-----------------|
| 🧪 Syrer & Baser | pH (stærk/svag syre/base), buffer, titrering |
| ⚖️ Atoms & Molarmasse | Molarmasse, procentsammensætning, elektronkonfiguration |
| 🧮 Stofmængder | Afstem reaktioner, begrænsende reaktant, fortynding, redox |
| 📊 Gasser | Ideel gaslov, Daltons lov, van der Waals, Graham |
| 🔥 Termokemi | ΔH°, Gibbs (ΔG), kalorimetri, opvarmningskurver, Hess |
| ⚗️ Ligevægt | ICE-tabel, Kc/Kp, reaktionskvotient Q, Le Chatelier |
| 🔋 Elektrokemi | Cellespænding E°, Nernst, ΔG og K, Faradays lov |
| ⚡ Kinetik | Integreret hastighedslov, halvliv, Arrhenius |
| 🌡️ Kolligative egenskaber | Kogepunktselevering, frysepunktssænkning, osmotisk tryk, find molarmasse |
| 🌫️ Damptryk | Raoults lov |
| 🔷 Geometri & Bindinger | VSEPR, Lewis-struktur, IMF, bindingsentalpier |
| ☢️ Nuklear kemi | α/β/γ-henfald, halvliv |
| 🧬 Organisk kemi | Funktionelle grupper, reaktionsprediktor, strukturreference |

---

## ❓ Fejlfinding

**"bash: run.sh: command not found"**  
Sørg for at du er i den rigtige mappe: `cd ~/Desktop/Kemi-regner`

**"command not found: python"**  
På Mac hedder kommandoen `python3` (ikke `python`). Brug `python3 scripts/download_structure_images.py`.

**"command not found: git"**  
Installér Git fra [git-scm.com](https://git-scm.com)

**Appen åbner ikke i browseren**  
Åbn selv [http://localhost:8501](http://localhost:8501) i din browser mens Terminal kører.

**Stop appen**  
Tryk `Ctrl + C` i Terminal.

---

## 🐛 Fejl eller forslag?

Opret et [Issue på GitHub](https://github.com/andyDTU/Kemi-regner/issues) – beskriv hvad der gik galt eller hvad du savner.
