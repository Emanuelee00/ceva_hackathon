# Scheda tecnica — FVL Dispatch Intelligence

Promemoria per rispondere a domande tecniche durante la presentazione. Ogni
numero qui sotto è verificato sui dati reali, non stimato a occhio — le fonti
sono i file Python indicati tra parentesi, consultabili se serve.

## 1. Il problema, in una riga

Nel dataset reale FVL 2026 (399.718 righe, 106.553 viaggi unici),
**il 34,45% di tutti i km percorsi sono a vuoto** (5,79M km su 16,8M km
totali, su 41.197 viaggi con distanza valida). È il numero centrale del
pitch — tutto il resto (dashboard, agente, mappa) è la soluzione costruita
attorno a questo numero.

Fonte: `analyze.py`, `cost_estimate.py` — verificato sia a livello di
viaggio deduplicato sia a livello di riga grezza (33,96%), il rapporto è
robusto in entrambi i casi.

## 2. Architettura in breve

```
Streamlit (app.py)
 ├─ Tab "Dispatcher check" — simulazione operativa in 4 step
 │   lot_builder.py → truck_picker.py → alert_ui.py → proposals_ui.py
 │   trip_map.py (mappa Leaflet/folium, routing reale via OSRM)
 │
 └─ Tab "Ask the data" — chat analitica
     agent/graph.py (LangGraph): router → tool → risposta template
     agent/llm.py: modello locale via Ollama (nessun dato esce dal laptop)

agent/autofill_graph.py — secondo grafo LangGraph, ciclo vero (non lineare):
     check → pick_best → check → ... finché il gap si chiude o non ci sono
     più candidati o si raggiunge il limite di iterazioni di sicurezza (10)
```

Tutta l'app gira su un'unica porta (8501) e un unico processo Python — non
c'è backend separato, non c'è database, i dati sono in memoria (pandas).

## 3. Stack tecnologico

| Componente | Scelta | Perché |
|---|---|---|
| UI | Streamlit 1.63 | dashboard interattiva senza scrivere frontend |
| Agente | LangGraph | orchestrazione a grafo, con un ciclo vero (auto-optimize), non solo routing lineare |
| LLM | Ollama, `qwen2.5:1.5b-instruct` locale | nessun dato aziendale esce dal laptop, no costi API |
| Mappa | folium (Leaflet) + streamlit-folium | routing reale via OSRM (servizio pubblico gratuito, no chiave) |
| Dati | pandas su CSV locale | 399.718 righe, nessun database esterno |

**Nota sul modello LLM**: inizialmente `qwen2.5:3b-instruct` (più accurato,
8/8 su un set di test di 8 domande IT/EN). Cambiato a `qwen2.5:1.5b-instruct`
durante l'hackathon per un vincolo di memoria della macchina (il modello da
3B ha smesso di entrare in RAM con troppi altri processi aperti) — se
qualcuno chiede "perché la chat a volte sbaglia il tool", questa è la
risposta onesta: modello più piccolo = meno accurato sul routing, scelta
fatta per necessità, documentata in `agent/llm.py`.

## 4. Dati: reali, simulati, stimati — la distinzione che conta

Questa è la domanda più probabile in un hackathon di analisi dati: **cosa è
vero e cosa è inventato?**

| Cosa | Reale/Simulato/Stimato | Dettaglio |
|---|---|---|
| Il numero 34,45% e tutte le statistiche aggregate | **Reale** | dai 399.718 record del dataset FVL 2026 |
| I 4 compound (Le Havre, Marckolsheim, Blyes, Marseille) | **Reale** | i veri Departure Name più frequenti nel dataset |
| I camion nel picker (targa, Loading Factor storico) | **Reale** | veri `Transport Truck Licence Plate`, esclusi 3 valori placeholder noti (una targa fittizia copriva da sola il 32% dei viaggi) |
| Le macchine nel "compose lot" | **Simulato** | non esiste un inventario reale per veicolo nel dataset — badge "Simulated inventory" sempre visibile in UI |
| Il percorso sulla mappa (ordine tappe, km) | **Reale/calcolato** | routing vero via OSRM sulle destinazioni reali delle macchine selezionate |
| Costo €/CO2 dei km a vuoto | **Stimato, assunzioni dichiarate** | vedi sezione 6 — non sono nel dataset, sono ipotesi esplicite |
| Il "massimo storico" di un camion | **Reale ma etichettato come riferimento** | mai chiamato "capacità certificata" — è solo il valore più alto mai registrato per quella targa |

