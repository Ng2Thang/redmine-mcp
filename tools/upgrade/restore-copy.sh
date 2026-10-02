#!/bin/sh
set -eu
umask 077

# This image sees only the copied snapshot and the isolated target volumes.
snapshot=/snapshot
files=/redmine-files
expected=redmine-mcp-synthetic-v1

for name in COMPLETE database.dump attachments.tar.gz environment.json manifest.json \
  credentials.json versions.txt; do
  test -f "$snapshot/$name" && test ! -L "$snapshot/$name" || {
    echo 'Incomplete or unsafe isolated snapshot' >&2
    exit 1
  }
done
grep -Fq "$expected" "$snapshot/environment.json" || {
  echo 'Snapshot is not marked synthetic' >&2
  exit 1
}
grep -Fqx 'redmine=6.0.5-bookworm' "$snapshot/versions.txt"
grep -Fqx 'postgres=16.8-bookworm' "$snapshot/versions.txt"

pg_restore --list "$snapshot/database.dump" >/dev/null
tar -tzf "$snapshot/attachments.tar.gz" >/dev/null
tar -tzf "$snapshot/attachments.tar.gz" | while IFS= read -r entry; do
  case "$entry" in
    .|./|./*) ;;
    *) echo 'Unsafe attachment archive path' >&2; exit 1 ;;
  esac
  case "/$entry/" in
    */../*|*/./../*|*//*) echo 'Unsafe attachment archive path' >&2; exit 1 ;;
  esac
done
tar -tvzf "$snapshot/attachments.tar.gz" | while IFS= read -r listing; do
  case "$listing" in
    -*) ;;
    d*) ;;
    *) echo 'Unsafe attachment archive entry type' >&2; exit 1 ;;
  esac
done

table_count="$(psql -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
test "$table_count" = 0 || {
  echo 'Isolated database is not empty' >&2
  exit 1
}
test -z "$(find "$files" -mindepth 1 -print -quit)" || {
  echo 'Isolated attachment volume is not empty' >&2
  exit 1
}

pg_restore --clean --if-exists --no-owner --no-acl --exit-on-error --single-transaction \
  --dbname="$PGDATABASE" "$snapshot/database.dump"
test "$(psql -At -c "SELECT value FROM settings WHERE name='app_title'")" = \
  'Redmine MCP Synthetic Test' || {
  echo 'Restored database marker mismatch; leave candidate stopped' >&2
  exit 1
}
tar --no-same-owner --no-same-permissions -xzf "$snapshot/attachments.tar.gz" -C "$files"
echo 'Isolated copy restored. Target migration and acceptance remain pending.'
