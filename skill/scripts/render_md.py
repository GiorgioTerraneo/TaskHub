#!/usr/bin/env python3
"""Render the Task Hub database into TASKS.md.

Usage: python3 render_md.py <db_dir> [out_file]
<db_dir> is the out_dir used with Artifact read_db: it must contain
config/main.json and tasks/<id>.json. Prints to stdout if no out_file.
The output format must stay identical to renderMarkdown() in the Task Hub page.
"""
import json, sys, glob, os, datetime

def flow_label(cfg, f):
    return ((cfg.get("flows") or {}).get(f) or {}).get("label") or "Flusso"

def flow_steps(tasks, f):
    steps = [t for t in tasks if t.get("flow") == f and t.get("status") != "deleted"]
    return sorted(steps, key=lambda t: (str(t.get("created_at") or ""), str(t.get("id") or "")))

def blockers(tasks, t):
    by = {x.get("id"): x for x in tasks}
    out = []
    for d in t.get("deps") or []:
        x = by.get(d)
        if x and x.get("status") not in ("done", "deleted"):
            out.append(x)
    return out

def load(db_dir):
    cfg = json.load(open(os.path.join(db_dir, "config", "main.json"), encoding="utf-8"))
    tasks = []
    for f in sorted(glob.glob(os.path.join(db_dir, "tasks", "*.json"))):
        t = json.load(open(f, encoding="utf-8"))
        t["id"] = os.path.splitext(os.path.basename(f))[0]
        tasks.append(t)
    return cfg, tasks

def key(t):
    return (t.get("deadline") or "9999-99-99", {"H": 0, "M": 1, "L": 2}.get(t.get("priority"), 3), str(t.get("title", "")).lower())

def task_lines(t, cfg=None, tasks=None):
    cfg = cfg or {}
    tasks = tasks or []
    dl = t.get("deadline") or "ongoing"
    sfx = ""
    if t.get("kind") == "check":
        try:
            nch = int(t.get("checks") or 0)
        except (TypeError, ValueError):
            nch = 0
        sfx = " | presidio"
        if t.get("waiting_on"):
            sfx += " (attesa: %s)" % t["waiting_on"]
        if t.get("recheck_days"):
            sfx += " ogni %sg" % t["recheck_days"]
        if nch:
            sfx += ", %d\u00b0 controllo" % nch
    fx = ""
    if t.get("flow"):
        steps = flow_steps(tasks, t["flow"])
        ids = [s.get("id") for s in steps]
        pos = ids.index(t.get("id")) + 1 if t.get("id") in ids else 0
        fx = " | flusso: %s" % flow_label(cfg, t["flow"])
        if pos:
            fx += " (%d/%d)" % (pos, len(steps))
    bl = blockers(tasks, t)
    bx = " | bloccata da: %s" % ", ".join(b["title"] for b in bl) if bl else ""
    out = ["- [ ] **%s** | %s | %s%s%s%s" % (t["title"], t.get("priority", "M"), dl, sfx, fx, bx)]
    for s in t.get("subtasks") or []:
        out.append("  - [%s] %s" % ("x" if s.get("done") else " ", s.get("text", "")))
    if (t.get("notes") or "").strip():
        out.append("  - Note: %s" % t["notes"].strip())
    return out

def render(cfg, tasks, today=None):
    today = today or datetime.date.today().isoformat()
    L = ["# TASKS — Giorgio Terraneo", "", f"**Last updated:** {today}  ",
         "**Source of truth:** Task Hub (claude.ai). Questo file è una copia in sola lettura: le modifiche fatte qui vengono sovrascritte.",
         "", "---", ""]
    open_t = [t for t in tasks if t.get("status") not in ("done", "deleted")]
    done_t = [t for t in tasks if t.get("status") == "done"]
    cats = sorted(cfg["categories"], key=lambda c: c.get("order", 99))
    known = {c["id"] for c in cats}
    for i, c in enumerate(cats, 1):
        L += [f"## {i}. {c['label']}", ""]
        ct = [t for t in open_t if t.get("category") == c["id"]]
        for t in sorted([t for t in ct if not t.get("subcategory")], key=key):
            L += task_lines(t, cfg, tasks) + [""]
        subs = list(c.get("subcategories") or [])
        subs += sorted({t["subcategory"] for t in ct if t.get("subcategory") and t["subcategory"] not in subs})
        for s in subs:
            st = sorted([t for t in ct if t.get("subcategory") == s], key=key)
            L += [f"### {s}", ""]
            for t in st:
                L += task_lines(t, cfg, tasks) + [""]
        L += ["---", ""]
    orphans = [t for t in open_t if t.get("category") not in known]
    if orphans:
        L += ["## Senza categoria", ""]
        for t in sorted(orphans, key=key):
            L += task_lines(t, cfg, tasks) + [""]
        L += ["---", ""]
    L += ["## Archive / Completed", ""]
    for t in sorted(done_t, key=lambda t: t.get("done_at") or "", reverse=True):
        d = (t.get("done_at") or "")[:10]
        subs = t.get("subtasks") or []
        tail = " | %d/%d sottotask" % (len([x for x in subs if x.get("done")]), len(subs)) if subs else ""
        L.append("- [x] **%s** | %s | completata %s%s" % (t["title"], t.get("priority", "M"), d, tail))
    if not done_t:
        L.append("*(nessuna task completata)*")
    return "\n".join(L).rstrip() + "\n"

if __name__ == "__main__":
    cfg, tasks = load(sys.argv[1])
    md = render(cfg, tasks)
    if len(sys.argv) > 2:
        open(sys.argv[2], "w", encoding="utf-8").write(md)
    else:
        sys.stdout.write(md)
