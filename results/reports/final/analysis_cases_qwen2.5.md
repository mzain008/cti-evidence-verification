## Correct (agent right, ReAct wrong)

**final-beni-benign_claim-006** (benign_claim) — Verify the following claim against authoritative security sources: "MITRE ATT&CK mitigation M1026 (Privileged Account Management) mitigates technique T1688 (Safe Mode Boot)." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: SUPPORTED
- Evidence-Aware Agent (C): ids=['T1688', 'M1026'] verdict=SUPPORTED flags=[]
- ReAct agent (A): ids=[] verdict=UNSUPPORTED flags=['OUTDATED']
- Non-agentic graph verifier (B): ids=['T1688', 'M1026'] verdict=SUPPORTED flags=[]

**final-outd-revoked-005** (revoked) — Which MITRE ATT&CK mitigations (M-IDs) should be applied against technique T1109 (Component Firmware)?

- Gold: M1051; outdated: T1109
- Evidence-Aware Agent (C): ids=['M1051'] verdict=None flags=['OUTDATED', 'REVOKED']
- ReAct agent (A): ids=['M1046'] verdict=None flags=['OUTDATED']
- Non-agentic graph verifier (B): ids=['M1051'] verdict=None flags=['OUTDATED', 'REVOKED']

**final-rela-claim_has_weakness-006** (claim_has_weakness) — Verify the following claim against authoritative security sources: "CVE-2017-12231 is caused by weakness CWE-399 (Resource Management Errors)." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: SUPPORTED
- Evidence-Aware Agent (C): ids=['CWE-399', 'CVE-2017-12231'] verdict=SUPPORTED flags=[]
- ReAct agent (A): ids=['CWE-399', 'CVE-2017-12231'] verdict=UNSUPPORTED flags=[]
- Non-agentic graph verifier (B): ids=[] verdict=SUPPORTED flags=['CONFLICT'] | conflicts: equal_authority:  ['CVE-2009-4324', 'CVE-2012-2539', 'CVE-2013-3893', 'CVE-2013-3897', 'CVE-2014-0496', 'CVE-2014-0502', 'CVE-2015-1641', 'CVE-2017-12231', 'CVE-2017-12232', 'CVE-2017-12237', 'CVE-2017-12238', 'CVE-2017-6627', 'CVE-2018-0154', 'CVE-2018-0156', 'CVE-2018-0161', 'CVE-2018-0179', 'CVE-2018-0180']

## Incorrect (agent wrong)

**final-outd-withdrawn-006** (withdrawn) — A legacy compliance baseline still lists NIST SP 800-53 control RA-5(7). Is this control current in Rev. 5? If it is not, which control(s) should be assessed instead?

- Gold: CM-8; outdated: RA-5(7)
- Evidence-Aware Agent (C): ids=[] verdict=None flags=['INSUFFICIENT_EVIDENCE', 'WITHDRAWN'] | rejected=[['CM-8(6)', 'no acceptable evidence path'], ['CA-9(1)', 'no acceptable evidence path']]
- ReAct agent (A): ids=['CM-8(6)'] verdict=SUPPORTED flags=['WITHDRAWN']
- Non-agentic graph verifier (B): ids=[] verdict=None flags=['INSUFFICIENT_EVIDENCE', 'WITHDRAWN'] | rejected=[['CM-8(6)', 'no acceptable evidence path'], ['CA-9(1)', 'no acceptable evidence path']]

**final-rela-cve_capec-000** (cve_capec) — Which CAPEC attack patterns are related to the weakness(es) recorded for CVE-2004-1464? Return the CAPEC IDs.

- Gold: CAPEC-147, CAPEC-227, CAPEC-492
- Evidence-Aware Agent (C): ids=[] verdict=None flags=['INSUFFICIENT_EVIDENCE'] | rejected=[['CAPEC-54', 'no acceptable evidence path'], ['CAPEC-680', 'no acceptable evidence path']]
- ReAct agent (A): ids=['CAPEC-54', 'CAPEC-680'] verdict=None flags=[]
- Non-agentic graph verifier (B): ids=[] verdict=None flags=['INSUFFICIENT_EVIDENCE'] | rejected=[['CAPEC-54', 'no acceptable evidence path'], ['CAPEC-680', 'no acceptable evidence path']]

**final-rela-cve_capec-001** (cve_capec) — Which CAPEC attack patterns are related to the weakness(es) recorded for CVE-2021-26086? Return the CAPEC IDs.

