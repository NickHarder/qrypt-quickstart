#!/bin/sh
# Starts one agent run in the harness's container, as the image's user without root.
#
# When the harness mounts its certificate authority (the mock run: api-eus.qrypt.com is mapped to
# the mock on the host), every client an agent might use trusts it beside the real authorities:
# OpenSSL through Python's ssl (SSL_CERT_FILE), requests (REQUESTS_CA_BUNDLE), curl
# (CURL_CA_BUNDLE) and Node.js (NODE_EXTRA_CA_CERTS). pip keeps its own bundle, so package installs
# from PyPI are unchanged.
#
# Behind an egress proxy that inspects TLS (a cloud session), the harness also mounts the proxy's
# authority as /harness/extra-ca.pem. It joins the same bundle, and pip is pointed at the bundle
# too (PIP_CERT), since every request then leaves through the proxy.
set -eu

extra_authorities=""
for authority in /harness/ca.pem /harness/extra-ca.pem; do
  if [ -f "$authority" ]; then extra_authorities="$extra_authorities $authority"; fi
done
if [ -n "$extra_authorities" ]; then
  combined_bundle="$HOME/trusted-authorities.pem"
  node_authorities="$HOME/extra-authorities.pem"
  # The list of files is meant to split into separate arguments.
  # shellcheck disable=SC2086
  cat /etc/ssl/certs/ca-certificates.crt $extra_authorities > "$combined_bundle"
  # shellcheck disable=SC2086
  cat $extra_authorities > "$node_authorities"
  export SSL_CERT_FILE="$combined_bundle"
  export REQUESTS_CA_BUNDLE="$combined_bundle"
  export CURL_CA_BUNDLE="$combined_bundle"
  export NODE_EXTRA_CA_CERTS="$node_authorities"
  if [ -f /harness/extra-ca.pem ]; then
    export PIP_CERT="$combined_bundle"
  fi
fi

exec "$@"