Se chiedono "avete inventato qualcosa?" la risposta onesta è: **le macchine
del lotto sono simulate (dichiarato in UI), tutto il resto — camion, rotte,
percentuali — è reale o calcolato da dati reali con assunzioni esplicite**.

## 5. Le 4 fasi del dispatcher (cosa fa ciascuna tecnicamente)

1. **Compose lot** (`lot_builder.py`) — scegli un compound, seleziona
   macchine (mock) da una tabella. Il percorso sulla mappa **non è
   preselezionato**: viene calcolato al volo dalle destinazioni delle
   macchine effettivamente selezionate, con l'ordine di visita ottimale
   risolto dal servizio OSRM Trip (un mini problema del commesso
   viaggiatore, non solo la distanza più breve).
2. **Assign a truck** (`truck_picker.py`) — lista dei veri camion con
   almeno 5 viaggi nel dataset, ordinati per attività, con il loro vero
   storico Loading Factor.
3. **Check loading** (`alert_ui.py`) — confronta il carico del lotto col
   massimo storico del camion. Soglia regolabile via slider (default 0,5).
4. **Cars to add** (`proposals_ui.py`) — tabella di macchine candidate
   ordinate per detour minimo (haversine) e loading più alto, per chiudere
   il gap manualmente, oppure...

## 6. L'agente "Auto-optimize" — il vero ciclo LangGraph

`agent/autofill_graph.py` è un grafo a 2 nodi con un **ciclo reale**:

```
check (valuta il gap) → se alert: pick_best (aggiunge la miglior macchina)
   ↑___________________________________________|
→ se non c'è più alert, o non ci sono candidati, o si arriva a 10
  iterazioni: STOP
```

Non è un semplice classificatore a singolo step (quello è il router della
chat, un altro grafo, più semplice) — qui il grafo **ripete davvero** la
stessa decisione più volte, aggiornando lo stato a ogni giro, finché una
condizione di stop è vera. Verificato con un caso reale: 6 iterazioni per
chiudere un gap da 0 a 6,78 su un massimo di 7,0.

## 7. Formule e soglie esatte

- **Alert di sotto-ottimizzazione**: `gap = truck_max − lot_loading`;
  alert se `gap > soglia` (soglia default **0,5**, regolabile 0,1–2,0).
  File: `loading_check.py`.
- **Detour di una macchina candidata**: se la città di destinazione è già
  una tappa del percorso → "On route", detour 0. Altrimenti: distanza
  haversine minima verso una tappa esistente, **raddoppiata** (andata e
  ritorno) → "Detour". File: `proposals.py`.
- **Matching opportunity** (tool nella chat): una richiesta di partenza è
  "compatibile" se nello stesso dipartimento francese ed entro **3 giorni**
  (`WINDOW_DAYS = 3`) dalla consegna che ha liberato il camion.
  File: `matching_opportunity.py`.
