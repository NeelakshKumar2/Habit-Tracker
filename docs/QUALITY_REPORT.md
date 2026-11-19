# Quality report (raw output)

Generated 2026-11-19 on 1 CPU core, Python 3.12.3, Node v22.23.5.

## 1. Test suite
```
Ran 87 tests in 5.827s
OK

tests per file:
  tests/test_auth.py: 30
  tests/test_data.py: 28
  tests/test_frontend_e2e.py: 1
  tests/test_ops.py: 12
  tests/test_parity.py: 1
  tests/test_review.py: 6
  tests/test_scoring.py: 9
front-end end-to-end checks run in Node: 20/20 passed
```

## 2. Static checks
```
python compiles: ok
javascript files syntax-checked: 29
```

## 3. Line coverage of server/
```
file                        lines   hit   cover
server/__init__.py              1     1  100.0%
server/api.py                 123   119   96.7%   missed: [38, 39, 148, 149]
server/auth.py                254   247   97.2%   missed: [51, 63, 64, 66, 85, 279, 320]
server/avatar.py               33    32   97.0%   missed: [28]
server/config.py               63    61   96.8%   missed: [18, 19]
server/db.py                   52    49   94.2%   missed: [84, 85, 86]
server/errors.py               36    36  100.0%
server/mail.py                 29    25   86.2%   missed: [32, 33, 34, 35]
server/main.py                 69    68   98.6%   missed: [34]
server/review.py               41    40   97.6%   missed: [60]
server/scoring.py              91    91  100.0%
server/security.py             62    56   90.3%   missed: [34, 42, 43, 50, 51, 91]
server/validators.py           70    68   97.1%   missed: [46, 70]
TOTAL                         924   893   96.6%   (all tests passed: True)
```

## 4. Mutation testing (15 deliberate bugs)
```
KILLED    one person can read everyone's challenges          caught by test_people_cannot_see_or_touch_each_others_data
KILLED    CSRF header check removed                          caught by test_state_changing_requests_need_the_csrf_header
KILLED    delete account without the password                caught by test_delete_needs_the_password
KILLED    session tokens stored in plain text                caught by test_session_tokens_are_stored_only_as_hashes
KILLED    login brute-force throttle removed                 caught by test_five_failures_lock_that_client_then_throttle_returns_429
KILLED    password check always succeeds                     caught by test_delete_needs_the_password
KILLED    expired sessions accepted                          caught by test_expired_sessions_are_refused
KILLED    image size guard removed (decompression bomb)      caught by test process crashed (out of memory)
KILLED    deleted data left on disk (secure_delete off)      caught by test_delete_removes_every_trace_and_leaves_others_alone
KILLED    ticks may point outside the challenge              caught by test_ticks_and_notes_must_sit_inside_the_challenge
KILLED    password change keeps other sessions               caught by test_change_password_needs_current_one_and_revokes_other_sessions
KILLED    password reset keeps old sessions                  caught by test_reset_sets_password_ends_all_sessions_and_is_single_use
KILLED    CSP allows inline scripts                          caught by test_security_headers_everywhere
KILLED    browser stops escaping HTML                        caught by test_front_end_against_live_server
KILLED    browser score formula drifts from the server       caught by test_js_and_python_scores_match_on_400_random_datasets

15/15 mutants killed
```

## 5. Load test (4 server processes sharing one SQLite file, production password hashing)
```
cpu cores available : 1   server processes : 4   client threads : 16   virtual users : 120
one password hash   : 214 ms (scrypt N=2^15, r=8, p=3)
requests            : 1304 in 69.5s  ->  19 req/s
operation            n   p50 ms   p95 ms   max ms
avatar get          40       47       60       96
avatar upload       40      211      576      677
delete account      24     4009     4100     4113
login              120     3951     4092     4233
logout             120       44       92      155
register           120     3979     4105     4190
review             120       43       77      130
save challenge     360       45       84      169
score              120       40       65      136
state              240       45       73       96
unexpected errors   : 0  []
users in db         : 96 (expected 96)
challenges in db    : 288 (expected 288, none lost)
orphan rows         : 0 after 24 account deletions
sqlite integrity    : ok
RESULT              : PASS
```
