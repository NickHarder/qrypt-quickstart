#!/bin/sh
# Starts one agent run in the harness's container.
#
# When the harness mounts its certificate authority (the mock run: api-eus.qrypt.com is mapped to
# the mock on the host), the container trusts it for every client an agent might use: the system
# store (Python's ssl, curl), requests (REQUESTS_CA_BUNDLE) and Node.js (NODE_EXTRA_CA_CERTS). Real
# certificates stay trusted, so package installs still work. Then the agent runs as a user without
# root, in the project folder.
set -eu

if [ -f /harness/ca.pem ]; then
  cp /harness/ca.pem /usr/local/share/ca-certificates/qrypt-agent-harness.crt
  update-ca-certificates >/dev/null
  export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
  export NODE_EXTRA_CA_CERTS=/harness/ca.pem
fi

chown -R agent /project
exec env HOME=/home/agent runuser -u agent -- "$@"
