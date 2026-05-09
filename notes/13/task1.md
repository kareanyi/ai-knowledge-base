## daemon status shortcut

```shell
root@VM-0-3-ubuntu:~# openclaw daemon status

🦞 OpenClaw 2026.4.21 (f788c88) — I can run local, remote, or purely on vibes—results may vary with DNS.

│
◇  
Service: systemd (enabled)
File logs: /tmp/openclaw/openclaw-2026-05-09.log
Command: /root/.nvm/versions/node/v22.22.2/bin/node /root/.local/share/pnpm/global/5/.pnpm/openclaw@2026.4.21_@napi-rs+canvas@0.1.99/node_modules/openclaw/dist/index.js gateway --port 22334
Service file: ~/.config/systemd/user/openclaw-gateway.service
Service env: OPENCLAW_GATEWAY_PORT=22334

Service config looks out of date or non-standard.
Service config issue: Gateway service PATH includes version managers or package managers; recommend a minimal PATH. (/root/.nvm/versions/node/v22.22.2/bin)
Service config issue: Gateway service uses Node from a version manager; it can break after upgrades. (/root/.nvm/versions/node/v22.22.2/bin/node)
Service config issue: System Node 22 LTS (22.14+) or Node 24 not found; install it before migrating away from version managers.
Recommendation: run "openclaw doctor" (or "openclaw doctor --repair").
Config (cli): ~/.openclaw/openclaw.json
Config (service): ~/.openclaw/openclaw.json
```