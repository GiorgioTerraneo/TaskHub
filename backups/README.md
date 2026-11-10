# Backup del database

Copie JSON dello stato del Task Hub (`config/main` + tutte le task).
Si creano da una chat Claude con la skill `task-manager`:

1. `read_db` list di `tasks` (limit 1000) e get di `config/main` in una cartella temporanea
2. unione in un unico file `db-backup-YYYY-MM-DD.json`

Il database vive su claude.ai e non è versionato da Git: questi file sono
istantanee, utili per ricostruire lo stato se una migrazione va storta.
