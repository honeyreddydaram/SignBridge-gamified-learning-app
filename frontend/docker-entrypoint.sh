#!/bin/sh
set -e

: "${PORT:=80}"
: "${BACKEND_URL:?BACKEND_URL must be set to the backend's base URL, e.g. https://signbridge-backend.onrender.com}"

case "$BACKEND_URL" in
  http://*|https://*) ;;
  *) BACKEND_URL="https://$BACKEND_URL" ;;
esac

envsubst '$PORT $BACKEND_URL' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
