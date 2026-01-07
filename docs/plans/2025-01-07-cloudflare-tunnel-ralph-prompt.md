# Ralph Loop Prompt: Cloudflare Tunnel Implementation

## Invocation

```
/ralph-loop "Implement Cloudflare Tunnel for Family Flix following docs/plans/2025-01-07-cloudflare-tunnel-implementation.md" --max-iterations 50 --completion-promise "CLOUDFLARE_TUNNEL_COMPLETE"
```

---

## Full Prompt

```markdown
# Task: Implement Cloudflare Tunnel for Family Flix

You are implementing Cloudflare Tunnel with Access authentication for Family Flix.

## Reference Documents

- **Design:** `docs/plans/2025-01-07-cloudflare-tunnel-design.md`
- **Checklist:** `docs/plans/2025-01-07-cloudflare-tunnel-implementation.md`

## Instructions

1. **Read the implementation checklist** to see current progress
2. **Identify the next incomplete step** (first unchecked item)
3. **Execute that step** using appropriate tools:
   - Browser automation (mcp__claude-in-chrome__*) for Cloudflare dashboard
   - Bash for SSH commands to LXC 103
   - Edit for docker-compose changes
4. **Update the checklist** by checking off completed items
5. **Verify the step succeeded** before proceeding

## Tool Selection Guide

| Task | Tools |
|------|-------|
| Cloudflare dashboard | `tabs_context_mcp` → `navigate` → `read_page` → `computer`/`form_input` |
| SSH to homelab | `Bash` with `ssh root@100.115.142.20 'pct exec 103 -- ...'` |
| Edit compose file | `Edit` tool on `deploy/docker-compose.homelab.yml` |
| Verify endpoints | `Bash` with `curl` |

## Browser Automation Notes

- Always call `tabs_context_mcp` first to get valid tab IDs
- Create new tab with `tabs_create_mcp` for Cloudflare work
- Use `read_page` to understand page structure before clicking
- Use `computer` with `screenshot` action to verify state
- Cloudflare Zero Trust URL: `https://one.dash.cloudflare.com/`

## Human Checkpoints

If you encounter a step marked **HUMAN:** in the checklist:
1. Stop and clearly explain what the human needs to do
2. Wait for confirmation before proceeding
3. Use AskUserQuestion if credentials or tokens are needed

## SSH Access Pattern

```bash
# Execute command in LXC 103
ssh root@100.115.142.20 'pct exec 103 -- <command>'

# Example: Check docker containers
ssh root@100.115.142.20 'pct exec 103 -- docker ps'

# Example: View logs
ssh root@100.115.142.20 'pct exec 103 -- docker logs familyflix-cloudflared'
```

## Progress Tracking

After completing each step:
1. Update `docs/plans/2025-01-07-cloudflare-tunnel-implementation.md`
2. Change `- [ ]` to `- [x]` for completed items
3. Set phase completion flags when all items in phase done

## Completion Criteria

Output the promise ONLY when ALL of these are true:
- All 5 phases marked complete in checklist
- `https://flix.andofam.com` shows Cloudflare Access login
- Sign-in flow works with authorized user
- Tailscale access still functional

When complete, output:
<promise>CLOUDFLARE_TUNNEL_COMPLETE</promise>

## Error Handling

If a step fails:
1. Document the error in the checklist
2. Attempt remediation based on Troubleshooting section
3. If stuck after 3 attempts on same step, use AskUserQuestion for help

## Current Iteration Focus

Read the checklist now and identify the FIRST unchecked non-HUMAN item. Execute it.
If all non-HUMAN items before a HUMAN item are done, prompt the user to complete the HUMAN step.
```

---

## Alternative: Phased Execution

If you prefer to run phases separately:

### Phase 2 Only (Docker Compose)
```
/ralph-loop "Update docker-compose.homelab.yml to add cloudflared service per docs/plans/2025-01-07-cloudflare-tunnel-implementation.md Phase 2" --max-iterations 5 --completion-promise "PHASE_2_COMPLETE"
```

### Phase 3 Only (Deploy)
```
/ralph-loop "Deploy updated Family Flix to homelab with cloudflared container per docs/plans/2025-01-07-cloudflare-tunnel-implementation.md Phase 3. Token will be provided." --max-iterations 10 --completion-promise "PHASE_3_COMPLETE"
```

### Phase 4 Only (Access Setup via Browser)
```
/ralph-loop "Configure Cloudflare Access for flix.andofam.com per docs/plans/2025-01-07-cloudflare-tunnel-implementation.md Phase 4. Use browser automation." --max-iterations 15 --completion-promise "PHASE_4_COMPLETE"
```

### Phase 5 Only (Verification)
```
/ralph-loop "Verify Cloudflare Tunnel implementation per docs/plans/2025-01-07-cloudflare-tunnel-implementation.md Phase 5" --max-iterations 10 --completion-promise "PHASE_5_COMPLETE"
```

---

## Pre-Flight Checklist

Before running Ralph Loop:

- [ ] Human has completed all HUMAN-marked prerequisites
- [ ] Cloudflare account exists and is logged in (browser)
- [ ] andofam.com is active in Cloudflare
- [ ] Tunnel `andofam-tunnel` created and token available
- [ ] SSH access to homelab working (`ssh root@100.115.142.20`)
- [ ] Chrome browser open for Claude-in-Chrome automation