- Gold: CAPEC-126, CAPEC-64, CAPEC-76, CAPEC-78, CAPEC-79
- Evidence-Aware Agent (C): ids=[] verdict=None flags=['INSUFFICIENT_EVIDENCE'] | rejected=[['CAPEC-240', 'no acceptable evidence path'], ['CAPEC-132', 'no acceptable evidence path']]
- ReAct agent (A): ids=['CAPEC-240', 'CAPEC-132'] verdict=None flags=[]
- Non-agentic graph verifier (B): ids=[] verdict=None flags=['INSUFFICIENT_EVIDENCE'] | rejected=[['CAPEC-240', 'no acceptable evidence path'], ['CAPEC-132', 'no acceptable evidence path']]

## Contradictory evidence

**final-conf-injected_claim-000** (injected_claim) — Verify the following claim against authoritative security sources: "MITRE ATT&CK mitigation M1026 (Privileged Account Management) mitigates technique T1211 (Exploitation for Stealth)." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: UNSUPPORTED; injected: M1026
- Evidence-Aware Agent (C): ids=['T1211', 'M1026'] verdict=UNSUPPORTED flags=['CONFLICT'] | conflicts: lower_authority: OSINT Digest ['M1026']
- ReAct agent (A): ids=['T1211', 'M1026'] verdict=UNSUPPORTED flags=['OUTDATED']
- Non-agentic graph verifier (B): ids=['T1211', 'M1026'] verdict=UNSUPPORTED flags=['CONFLICT'] | conflicts: lower_authority: OSINT Digest ['M1026']

**final-conf-injected_claim-001** (injected_claim) — Verify the following claim against authoritative security sources: "MITRE ATT&CK mitigation M1022 (Restrict File and Directory Permissions) mitigates technique T1003.002 (Security Account Manager)." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: UNSUPPORTED; injected: M1022
- Evidence-Aware Agent (C): ids=['T1003.002', 'M1022'] verdict=UNSUPPORTED flags=['CONFLICT'] | conflicts: lower_authority: Analyst Notebook ['M1022']
- ReAct agent (A): ids=['T1003.002', 'M1022'] verdict=UNSUPPORTED flags=['OUTDATED']
- Non-agentic graph verifier (B): ids=[] verdict=UNSUPPORTED flags=['CONFLICT'] | conflicts: lower_authority: Analyst Notebook ['M1022']

**final-conf-injected_claim-002** (injected_claim) — Verify the following claim against authoritative security sources: "MITRE ATT&CK mitigation M1017 (User Training) mitigates technique T1690 (Prevent Command History Logging)." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: UNSUPPORTED; injected: M1017
- Evidence-Aware Agent (C): ids=[] verdict=UNSUPPORTED flags=['CONFLICT'] | conflicts: lower_authority: Threat Exchange Post ['M1017']
- ReAct agent (A): ids=[] verdict=UNSUPPORTED flags=['OUTDATED']
- Non-agentic graph verifier (B): ids=['T1690', 'M1017'] verdict=UNSUPPORTED flags=['CONFLICT'] | conflicts: lower_authority: Threat Exchange Post ['M1017']

## Unanswerable

**final-insu-claim_nei-000** (claim_nei) — Verify the following claim against authoritative security sources: "MITRE ATT&CK mitigation M1026 (Privileged Account Management) mitigates technique T1829." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: NOT_ENOUGH_INFO
- Evidence-Aware Agent (C): ids=['T1829', 'M1026'] verdict=NOT_ENOUGH_INFO flags=['OUTDATED']
- ReAct agent (A): ids=[] verdict=UNSUPPORTED flags=['INSUFFICIENT_EVIDENCE', 'OUTDATED']
- Non-agentic graph verifier (B): ids=['T1829', 'M1026'] verdict=NOT_ENOUGH_INFO flags=[]

**final-insu-claim_nei-001** (claim_nei) — Verify the following claim against authoritative security sources: "CVE-2031-36236 is caused by weakness CWE-281." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: NOT_ENOUGH_INFO
- Evidence-Aware Agent (C): ids=[] verdict=NOT_ENOUGH_INFO flags=[]
- ReAct agent (A): ids=[] verdict=UNSUPPORTED flags=[]
- Non-agentic graph verifier (B): ids=[] verdict=NOT_ENOUGH_INFO flags=[]

**final-insu-claim_nei-002** (claim_nei) — Verify the following claim against authoritative security sources: "NIST SP 800-53 Rev. 5 control SC-23 is mapped as a mitigation for ATT&CK technique T1755.082." Answer SUPPORTED, UNSUPPORTED (the sources do not establish this association or contradict it), or NOT_ENOUGH_INFO (an entity in the claim cannot be found).

- Gold: NOT_ENOUGH_INFO
- Evidence-Aware Agent (C): ids=['SC-23'] verdict=NOT_ENOUGH_INFO flags=[]
- ReAct agent (A): ids=['SC-23'] verdict=UNSUPPORTED flags=[]
- Non-agentic graph verifier (B): ids=['SC-23'] verdict=NOT_ENOUGH_INFO flags=['OUTDATED']
