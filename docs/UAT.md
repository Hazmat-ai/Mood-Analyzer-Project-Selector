# User acceptance protocol

Execute on the exact HTTPS staging candidate. Record tester, date, OS/browser, viewport, commit or image digest, expected/actual result and evidence. These are human checks; do not mark them passed from a unit test run.

| ID | Scenario | Acceptance |
|---|---|---|
| U01 | First visit | Purpose and seven-question flow understood; no camera/microphone prompts; no external font calls |
| U02 | All specialties/difficulties | Five specialties and all difficulty paths produce a canonical project with steps; difficulty choice respected |
| U03 | Answer editing | Back retains prior answers; radio inputs support keyboard arrows; Next disabled until selected; focus reaches new question |
| U04 | Repeated clicks | Double click difficulty cannot create two picks; completion button visibly waits and reports errors |
| U05 | API/network failure | Failure keeps selections, provides recovery, and never presents an old result as a new match |
| U06 | Lost submit response | Server commits, response lost, user retries same choice; only one pick recorded |
| U07 | Cancel waiting | Late response cannot change current screen; any already committed pick is visible in history |
| U08 | Animation | Skip works; reduced motion bypasses roulette; leaving it cannot trigger a stale timer |
| U09 | History/privacy | Fresh browser profile sees none of another profile's picks; export scoped; reopening works; deletion/reset actually clears records |
| U10 | Sessions | Existing identity survives restart and expires after 30 days; no cross-device account/recovery promise; new quiz gets a fresh request intent |
| U11 | Content quality | Review all five categories, difficulty tags, useful details and honest outline labels; verify legal/safe educational scope and no fabricated starter links |
| U12 | Explainability | User understands the draw is weighted, not guaranteed closest; preference axes are self-reported heuristics |
| U13 | Accessibility | Keyboard-only full journey, visible focus, screen reader labels and announcements, 200% zoom, non-colour-only selection, native controls |
| U14 | Mobile | Current Safari/iOS, Chrome/Android and desktop Chrome/Firefox/Edge: 320px and 375px layouts, long titles and large text remain usable |
| U15 | Deployment | TLS, origin/Host enforcement, security headers, persistence across service restart, worker concurrency and acceptable latency under expected load |
| U16 | Operations | Full/read-only disk, backup restore, process termination, expired-data cleanup and rollback tested on staging |

Use `docs/release-signoff.json` only to reference completed evidence. Do not invent tester names, approval dates, penetration-test reports or launch certification. Browser automation supplements this protocol; it does not replace it.
