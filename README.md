# SimplifyNext: Supported next steps

A small, synthetic-data transition-planning MVP for parents, guardians and educators to use with young adults with disabilities. Start with the young adult's work goal, explore up to three catalog-backed next steps, resolve questions together, explicitly review, and download a Markdown plan. The participant's preferences stay in charge; a supporter does not make decisions on their behalf.

Private repository: [Xateh/simplifynext-mvp](https://github.com/Xateh/simplifynext-mvp), default branch `mvp`. Repository access must be granted separately to intended teammates; no collaborator invitations were sent and visibility was not made public.

## Readiness

**Interface refined; deployed API unchanged:** the 7 September UI pass adds Profile / Review / Download stages, linked field hints, narrow-screen styles, Edit profile, Start over, focus handoffs and visible expiry. Fresh checks pass 73 Python and 26 JavaScript tests, plus a real loopback API compatibility check. JavaScript event tests use a simulated DOM, not a rendered browser. Visual, keyboard and teammate-session acceptance remain open. See [verification evidence](docs/VERIFICATION.md).

On 6 September, the `5328bcb3...` package was verified `Active` / `Successful` on the existing IAM-authenticated endpoint. Broad and narrow synthetic requests each returned a Bedrock draft and passed exact-plan review/export and rejection guards: two model calls total, no repairs, retries or fallback. The planner supplies up to three constraint-filtered catalog records and permits at most two model calls per plan including one repair. These smoke cases do not establish general reliability. No AWS deployment, configuration change or model call occurred during the UI pass.

- Local offline workflow: implemented, including profile form, source cards, questions, review, export and trace.
- Bedrock workflow: the current broad goal and [narrow fictional request](examples/fictional-bedrock-request.json) passed once each. Both selected only the fictional office-skills taster. The broad result added a permitted but unnecessary provider-access question; narrow had no questions. Real-provider recommendation quality and repeatability remain unverified. Older results are preserved separately in the verification history.
- Shared AWS endpoint: deployed at `https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/` with `AWS_IAM`. Unsigned health returned 403; signed health returned 200, and signed resource listing returned 200 with eight records. Baseline offline create, review and export returned 200; unreviewed export returned 409 and a tampered envelope returned 400.
- Teammate access: **not yet verified from a teammate's own temporary organizer session**. Leader CloudShell verification does not prove every teammate has both required invoke permissions.
- Real participant use: **not approved**. Use invented profiles only. No clinical, employment-outcome or accessibility-conformance claim.

## Run the demo

Python 3.12 is the reference runtime. No dependencies or AWS credentials are needed for offline mode.

```powershell
python app.py
```

Open http://127.0.0.1:8765 on that computer. Select **Load fictional example**, **Explore next steps**, review the resource checks, select the review checkbox, **Confirm review**, then **Download reviewed plan**. Stop the server with Ctrl+C.

**Edit profile** retains your inputs but clears the displayed draft and approval. **Start over** clears the local profile and plan, restores offline mode and unchecks the synthetic-data declaration; already downloaded files remain. Expired plans stay readable, but review/download requires a fresh plan. Browser timeout or connection loss never triggers an automatic retry; an interrupted Bedrock request may still finish, and generating again may incur another charge.

If `python` is unavailable on Windows, install Python 3.12 or use `py -3.12 app.py` when the Python launcher is installed. Do not expose this development server to the internet or change its loopback binding.

## Connect to the shared AWS endpoint

Using the verified endpoint:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Authenticate with the organizer-provided temporary AWS role privately.
$env:AWS_PROFILE = 'YOUR_ORGANIZER_PROFILE'
$env:MVP_API_URL = 'https://54hpz6viwadtysmbdmj2i3gi5e0lcjoz.lambda-url.us-east-1.on.aws/'
.\.venv\Scripts\python.exe scripts\aws_client.py health
.\.venv\Scripts\python.exe app.py
```

On macOS/Linux the virtual-environment interpreter is `.venv/bin/python`; use your shell's environment-variable syntax. Every teammate runs their own loopback interface. The local server signs calls to the same AWS API using temporary credentials; credentials never enter browser code. A Function URL is internet-addressable but requires AWS IAM authorization—it is not a private-network endpoint. See [teammate AWS access](docs/TEAM-AWS.md).

For local direct Bedrock testing, leave `MVP_API_URL` unset, set `AWS_DEFAULT_REGION` and the explicitly approved `BEDROCK_MODEL_ID`, then choose Bedrock in the interface. Verify the organizer balance first. Offline is always labelled and is never substituted silently for a failed live call.

The committed Bedrock example and original broad goal have now passed on the current deployment after explicit approval and budget checks. This completes that two-case test authorization; no further paid calls are planned. Future live rehearsals require their own purpose, approval and fresh budget check. Do not rerun paid requests merely to reproduce evidence.

## Engineering references

- [Current team direction and scope boundaries](docs/DIRECTION-UPDATE.md)
- [API reference and examples](docs/API.md)
- [Teammate AWS access](docs/TEAM-AWS.md)
- [Deployment and rollback](docs/DEPLOYMENT.md)
- [Architecture and deliberate limitations](docs/ARCHITECTURE.md)
- [Research and existing tools](docs/RESEARCH.md)
- [Demo and readiness checklist](docs/READINESS.md)
- [Five-minute rehearsal script](docs/DEMO-SCRIPT.md)
- [Verification record](docs/VERIFICATION.md)

## Verify

Install `requirements.txt` for SDK/client tests, then:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --test tests/test_ui.cjs tests/test_ui_flow.cjs
.\.venv\Scripts\python.exe scripts\deploy.py --package
```

Node is needed only for interface-state, response and simulated interaction tests, not to run the app. HTTP tests start and stop an isolated loopback server. Tests make no live AWS requests. The deployment command defaults to package-only; it cannot deploy without explicit apply/account/region/model/budget arguments. Static UI assets are served locally and excluded from the Lambda package; this UI update needs no AWS redeployment.

No Telegram/email messages, applications, bookings or submissions are sent. No permanent AWS keys, raw private chats, personal records or private organizer links belong in this repository.
