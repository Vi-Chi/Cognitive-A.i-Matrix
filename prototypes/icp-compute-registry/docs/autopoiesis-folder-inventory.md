# Autopoiesis Folder Inventory
Generated: 2026-05-26

Root: `C:\Users\Vi Chi\Desktop\Projectz\Wibo-835_Vento-Vivere\!Modules\Autopoiesis_Project`

## Summary

- Read-first files inventoried: 188
- Read-first total bytes: 638670
- This inventory intentionally excludes the Task 3 generated `autopoiesis-folder-inventory.md` and `gap-report-autopoiesis-vs-build.md` artifacts so the manifest reflects the source tree before Task 3 writes.
- Git object files are listed as repository metadata; schema and design extraction focuses on text, schema, source, script, config, and ZIP text entries.
- Key themes found: Integrity Gate, SigmaBUS/SigmaBUS envelopes, ComputeDecisionRecord, ProviderCapabilityProfile, JobLifecycleRecord, TreasuryPolicy, ICP cycles, local-first sovereignty, Akash/Golem procurement, data privacy tiers, maritime/Wibo hardware context.

## Extension Counts

| Extension | Files |
| --- | ---: |
| .did | 1 |
| .gitattributes | 1 |
| .gitignore | 1 |
| .idx | 1 |
| .json | 7 |
| .md | 45 |
| .mo | 8 |
| .pack | 1 |
| .py | 1 |
| .rev | 1 |
| .rs | 1 |
| .sample | 14 |
| .sh | 2 |
| .toml | 2 |
| .txt | 6 |
| .yml | 1 |
| .zip | 1 |
| [none] | 94 |

## Schema And Archive Details

- Root `compute-decision.schema.json`: title `ComputeDecisionRecord`; required fields include `decision_id`, `job_id`, `evaluated_at`, `decision`, `cost_breakdown`, `value_breakdown`, `net_value_credits`, `integrity_gate`, `treasury_state_before`; definitions include `CostBreakdown`, `ValueBreakdown`, `IntegrityGateResult`, `TreasurySnapshot`, and `ProviderSelectionRecord`.
- Root `treasury-policy.schema.json`: title `TreasuryPolicy`; required fields include `policy_id`, `version`, `effective_from`, `currency`, `reserve_policy`, `operating_policy`, `reinvestment_policy`, `approval_thresholds`, `lockdown_policy`, `refusal_conditions`, and `audit_requirements`; definitions include `BalanceTier`, `BurnRateThreshold`, `ApprovalThreshold`, and `RefusalCondition`.
- `PAY_icp_design_files.zip` contains `MASTER_CONTEXT.md`, `README.md`, `provider-capability.schema.json`, `job-lifecycle.schema.json`, and `compute-decision.schema.json`. The ZIP `ProviderCapabilityProfile`, `JobLifecycleRecord`, and `ComputeDecisionRecord` schemas are fuller than the compact repo `specs/` copies and are the main source for type-gap analysis where they are non-conflicting.

## File Inventory

