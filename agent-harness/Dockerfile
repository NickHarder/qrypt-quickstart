# The agent-readiness test's fresh environment (docs/PLAN.md, Phase 8): one new container per run,
# holding only the project folder, with Claude Code, Python 3 and Node.js, as a new developer's
# machine would. Build: docker build -t qrypt-agent-harness agent-harness/
FROM node:22.22.0-bookworm-slim

RUN apt-get update \
 && apt-get install --yes --no-install-recommends python3 python3-pip python3-venv ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# The agent under test, pinned so both rounds run the same version. Behind a TLS-inspecting proxy,
# give its authority as a build secret (docker build --secret id=extra_ca,src=<file>); without one,
# npm trusts only the public authorities.
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -f /run/secrets/extra_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/extra_ca; fi \
 && npm install --global @anthropic-ai/claude-code@2.1.304

COPY entrypoint.sh /usr/local/bin/harness-entrypoint
RUN chmod 755 /usr/local/bin/harness-entrypoint \
 && useradd --create-home agent

# The agent runs without root; the harness opens the throwaway project folder to this user.
USER agent
WORKDIR /project
ENTRYPOINT ["/usr/local/bin/harness-entrypoint"]
