#!/bin/sh
set -e

: "${PORT:=80}"
: "${BACKEND_URL:?BACKEND_URL must be set to the backend's base URL, e.g. https://signbridge-backend.onrender.com}"

case "$BACKEND_URL" in
  http://*|https://*) ;;
  *) BACKEND_URL="https://$BACKEND_URL" ;;
esac

# Strip any trailing slash(es) -- the template appends its own "/api/", so a
# trailing slash here would produce "...//api/..." and 404 at the backend.
# (POSIX parameter expansion only -- no extglob -- since this runs under
# Alpine's /bin/sh, not bash.)
while [ "${BACKEND_URL%/}" != "$BACKEND_URL" ]; do
  BACKEND_URL="${BACKEND_URL%/}"
done

envsubst '$PORT $BACKEND_URL' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
