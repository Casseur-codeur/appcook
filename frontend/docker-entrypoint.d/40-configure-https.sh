#!/bin/sh
set -eu

mode="$(printf '%s' "${APPCOOK_HTTPS_MODE:-auto}" | tr '[:upper:]' '[:lower:]')"
cert_path="${APPCOOK_TLS_CERT_PATH:-/etc/appcook/certs/fullchain.pem}"
key_path="${APPCOOK_TLS_KEY_PATH:-/etc/appcook/certs/privkey.pem}"
redirect_port="${APPCOOK_HTTPS_REDIRECT_PORT:-${APPCOOK_HTTPS_PORT:-443}}"

export APPCOOK_TLS_SERVER_NAME="${APPCOOK_TLS_SERVER_NAME:-_}"
export APPCOOK_TLS_CERT_PATH="$cert_path"
export APPCOOK_TLS_KEY_PATH="$key_path"

if [ "$redirect_port" = "443" ]; then
    export APPCOOK_HTTPS_REDIRECT_TARGET='https://$host$request_uri'
else
    export APPCOOK_HTTPS_REDIRECT_TARGET="https://\$host:${redirect_port}\$request_uri"
fi

has_tls_material() {
    [ -f "$cert_path" ] && [ -f "$key_path" ]
}

render_template() {
    template="$1"
    envsubst '${APPCOOK_TLS_SERVER_NAME} ${APPCOOK_TLS_CERT_PATH} ${APPCOOK_TLS_KEY_PATH} ${APPCOOK_HTTPS_REDIRECT_TARGET}' \
        < "$template" \
        > /etc/nginx/conf.d/default.conf
}

case "$mode" in
    auto)
        if has_tls_material; then
            render_template /etc/nginx/templates/nginx.https.conf.template
            echo "AppCook frontend: HTTPS enabled in auto mode." >&2
        else
            render_template /etc/nginx/templates/nginx.http.conf.template
            echo "AppCook frontend: TLS files not found, serving HTTP only in auto mode." >&2
        fi
        ;;
    redirect|enforce|https-only|on)
        if ! has_tls_material; then
            echo "AppCook frontend: APPCOOK_HTTPS_MODE=${mode} requires TLS files at ${cert_path} and ${key_path}." >&2
            exit 1
        fi
        render_template /etc/nginx/templates/nginx.https.conf.template
        echo "AppCook frontend: HTTPS enforced." >&2
        ;;
    off|http-only|disabled)
        render_template /etc/nginx/templates/nginx.http.conf.template
        echo "AppCook frontend: HTTPS disabled, serving HTTP only." >&2
        ;;
    *)
        echo "AppCook frontend: unsupported APPCOOK_HTTPS_MODE '${mode}'." >&2
        exit 1
        ;;
esac
