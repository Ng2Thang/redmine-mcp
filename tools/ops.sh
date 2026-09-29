#!/bin/sh
set -eu
umask 077
expected=redmine-mcp-synthetic-v1
test -f /state/environment.json
grep -q "$expected" /state/environment.json || { echo 'Wrong environment'; exit 1; }
test "$(psql -Atc "SELECT value FROM settings WHERE name='app_title'")" = "Redmine MCP Synthetic Test" || {
  echo 'Database is not the marked synthetic instance'; exit 1;
}
case "${SNAPSHOT_ID:-}" in
  ''|*[!a-zA-Z0-9_-]*) echo 'Invalid snapshot ID'; exit 1 ;;
esac
snapshot="/state/backups/$SNAPSHOT_ID"
case "${1:-}" in
  backup)
    test ! -e "$snapshot" || { echo 'Snapshot already exists'; exit 1; }
    mkdir -p "$snapshot"
    pg_dump --format=custom --file="$snapshot/database.dump"
    tar -czf "$snapshot/attachments.tar.gz" -C /redmine-files .
    cp /state/environment.json /state/manifest.json /state/credentials.json "$snapshot/"
    printf '%s\n' 'redmine=6.0.5-bookworm' 'postgres=16.8-bookworm' > "$snapshot/versions.txt"
    touch "$snapshot/COMPLETE"
    echo 'Backup complete; contains test credentials. Keep outside version control.'
    ;;
  restore)
    test -f "$snapshot/COMPLETE" || { echo 'Snapshot incomplete'; exit 1; }
    grep -qx 'redmine=6.0.5-bookworm' "$snapshot/versions.txt"
    grep -qx 'postgres=16.8-bookworm' "$snapshot/versions.txt"
    grep -q "$expected" "$snapshot/environment.json"
    pg_restore --list "$snapshot/database.dump" >/dev/null
    tar -tzf "$snapshot/attachments.tar.gz" >/dev/null
    pg_restore --clean --if-exists --no-owner --exit-on-error --single-transaction \
      --dbname="$PGDATABASE" "$snapshot/database.dump"
    # Only the fixed attachment mount is cleared; never a user-provided path.
    find /redmine-files -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
    tar -xzf "$snapshot/attachments.tar.gz" -C /redmine-files
    cp "$snapshot/environment.json" "$snapshot/manifest.json" "$snapshot/credentials.json" /state/
    echo 'Restore commands completed; full restore validation remains deferred.'
    ;;
  *) echo 'Use backup or restore'; exit 1 ;;
esac

