#!/bin/sh
set -eu
case "${ADMIN_API_KEY:-}" in
  *[!A-Za-z0-9_-]*|'') echo "ADMIN_API_KEY must be a 32-128 character URL-safe random value" >&2; exit 1 ;;
esac
[ "${#ADMIN_API_KEY}" -ge 32 ] && [ "${#ADMIN_API_KEY}" -le 128 ] || exit 1
[ -s /run/secrets/admin_htpasswd ] || { echo "admin_htpasswd is required" >&2; exit 1; }
