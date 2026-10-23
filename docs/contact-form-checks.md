# Contact form verification — 23 October 2026

## Scope and evidence

- Starting revision: `7955090` on `main`; PR #2 was already merged and no open PR overlapped this work.
- Production form: `https://hmimar.com/#iletisim`, endpoint `https://formspree.io/f/mbdwlwgd`.
- The existing layout, CSS, images, content, translations and endpoint are unchanged. Contact-form behavior in `site.js` changes; development-only test files are added. The homepage script URL is versioned so a recently cached script does not keep the old handler after deployment.

## Production desktop checks before the fix

Chrome viewport: 1363 × 936 CSS pixels.

| Check | Observed result |
| --- | --- |
| Empty form | Native validation blocked submission and focused the name field. |
| Invalid email | Native validation blocked submission and focused the email field. |
| Consent unchecked | Native validation blocked submission and focused the checkbox. |
| Whitespace-only name/message | Both fields reported valid. No whitespace-only test was sent to production. Fixed below. |
| One valid, clearly labelled test | Loading message appeared and submit button was disabled. Success feedback appeared, form reset, button re-enabled. |
| Real email delivery | The exact unique test marker and full test body were found in the connected recipient Gmail inbox, received 23 October 2026 at 21:36:37 Europe/Istanbul. |

The successful production UI followed `response.ok`, so it establishes an HTTP 2xx outcome. The precise numerical HTTP code was not captured. Inbox delivery was verified separately by reading the matching received email; it was **not inferred from HTTP success**. This verifies this one submission, not every future delivery. The separate `info@hmimar.com` Gmail connection reported `mail_service_not_enabled`; delivery to that particular mailbox could not be checked.

## Fixes

- Reject whitespace-only required name/message and retain native email/consent validation. Telephone and project type remain optional.
- Prevent concurrent submissions and lock fields while a request is pending, so a successful reset cannot erase edits made during submission. Serialize all values before disabling controls.
- Abort a stalled request after 15 seconds; restore controls and preserve input after failure.
- Distinguish HTTP rejection from an uncertain network/timeout result. An interrupted response can follow server acceptance, so there is no automatic retry.
- Replace inbox-delivery wording with submission wording. Only mailbox evidence can establish email delivery.
- Support TR/EN/AR feedback, including language changes during a request. Clear stale feedback when the user edits or makes an invalid new attempt.

## Repeatable local checks

```sh
npm ci --ignore-scripts
npm test
node --check site.js
git diff --check
```

The suite uses the actual `index.html`, `site.js` and (for language switching) `i18n.js` in jsdom, with intercepted requests and controlled timers. It loads no external resources and sends no email.

13 tests passed: required fields/email/consent; whitespace rejection/recovery; optional fields and consent serialization; successful payload/reset and concurrent-submission protection; HTTP 400/422/429/500 with data retention and manual retry; network rejection; 15-second timeout; TR/EN/AR switching; stale feedback clearing; initialization on pages without the form.

Four focused regression checks (whitespace, uncertain network result, stalled request, language switching) fail against the original `site.js` and pass with this change.

## Limits / remaining checks

- jsdom tests verify DOM behavior, not visual layout or a real mobile browser.
- The available cloud browser exposes no viewport/device-emulation control and cannot reach the local test server. A mobile-sized preview could not be opened because its URL protocol was blocked. No workaround was used.
- Mobile CSS inspection confirms the existing single-column form rule at the small-screen breakpoint. This is **not a completed mobile-device test**. Android Chrome / iOS Safari keyboard, viewport, touch, native validation and one controlled submission remain to be checked on actual devices or an authorized mobile testing surface.
- HTTP errors, network failures and timeout behavior were simulated locally, not induced against the production Formspree service. No load test or repeated production failure requests were made.
- Post-deployment verification is tracked in the pull requests. PR #3 deployed successfully; the production `/site.js` response matched the tested file byte for byte (SHA-256 `02e1025da07d1a44103e12b1b94b7d0ec282cf86c668b3b7e5030005cdebe6b4`). Its `max-age=600` cache header and the old behavior in the existing browser session prompted the homepage script URL version. The desktop evidence above was collected before the fix.