- **Filtro camion nel picker**: solo targhe reali con almeno **5 viaggi**
  registrati, e con Loading Factor storico massimo **≤ 10** (il "general
  rule" del glossario FVL) — esclude l'89% delle targhe reali il cui
  massimo supera 10, altrimenti il gap con le macchine mock sarebbe troppo
  grande da chiudere nella demo. File: `loading_factor_alert.py`.

## 8. Assunzioni dichiarate (costo/CO2)

Non presenti nel dataset — dichiarate esplicitamente in `cost_estimate.py`,
mai presentate come dati misurati:

- Costo carburante: **0,55 €/km** (diesel, ~35 L/100km a ~1,60 €/L)
- Costo all-in (carburante+autista+manutenzione+pedaggi): **1,20 €/km**
  (range tipico pubblicato per trasporto pesante UE)
- CO2: **900 g/km** (fattore di emissione medio HDV diesel UE)

Risultato: 5.786.232 km a vuoto/anno → **~3,18M€ solo carburante / ~6,94M€
all-in / ~5.208 t CO2/anno**.

## 9. Le altre 2 analisi (usabili come argomenti extra)

- **Matching opportunity**: sui 41.197 viaggi reali, il **33,5%** dei viaggi
  a vuoto (11.880 su 35.410) aveva già una richiesta di partenza compatibile
  nelle vicinanze — **29,5%** dei km a vuoto (1.696.184 di 5.751.244 km) è
  quindi risolvibile con un dispatch migliore, non con più camion. Questo è
  un **limite inferiore misurato**, non una promessa.
- **Geo mismatch**: correlazione **r = 0,63** tra volumi di consegna FVL e
  immatricolazioni reali per dipartimento francese (94 dipartimenti).
  Hauts-de-Seine sovra-servito 3,6×, Parigi sotto-servita — due spiegazioni
  possibili disclosed (zona a traffico limitato vs sedi legali), non è
  possibile distinguerle con questi dati soli.
- **Concentrazione flotta**: escludendo 3 targhe placeholder (una da sola
  copriva il 32% dei viaggi — dato non realistico), **11.667 camion reali**
  gestiscono 67.797 viaggi, e il **top 10% dei camion porta il 76% dei
  viaggi** — un secondo argomento di concentrazione, utile per dire "un
  intervento mirato sul nucleo della flotta ha impatto sproporzionato".

## 10. Limiti noti — dillo prima che te lo chiedano

- **94% vs 28%**: applicando la regola dell'alert (gap > 0,5) a tutti i
  40.841 viaggi reali confrontando col **massimo storico** di ogni camion,
  il 94% risulta "sotto-ottimizzato" — ma è un artefatto statistico
  (confrontare ogni giorno col giorno migliore di sempre flagga quasi
  tutto). Confrontando con la **mediana** del camion, il numero scende a un
  più difendibile **28%** — mostriamo entrambi in app, mai solo il 94%.
- Solo il 68% delle righe ha `Trip Distance KM` valorizzato — motivo non
  100% confermato (ipotesi: l'ultimo viaggio di ogni camion nel periodo
  osservato non ha ancora un "prossimo viaggio" per calcolare il km vuoto).
- Le macchine del lotto sono un inventario simulato — non esiste nel
  dataset un collegamento veicolo↔compound in tempo reale.
- Il modello LLM locale è stato ridotto da 3B a 1.5B per vincoli di memoria
  della macchina demo — su un server reale con più RAM si userebbe il 3B
  (più accurato nel routing).

## 11. Domande-tipo e risposta pronta

**"Perché non usate un modello cloud (GPT/Claude) per la chat?"**
→ Scelta esplicita: nessun dato di trasporto aziendale esce dal laptop.
Compromesso accettato: risposte più lente (~10-15s) e un modello meno
potente, in cambio di privacy dei dati.

**"Il modello LLM può sbagliare/inventare numeri?"**
→ Il modello sceglie *solo* quale funzione Python chiamare (tra 6 fisse,
mai codice libero). Il testo della risposta è generato da template Python
deterministici, non da una seconda chiamata LLM — quindi ogni numero
mostrato in chat è esattamente quello calcolato da pandas, mai inventato.

**"Le macchine/il traffico che vedo sono reali?"**
→ Le auto nel lotto sono simulate (dichiarato con badge in UI). Camion,
percorsi stradali e tutte le percentuali del pitch sono reali o calcolati
da dati reali.

**"Quanto è scalabile questa soluzione?"**
→ La logica di matching/alert è già generica (funziona su qualunque
compound/camion nel dataset, non solo sui 3-4 usati in demo) — il limite
attuale è l'inventario veicoli simulato, non l'algoritmo.
