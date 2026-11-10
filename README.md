# TaskHub

Sistema di gestione task personale di Giorgio Terraneo, costruito su un artefatto
pubblicato di claude.ai. Una sola fonte di verità, accessibile sia da interfaccia
grafica sia da qualunque conversazione con Claude.

## Architettura

```
                 Task Hub (artefatto pubblicato su claude.ai)
                 ├── index.html   pagina: vista, filtri, modifica
                 └── database     config/main + tasks/<id>
                          ▲                      ▲
            read_db / write_db              lettura e scrittura live
                          │                      │
              Chat Claude (skill)        Browser e telefono
                          │
                 app desktop Claude
                          │
          C:\Users\giorg\OneDrive\Documenti\Tasks\TASKS.md
                   (copia in sola lettura, per uso offline)
```

Il database è l'unico posto in cui le task esistono. La pagina e le chat lo leggono
e lo scrivono; `TASKS.md` è una copia rigenerata dalle chat che girano nell'app
desktop, pensata per la consultazione offline e mai per la modifica.

## Contenuto della repository

| Percorso | Descrizione |
|---|---|
| `index.html` | Pagina dell'artefatto. File unico e autoconsistente: HTML, CSS e JavaScript insieme |
| `skill/SKILL.md` | Skill `task-manager`: protocollo che le chat seguono per leggere e scrivere le task |
| `skill/scripts/render_md.py` | Renderer di `TASKS.md` lato chat |
| `backups/` | Istantanee JSON del database |

Versione corrente: punto 2 (chain e dipendenze), 10 novembre 2026.

## Modello dati

`config/main`

| Campo | Tipo | Note |
|---|---|---|
| `categories` | lista di `{id, label, color, order, subcategories[]}` | Unico elenco valido di categorie |
| `mirror_path` | stringa | Percorso Windows della copia `TASKS.md` |

`tasks/<id>`

| Campo | Tipo | Note |
|---|---|---|
| `title` | stringa | |
| `category` | stringa | `id` di una categoria |
| `subcategory` | stringa o null | |
| `priority` | `H`, `M`, `L` | |
| `deadline` | `YYYY-MM-DD` o null | |
| `status` | `open`, `done`, `deleted` | `deleted` significa nel cestino |
| `done_at`, `deleted_at` | ISO datetime o null | |
| `kind` | `action` o `check` | `check` è un presidio: si attende qualcun altro |
| `waiting_on` | stringa o null | Per i presidi: chi deve consegnare |
| `recheck_days` | intero o null | Per i presidi: cadenza del controllo |
| `checks` | intero | Controlli andati a vuoto |
| `last_check` | ISO datetime o null | |
| `subtasks` | lista di `{text, done, done_at}` | |
| `notes` | stringa | |
| `created_at`, `updated_at`, `updated_by` | | `updated_by` è `hub` o `chat` |

## Funzionalità della pagina

- Striscia dei giorni con le scadenze, lunghezza variabile secondo la finestra scelta
- Finestre temporali: oggi, domani, settimana, mese, tutte
- Barra categorie verticale su desktop, orizzontale su mobile, con sottocategorie annidate
- Filtro per tipo: tutte, da fare, presidi
- Presidi con pulsante di rinvio al controllo successivo e contatore dei solleciti
- Chain di passi: ogni task può dipendere da altre (`deps`) e appartenere a un flusso (`flow`); le task bloccate restano fuori dalla lista e si contano nell'intestazione
- Dopo il completamento compaiono + (passo successivo) e × (chiudi la chain), anche in Archivio
- Archivio delle task completate, raggruppato per mese e con ricerca
- Cestino con ripristino; lo svuotamento è l'unica azione distruttiva
- Contatore delle task e dei sottotask completati oggi
- Tema automatico, chiaro o scuro; la preferenza resta per dispositivo
- Barra comandi in linguaggio naturale, inclusa la creazione esplicita di categorie
- Esportazione di `TASKS.md`

## Pubblicazione

L'artefatto si aggiorna pubblicando `index.html` sullo stesso link, che mantiene il
database. Pubblicare su un link nuovo crea un database vuoto.

Capability dichiarate: `db`, `sample`, `downloads`.

## Vincoli noti

- La pagina richiede una sessione claude.ai attiva: non funziona offline
- Le finestre di dialogo native del browser (`confirm`, `alert`) vengono ignorate
  dentro l'artefatto: le conferme sono a due clic dentro la pagina
- `TASKS.md` si aggiorna solo quando una chat dell'app desktop esegue la copia
- Il renderer del markdown è duplicato, in `index.html` e in `render_md.py`:
  ogni modifica al formato va fatta in entrambi, e i due output devono restare
  identici byte per byte

## Sviluppo

Il file è autoconsistente e si apre anche da disco, ma senza `window.claude` la
pagina mostra solo un avviso. Per provarla in locale servono dei mock delle API
`db`, `sample` e `downloads`.

Prima di pubblicare conviene verificare:

1. sintassi JavaScript del blocco inline
2. parità del markdown tra pagina e `render_md.py` su un'istantanea reale
3. resa su desktop e mobile, in tema chiaro e scuro
