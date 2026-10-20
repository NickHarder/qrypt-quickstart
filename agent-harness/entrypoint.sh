#!/bin/sh
# Starts one agent run in the harness's container, as the image's user without root.
#
# When the harness mounts its certificate authority (the mock run: api-eus.qrypt.com is mapped to
# the mock on the host), every client an agent might use trusts it beside the real authorities:
# OpenSSL through Python's ssl (SSL_CERT_FILE), requests (REQUESTS_CA_BUNDLE), curl
# (CURL_CA_BUNDLE) and Node.js (NODE_EXTRA_CA_CERTS). pip keeps its own bundle, so package installs
# from PyPI are unchanged.
set -eu

if [ -f /harness/ca.pem ]; then
  combined_bundle="$HOME/trusted-authorities.pem"
  cat /etc/ssl/certs/ca-certificates.crt /harness/ca.pem > "$combined_bundle"
  export SSL_CERT_FILE="$combined_bundle"
  export REQUESTS_CA_BUNDLE="$combined_bundle"
  export CURL_CA_BUNDLE="$combined_bundle"
  export NODE_EXTRA_CA_CERTS=/harness/ca.pem
fi

exec "$@"
