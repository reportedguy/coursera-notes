# Security policy

## Reporting a vulnerability
Please **don't open a public issue**. Report it privately through [GitHub security advisories](https://github.com/reportedguy/coursera-notes/security/advisories/new). You'll get a reply within a few days.

## In scope
Report anything that could:
- leak the Coursera session (cookies, the browser profile) or any credential
- make the tool send a request that changes something on Coursera (submit, enroll, start an attempt), getting past the read-only guard
- get past the pacing or the stop rules (429, 403, captcha, login)
- send course data or notebook content anywhere other than the user's own machine and their own AI agent
- run code from fetched course content or from a notebook file

## Out of scope
- Coursera's own services. Report those to Coursera.
- The terms-of-use risk of automated access, which the README describes.
