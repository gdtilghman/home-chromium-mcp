# Security notes

This project intentionally combines a logged-in browser, a remote GUI, an automation endpoint, and Chrome DevTools Protocol access. Those features are useful precisely because they are powerful. Deploy it only on a trusted private network.

## Non-negotiable exposure rules

- Do **not** port-forward ports `9222`, `13000`, `13001`, or `18000` from a router.
- Do **not** publish CDP port `9222` in Docker Compose.
- Do **not** disable the Chromium GUI username and password.
- Do **not** reuse the GUI password or MCP token anywhere else.
- Do **not** commit a completed `.env`, `docker-compose.yml`, browser profile, or storage-state JSON file.
- Reach the NAS from outside the home only through an authenticated private network such as Tailscale or WireGuard, or through a separately secured reverse proxy that you understand.

## What each access path controls

### Chromium GUI credentials

The LinuxServer web interface streams the browser desktop. LinuxServer's environment can also provide a terminal with passwordless sudo inside the container. Treat GUI access as administrative access to the browser container.

### MCP bearer token

The token authorizes an agent or another MCP client to use the Scrapling browser service. Anyone with the token and network access should be treated as able to use the browser sessions made available through that service.

### CDP

Chrome DevTools Protocol can inspect pages, execute JavaScript, navigate tabs, access browser state, and interact with logged-in sites. In this design it is limited to loopback inside a shared Docker network namespace. Preserving that boundary is essential.

### Chromium profile

The persistent `/config` volume contains the browser profile, including cookies and site data. Possession of a copied profile may provide access to active website sessions.

### Playwright storage-state files

A storage-state JSON file can contain reusable session cookies and local-storage data. Treat it like a temporary password. Store it only in the intended `/data` volume or an encrypted backup.

## Dedicated profile recommendation

Use a browser profile dedicated to this project. `extract_state.py` exports the default browser context, which can include cookies and origins for every site signed into that profile. Do not add unrelated high-value accounts to the profile without understanding that a state export includes the context as a whole.

## Safer port binding

The example publishes ports using Docker's normal host bindings. Protect them with the host firewall and the private-network design.

Where all clients connect through one known private address, consider binding the GUI and MCP ports to that address instead:

```yaml
ports:
  - "<NAS_PRIVATE_IP>:13001:3001"
  - "<NAS_PRIVATE_IP>:18000:8000"
```

Do not bind a headless NAS GUI only to `127.0.0.1` unless you also provide a tunnel or another deliberate access path.

## Checking a repository before publishing it

Before making a repository or Gist public, inspect every file for:

- Real GUI usernames or passwords
- MCP tokens
- Private IP addresses or hostnames you do not want public
- Tailscale node names or addresses
- Website account names
- Complete URLs containing account or family-site identifiers
- Cookies, browser-state JSON, screenshots showing account data, and profile files

Remember that deleting a secret from the latest commit does not remove it from Git history or from copies already made of a public Gist.

## Rotation and revocation

### Stop everything

```bash
docker compose down
```

### Rotate the MCP token

1. Generate a new token.
2. Update `.env`.
3. Recreate the `home-browser` service.
4. Update the agent's MCP client configuration.

### Change the GUI password

1. Update `CHROMIUM_GUI_PASSWORD` in `.env`.
2. Recreate the Chromium service.
3. Restart `home-browser` after Chromium.

### End one website session

Sign out on the website in the visible Chromium browser, delete the corresponding state file from `browser-data/`, and use the website's own session-management page to revoke the session if it provides one.

### Remove all local browser sessions

Stop the project and delete the dedicated Chromium profile and state files. Expect every website in that profile to require a fresh login afterward.

### Remove deployment access

If a separate SSH or NAS account was created to install or maintain this project, disable or delete it when that access is no longer wanted. Rotating Docker credentials does not revoke host-level maintenance access.

## Reporting problems in public

When asking for help publicly, share image names, sanitized Compose structure, and relevant log lines. Remove tokens, passwords, private addresses, account names, complete account URLs, cookies, and state-file contents first.

Do not paste the output of `docker compose config` publicly; it can contain expanded secret values.
