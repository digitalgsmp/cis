## CARD 4.2 — merge against the build list (BUILD)

```
For each mined_tasks row, grep docs/UNIFIED_BUILD_LIST.md and set in_build_list
or leave NULL. Paste the grep for anything marked covered.

PROOF:
  select count(*) from mined_tasks where in_build_list is null
  select count(*) from mined_tasks where in_build_list is not null
The first number is the answer to the question you asked on 8/30: how many of
these are new versus already acknowledged.
```