| Path | Type | Bytes | Kind | Summary |
| --- | --- | ---: | --- | --- |
| `!BACKUP/project-autopoiesis-pre-hardening-20260526-105642/Autopoiesis_Project.txt` | txt | 13331 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `!BACKUP/project-autopoiesis-pre-hardening-20260526-105642/project-autopoiesis-ai-instruction-set.md` | md | 21860 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `Autopoiesis_Project.txt` | txt | 13331 | design documentation | Prior hardening transcript and action summary; highlights Integrity Gate, SigmaBUS, schemas, GPLv3, repo structure. |
| `compute-decision.schema.json` | json | 21988 | json schema/config | Full ComputeDecisionRecord schema with cost/value, integrity gate result, treasury snapshot, provider selection, ICP/Akash/dream metadata. |
| `icp_cloud_node.txt` | txt | 18785 | design documentation | ICP/decentralized cloud economics, cycles, treasury, local-vs-cloud architecture and cost reasoning. |
| `PAY_icp_design_files.zip` | zip | 20286 | zip archive | ZIP payload containing MASTER_CONTEXT.md, README.md, provider-capability.schema.json, job-lifecycle.schema.json, compute-decision.schema.json. |
| `Project Autopoiesis_grok.txt` | txt | 46544 | design documentation | Alternate synthesis/design transcript covering ICP role, SigmaBUS, Motoko/RISC-V, trading/treasury risks, privacy gates. |
| `Project Autopoiesis.txt` | txt | 61171 | design documentation | Large design transcript covering ICP canisters, cycles cost modeling, Akash/Golem, Matrix integration, SigmaBUS, treasury, maritime workloads. |
| `project_autopoiesis_claude_instructions_goals.md` | md | 24430 | design documentation | Project instructions/goals; economic survival layer, treasury, compute procurement, SigmaBUS, Cognitive Matrix boundaries. |
| `project-autopoiesis-ai-instruction-set.md` | md | 21860 | design documentation | Canonical AI instruction set; mission, doctrine, economic loop, integrity gate, provider registry, job manager, audit ledger. |
| `project-autopoiesis/.git/COMMIT_EDITMSG` | [none] | 29 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/config` | [none] | 380 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/description` | [none] | 73 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/HEAD` | [none] | 21 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/hooks/applypatch-msg.sample` | sample | 478 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/commit-msg.sample` | sample | 896 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/fsmonitor-watchman.sample` | sample | 4726 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/post-update.sample` | sample | 189 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/pre-applypatch.sample` | sample | 424 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/pre-commit.sample` | sample | 1649 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/pre-merge-commit.sample` | sample | 416 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/pre-push.sample` | sample | 1374 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/pre-rebase.sample` | sample | 4898 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/pre-receive.sample` | sample | 544 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/prepare-commit-msg.sample` | sample | 1492 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/push-to-checkout.sample` | sample | 2783 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/sendemail-validate.sample` | sample | 2308 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/hooks/update.sample` | sample | 3650 | project file | Git hook sample from repository metadata; no Autopoiesis design content. |
| `project-autopoiesis/.git/index` | [none] | 6152 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/info/exclude` | [none] | 240 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/logs/HEAD` | [none] | 577 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/logs/refs/heads/main` | [none] | 577 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/logs/refs/remotes/origin/HEAD` | [none] | 201 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/logs/refs/remotes/origin/main` | [none] | 328 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/00/e419a8657ceb8f69f3ff8e73b75a0853c34431` | [none] | 80 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/01/830bffe2dd27d5d0efe00fab517e2e4e0b7033` | [none] | 379 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/02/4be59b9292abb1f8d19a0ebcc7f91ee78f8de3` | [none] | 54 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/0b/1f3f047c67e9014991de02c57fd69d3d091bf5` | [none] | 54 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/0e/b43bd9f452ca2cfd63ddb6f9ba0d54e2a07b4f` | [none] | 203 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/0f/182d453ddbebb21f9d56a58d1aeeff37d88db0` | [none] | 54 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/12/286c7dade8290f58e40fe58f1f49236f488e66` | [none] | 380 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/13/f2186dcff24e88fdbc5532b65f13f8ad352a2c` | [none] | 1939 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/14/a3423a0ddcc03d62e826defe9dd619cbb2b94f` | [none] | 57 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/15/34b4094ef8d1d4e0a7b33ff5942e2b52aa6f22` | [none] | 376 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/17/2338c51e64a9882c0569897657d96f4ae0cd21` | [none] | 331 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/17/5aa355a055ac021380959e9cfc1f238dc68d16` | [none] | 228 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/1a/c3111876c35755eb38c9a98a2071f3fac0f74e` | [none] | 56 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/1b/68beb4d331adeb21eb855a229f7d358d939b46` | [none] | 122 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/1d/b137bde5c3f4cd9831ba1a42c8d03898f376ae` | [none] | 485 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/23/afc659062be6824ebc899dda0d575d41188b89` | [none] | 351 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/3b/778f96be7d29867e975750d42c30576dea8462` | [none] | 326 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/3b/d3589b746fb964b323cd48cc14936276576d6f` | [none] | 531 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/3c/9d236cdf64672ae235546ad2a7f3c1ef3245b6` | [none] | 678 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/3f/ba0de1a63162c0649033a48d50118a9b7dfdc1` | [none] | 190 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/45/132db81b68413fe7c93556e2c515b202a5c145` | [none] | 54 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/47/33fa36779577ac58c6cade5ea5649a4a8409c7` | [none] | 401 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/4b/32df21afd3485eb16145f9d0dc2fba2d850e5b` | [none] | 135 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/4f/f809a5d5562f1bc17610800825d29da209b515` | [none] | 1579 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/51/1e56888efb6d0f37b1aa257704f346f48195e6` | [none] | 970 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/51/8a873d8f896f9e287c3b4367effda8240aae95` | [none] | 397 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/5a/82fc6c9f60c3589451e2c1f6d2d421c74e121c` | [none] | 671 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/5b/22072b30bcf44b3c26d154960e2a43f89a002f` | [none] | 471 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/5d/b3820701886b40e34b683560b45ee4db12184d` | [none] | 306 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/62/42874bb54d159a053f83eb831a134292b207f5` | [none] | 9164 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/6a/94449e6d2f5ce0caa12aa5b91a6188986cd12c` | [none] | 201 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/6d/b4ae44c369275951089ef1ea5bd932de424544` | [none] | 585 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/6e/f7787bcc84074b3aaf88e2f5dfc2f43d62b23f` | [none] | 377 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/6f/c88d48c2dfeafa7fd8d4482bca3110415016f0` | [none] | 54 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/71/68da9770f6882148ca12b2c9679d842c8a1318` | [none] | 426 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/71/e4850daefc8dfff7a683ac789970b50d0b810e` | [none] | 571 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/76/b0e38841d7345fd570100fca9c91da222de97c` | [none] | 192 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/7a/7487f5bff68552164a237611f3795f99e0484c` | [none] | 766 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/89/26288f0b92734d0a64188c2d031eff0b257866` | [none] | 270 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/89/b2c79639956a8eeaae0c902b160e6611604e88` | [none] | 558 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/8a/d5a5dadb1f8a21c39d622bed551c344dde8e7b` | [none] | 74 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/8b/3db76e010aa631132c733e841e6b7f2ba3f8c4` | [none] | 196 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/8c/67b6e830329afe629c429580bb7cdb2dcc420f` | [none] | 90 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/8e/b37aa72b030b0f630189cc22a3addfc7b63486` | [none] | 131 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/99/6d9227d2b836e183d5f09eb546573e4f07f4d8` | [none] | 414 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/99/fc9e4643b65617f6199d6c57cc1f718473c503` | [none] | 76 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/a0/fa58657e54d7f6ba46dc12a7c68358d5a128d3` | [none] | 326 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/a8/e5b65edad143f5dc970d3c5b2a9b0f1cd809a4` | [none] | 325 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/ab/5ae90b44c3665c48eb0dea61d2bdc70b8dc989` | [none] | 64 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/b0/fd0244facfe5fdd6b18b10d47bccf795717597` | [none] | 103 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/b1/257145bc38896feb4a305474ae717d0ecc40c7` | [none] | 176 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/b3/41bbc426c5a01b553105d57ed8e6f8337a3e9b` | [none] | 571 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/b4/60d48baf21f3be7800df9e8eecf5fb417ee4e6` | [none] | 805 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/bc/3e5da44a8d47ecd0fadfe84dcb570bea35e7bc` | [none] | 619 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/bf/d6a51aee52f4808b39af2e59b053fe34272a74` | [none] | 325 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/c4/1454207bcccf79f4c1b4603f81f453079685a3` | [none] | 53 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/c9/aadb7fa0558df2e7b7faee15a1c6e962f2fe64` | [none] | 230 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/d2/92091d57be0e152cbdc713beff2cdbc1414a1b` | [none] | 375 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/d4/1bd9b935a559fc71b91203cf6b0ee95c736551` | [none] | 329 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/d6/58f39704f59e487858c8d0203c8e39b61ae5e9` | [none] | 124 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/d9/063e6201e15415ea92130600b126daf870a196` | [none] | 114 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/de/d9fd74196e5554ca6c228fb0109baf0b2c6d75` | [none] | 61 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/df/2f1a6c51abb84a3e6e620bb761dff1214adae3` | [none] | 195 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/e0/94f0c21cad5e5805bd7760d95900af63aece78` | [none] | 358 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/e0/dc53b3390d4ba506519c1f45e0524777fb423f` | [none] | 80 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/e1/8046f50bfca228f9992c9c9d053a1955985731` | [none] | 441 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/e2/53c6758177d933f673ab39ac65634dfd9fb75a` | [none] | 133 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/e7/93b1b3f8dfdf129c2ad945b4e97bbf8bd98a58` | [none] | 54 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/e9/79437c6137b13c04772314d694df24e42e8029` | [none] | 54 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/e9/c5fc97eff245e61d9feac0e3fb0ac224c332df` | [none] | 121 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/ef/650577d1906d92db45131c43caf889af9fd00c` | [none] | 439 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/f2/88702d2fa16d3cdf0035b15a9fcbc552cd88e7` | [none] | 14219 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/f6/b37cc1c33c7b2365252c2af83ff4a71f1926b8` | [none] | 243 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/f9/7dbaad720f998b7676355f9adbc0155536beba` | [none] | 356 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/fb/562921c58a9ec81ec130a1faab4f44f5f0db82` | [none] | 531 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/fb/a4d98124e2bf090847b48faabf81701ec947d3` | [none] | 249 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/ff/16f8f94af19d860ce3a616aaa6540b00dfdac4` | [none] | 148 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/ff/268bed8945e2209646840b6818859d56a0e97d` | [none] | 874 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/ff/e4d57a95b34a00e7b053575442f824e7d8a71f` | [none] | 323 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/pack/pack-c3aeb1342b1f83377ed97f3c94083f91ea82fbd0.idx` | idx | 1296 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/pack/pack-c3aeb1342b1f83377ed97f3c94083f91ea82fbd0.pack` | pack | 12523 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/objects/pack/pack-c3aeb1342b1f83377ed97f3c94083f91ea82fbd0.rev` | rev | 84 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/packed-refs` | [none] | 112 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/refs/heads/main` | [none] | 41 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/refs/remotes/origin/HEAD` | [none] | 30 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.git/refs/remotes/origin/main` | [none] | 41 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.gitattributes` | gitattributes | 109 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.github/ISSUE_TEMPLATE/integrity-review.md` | md | 788 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/.github/ISSUE_TEMPLATE/research-brief.md` | md | 608 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/.github/workflows/validate.yml` | yml | 384 | config | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/.gitignore` | gitignore | 358 | project file | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/CHANGELOG.md` | md | 549 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/CODE_OF_CONDUCT.md` | md | 590 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/CONTRIBUTING.md` | md | 694 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/00-thesis/00-autopoiesis-thesis.md` | md | 891 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/00-thesis/01-integrity-vs-economic-pressure.md` | md | 1175 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/00-thesis/02-compute-metabolism-model.md` | md | 902 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/10-network-map/10-network-role-map.md` | md | 975 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/10-network-map/11-icp-role-in-autopoiesis.md` | md | 690 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/10-network-map/12-akash-compute-procurement.md` | md | 508 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/10-network-map/13-golem-task-execution.md` | md | 502 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/10-network-map/14-bittensor-usefulness-markets.md` | md | 514 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/10-network-map/15-storage-and-public-memory-options.md` | md | 469 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/20-economic-loop/20-economic-loop.md` | md | 753 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/20-economic-loop/21-compute-cost-estimator.md` | md | 649 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/20-economic-loop/22-task-value-estimator.md` | md | 694 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/20-economic-loop/23-budget-and-treasury-policy.md` | md | 576 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/30-v0-prototype/30-autopoiesis-v0-scope.md` | md | 494 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/30-v0-prototype/31-icp-compute-registry-spec.md` | md | 536 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/40-procurement/40-procurement-experiment-plan.md` | md | 525 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/50-cognitive-matrix-integration/50-cognitive-matrix-integration.md` | md | 615 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/50-cognitive-matrix-integration/51-integrity-gate-for-economic-actions.md` | md | 507 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/50-cognitive-matrix-integration/52-out-of-loop-audit-of-autopoietic-decisions.md` | md | 622 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/60-services-and-revenue/60-safe-service-candidate-filter.md` | md | 811 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/docs/70-sovereignty-and-safety/70-local-sovereignty-and-privacy.md` | md | 598 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/LICENSE` | [none] | 35149 | project file | Repository license file. |
| `project-autopoiesis/MASTER_CONTEXT.md` | md | 21850 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/prototypes/icp-compute-registry/Cargo.toml` | toml | 140 | config | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/prototypes/icp-compute-registry/dfx.json` | json | 1063 | json schema/config | Prototype dfx canister manifest for Motoko canisters and Rust ledger. |
| `project-autopoiesis/prototypes/icp-compute-registry/README.md` | md | 4472 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/prototypes/icp-compute-registry/scripts/deploy_local.sh` | sh | 2031 | script | Local dfx deployment/configuration script; blocked on dfx availability on Windows host. |
| `project-autopoiesis/prototypes/icp-compute-registry/scripts/smoke_test.sh` | sh | 7214 | script | End-to-end local dfx smoke script; exercises identity, registry, ledger, market, pool, procurement, data policy. |
| `project-autopoiesis/prototypes/icp-compute-registry/SPEC.md` | md | 9632 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/agent_runtime/main.mo` | mo | 9477 | Motoko source | Motoko per-agent runtime: local job state, bidding/completion helpers, canister wiring. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/capital_pool/main.mo` | mo | 22699 | Motoko source | Motoko capital pool: Nat-only pool accounting, phases, underwriting, science pool donations/disbursements. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/compute_ledger/Cargo.toml` | toml | 202 | config | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/compute_ledger/compute_ledger.did` | did | 1039 | Candid interface | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/compute_ledger/src/lib.rs` | rs | 11067 | Rust source | Rust compute ledger: credits, escrow, stake, slashing, transfer, supply accounting. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/compute_registry/main.mo` | mo | 10060 | Motoko source | Motoko compute registry: provider catalog, matching, science pool entries. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/data_orchestrator/main.mo` | mo | 10854 | Motoko source | Motoko data orchestrator: typed privacy-tier/storage-target policy, asset registration, pipeline planning. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/identity_registry/main.mo` | mo | 7002 | Motoko source | Motoko identity registry: agent DIDs, capability profiles, hardware platform, privacy tier, registration/verification. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/job_market/main.mo` | mo | 13171 | Motoko source | Motoko job market: post/bid/accept/status lifecycle, ledger escrow, reputation outcome calls. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/procurement_router/main.mo` | mo | 20136 | Motoko source | Motoko procurement router: typed Akash/Golem/cloud/Filecoin/R2 stubs, hard privacy gate, spend caps. |
| `project-autopoiesis/prototypes/icp-compute-registry/src/reputation_engine/main.mo` | mo | 8168 | Motoko source | Motoko reputation engine: score history, outcome aggregation, endorsements/ranking. |
| `project-autopoiesis/prototypes/icp-compute-registry/tests/integration_notes.md` | md | 2024 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/prototypes/local-vs-remote-router/README.md` | md | 336 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/prototypes/treasury-simulator/README.md` | md | 348 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/README.md` | md | 3141 | design documentation | Project repository README and architecture overview. |
| `project-autopoiesis/reports/autopoiesis-discovery-phase0.md` | md | 1601 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/research/akash/README.md` | md | 130 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/research/bittensor/README.md` | md | 153 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/research/ethereum/README.md` | md | 155 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/research/golem/README.md` | md | 119 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/research/icp/README.md` | md | 129 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/research/storage/README.md` | md | 147 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/ROADMAP.md` | md | 1782 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/scripts/validate_project.py` | py | 4825 | script | Project file; inventoried and scanned where text-readable. |
| `project-autopoiesis/SECURITY.md` | md | 933 | design documentation | Text/design document; scanned for ICP, SigmaBUS, Integrity Gate, treasury, maritime, schema, and canister concepts. |
| `project-autopoiesis/specs/compute-decision.schema.json` | json | 2129 | json schema/config | Compact ComputeDecision schema; conflicts with richer root/ZIP ComputeDecisionRecord. |
| `project-autopoiesis/specs/job-lifecycle.schema.json` | json | 1683 | json schema/config | Compact JobLifecycle schema; overlaps but is smaller than ZIP JobLifecycleRecord. |
| `project-autopoiesis/specs/provider-capability.schema.json` | json | 2147 | json schema/config | Compact ProviderCapability schema; overlaps but is smaller than ZIP ProviderCapabilityProfile. |
| `project-autopoiesis/specs/treasury-policy.schema.json` | json | 1799 | json schema/config | Compact TreasuryPolicy schema; conflicts with richer root TreasuryPolicy. |
| `recapitalization.txt` | txt | 12930 | design documentation | Recapitalization/economic planning notes connected to treasury and survival-loop funding. |
| `treasury-policy.schema.json` | json | 27108 | json schema/config | Full TreasuryPolicy schema with reserve, operating, reinvestment, approval threshold, lockdown, refusal, and audit requirements. |
