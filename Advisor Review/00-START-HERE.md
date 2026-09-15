# REVIEWER BOOTSTRAP PACKET — START HERE

Purpose: eliminate copy/paste/version drift while bootstrapping the two CIS reviewer lineages.

## What is in this packet
1. CARD-01-reviewer-measurement-v1.md
   Gives advisor/evaluator the ability to measure and adds independent round-1 + reconciliation.

2. CARD-02-reviewer-isolation-v1.md
   Separates reviewer execution from mutator execution so reviewers cannot change protected state.

3. SEND-TO-GLM.txt
   Independent adversarial review instructions for GLM.

4. SEND-TO-QWEN.txt
   Independent adversarial review instructions for Qwen.

5. CLAUDE-CODE-HANDOFF.txt
   Use only after a card version is approved.

6. SHA256SUMS.txt
   Integrity manifest for the exact files in this packet.

## The manual bootstrap workflow

A. REVIEW CARD 01
- Open a fresh GLM platform chat.
- Upload SEND-TO-GLM.txt and CARD-01-reviewer-measurement-v1.md.
- Save the full GLM response as: REVIEW-GLM-CARD-01-v1.txt
- Open a fresh Qwen platform chat.
- Upload SEND-TO-QWEN.txt and CARD-01-reviewer-measurement-v1.md.
- Save the full Qwen response as: REVIEW-QWEN-CARD-01-v1.txt
- Do NOT show either reviewer the other's round-1 review.

B. REVISE
- Give the original CARD-01 file plus BOTH review files to the drafter.
- The next card must get a new VERSION and CANONICAL_TOKEN plus a CHANGES section mapping every reviewer finding to: ACCEPTED / REJECTED WITH REASON / DEFERRED WITH SCOPE.
- Never overwrite an old version. Create v2 as a new file.

C. ROUND 2
- Upload the new canonical v2 file to each reviewer with the same reviewer instruction file.
- Require the reviewer to echo CARD_ID + VERSION + CANONICAL_TOKEN before reviewing.
- Repeat until the version is approved or explicitly rejected.

D. IMPLEMENT
- Once the approved version is frozen, upload that exact card file plus CLAUDE-CODE-HANDOFF.txt to Claude Code.
- Claude implements only that card and returns raw evidence.

E. VERIFY
- After CARD-01 is implemented, its contained advisor/evaluator should be able to perform measurement and reconciliation.
- Do not treat them as trusted non-mutating reviewers until CARD-02 isolation is also implemented and proven.

F. REVIEW / IMPLEMENT CARD 02
- Repeat the same GLM + Qwen independent-review process for CARD-02.
- After approval, give the exact approved CARD-02 version to Claude Code.
- Require the isolation evidence from the card.

## Rules that prevent the copy/paste failure
- The FILE is the artifact of record; chat text is not.
- Never copy a card out of a conversation transcript.
- Never overwrite a versioned card.
- Every card carries CARD_ID, VERSION, and CANONICAL_TOKEN inside the content.
- Every reviewer must echo those three fields before reviewing.
- GLM and Qwen round 1 remain independent.
- Keep each complete review as its own file.
- Use SHA256SUMS.txt when you need byte-level confirmation.
