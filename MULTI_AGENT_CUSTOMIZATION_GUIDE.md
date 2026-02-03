# Multi-Agent Customization Guide

## Overview

The multi-agent system is now configured to prioritize **business consulting** over immediate technical solutions. The Consultant agent will ask clarifying questions to understand the full business context before recommending solutions.

## Updated Agent Behaviors

### 1. Consultant Agent (BUSINESS CONSULTANT)

**New Behavior:**
- **ALWAYS asks questions first** - Never jumps to solutions
- Gathers 3-5 business context questions before recommending
- Strongly advocates for OOB (Out-of-Box) solutions
- Presents implementation risks when custom is considered
- Acts as a trusted advisor, not just an answer machine

**Example Interaction:**

**Before (Old Behavior):**
```
User: "I need to auto-assign incidents"
Consultant: "Here's how to configure assignment rules... [provides solution immediately]"
```

**After (New Behavior):**
```
User: "I need to auto-assign incidents"
Consultant: "I'd like to understand your requirements better:

1. What criteria should determine assignment? (category, location, urgency?)
2. Who should incidents be assigned to - individuals or groups?
3. Do you have existing assignment groups set up?
4. Are there special workflows or approval processes?
5. What happens if no match is found?

This will help me recommend the best OOB approach."
```

**When It's Triggered:**
- Business requirements ("I need to...", "How should we...")
- Process questions ("What's the best practice...")
- OOB configuration questions
- Strategic decisions
- **Any question about business processes or workflows**

### 2. Orchestrator (ROUTING LOGIC)

**New Behavior:**
- **Biases toward Consultant** for ambiguous queries
- Distinguishes business problems from technical requests
- Routes based on question type, not keywords
- Assumes most users need context-gathering, not immediate solutions

**Business Problem → Consultant:**
- "I need to auto-assign incidents" → **Consultant** (business requirement)
- "We want to improve approvals" → **Consultant** (process optimization)
- "How should we handle changes?" → **Consultant** (business process)

**Technical Request → Solution Architect:**
- "Write a business rule to..." → **Solution Architect** (explicit code request)
- "Create a custom table..." → **Solution Architect** (explicit custom request)

**Instance Problem → Implementation:**
- "My incidents aren't assigning" → **Implementation** (troubleshooting)
- "Getting errors in logs" → **Implementation** (debugging)

## How to Customize Agent Behaviors

### Access Superadmin Settings

1. Log in as superadmin
2. Go to **Admin Dashboard**
3. Click **Superadmin** tab
4. Select the agent you want to customize

### What You Can Customize

#### Consultant Agent
- **Question-asking behavior**
  - Number of questions (default: 3-5)
  - Depth of questions
  - When to ask vs when to answer directly

- **OOB vs Custom framework**
  - How strongly to advocate for OOB
  - When to present custom as an option
  - How to present implementation risks

- **Tone and style**
  - Consultative vs directive
  - Educational vs prescriptive
  - Patience level

**Example Customizations:**

*Make Consultant More Directive:*
```
Change: "I'd like to understand your requirements better:"
To: "To recommend the right solution, I need to know:"
```

*Adjust Question Count:*
```
Change: "3-5 questions"
To: "2-3 quick questions" (faster)
Or: "5-7 detailed questions" (more thorough)
```

*Change OOB Advocacy Strength:*
```
Stronger: "I strongly recommend avoiding custom code unless absolutely necessary"
Balanced: "Let's evaluate both OOB and custom approaches"
Lighter: "Both OOB and custom are valid options"
```

#### Orchestrator
- **Routing bias**
  - Default agent when uncertain
  - Threshold for routing to each agent

- **Classification criteria**
  - Keywords that trigger each agent
  - Business vs technical patterns

- **Confidence levels**
  - When to default to Consultant
  - When to route directly

**Example Customizations:**

*Increase Technical Routing:*
```
Change: "When in doubt, route to Consultant"
To: "Route to Solution Architect for any technical keywords"
```

*Adjust Business/Technical Classification:*
```
Add keywords:
Business: "workflow", "process", "users", "stakeholders"
Technical: "code", "script", "API", "integration"
```

## Customization Best Practices

### 1. Test Changes Incrementally

```
1. Make small changes to one aspect
2. Test with sample queries
3. Observe behavior
4. Adjust as needed
5. Repeat
```

### 2. Document Your Changes

Keep a log of what you changed and why:
```
Date: 2026-01-31
Agent: Consultant
Change: Reduced question count from 5 to 3
Reason: Users complained about too many questions
Result: Faster but less context
```

### 3. Use the Default as a Template

- View the default prompt (click "View Default")
- Copy sections you like
- Modify specific behaviors
- Keep the overall structure

### 4. Monitor and Iterate

After making changes:
- Test with real user queries
- Check handoff analytics
- Gather user feedback
- Refine based on patterns

## Common Customization Scenarios

### Scenario 1: "Consultant asks TOO many questions"

**Change:**
```
From: "Ask 3-5 questions"
To: "Ask 2-3 focused questions"
```

**And/Or:**
```
From: "Gather business context, technical context..."
To: "Gather essential business context only"
```

### Scenario 2: "Need faster responses"

**Change Consultant:**
```
Add: "If user provides sufficient context, skip additional questions"
```

**Change Orchestrator:**
```
Add: "For experienced users, route directly to Solution Architect for technical queries"
```

### Scenario 3: "Too much OOB bias"

**Change Consultant:**
```
From: "Strongly advocate for OOB"
To: "Present both OOB and custom as equal options with trade-offs"
```

### Scenario 4: "Users expect direct answers"

**Change Consultant:**
```
From: "ALWAYS ask questions first"
To: "For simple, common questions, provide direct answer then ask if they need customization"
```

## Testing Your Changes

### 1. Use Test Queries

**Business Context Test:**
```
Query: "I need to auto-assign incidents"
Expected: Consultant asks about assignment criteria, groups, workflows
```

**Technical Test:**
```
Query: "Write a business rule to auto-assign incidents"
Expected: Routes directly to Solution Architect
```

**Instance Problem Test:**
```
Query: "My incidents aren't auto-assigning"
Expected: Routes to Implementation for diagnostics
```

### 2. Check Handoff Analytics

After changes:
1. Go to Admin Dashboard → Multi-Agent tab
2. View handoff analytics
3. Look for unusual patterns:
   - Excessive handoffs = routing issues
   - No handoffs = agents too isolated
   - Circular handoffs = confusion

### 3. Monitor User Feedback

- Are users getting frustrated with questions?
- Are solutions appropriate?
- Is the consultant jumping to code too quickly?
- Is enough context being gathered?

## Rollback Instructions

If changes don't work as expected:

1. Go to Superadmin Settings
2. Select the agent
3. Click "Reset to Default"
4. Confirm

**Note:** This restores the system default. Your custom changes are lost.

**Best Practice:** Keep a backup copy of working custom prompts in a separate document.

## Advanced Customization

### Adding New Behaviors

You can add entirely new behaviors to the prompts:

**Example: Add Industry-Specific Guidance**
```
Add to Consultant prompt:
"**HEALTHCARE SPECIFIC:**
- Always consider HIPAA compliance
- Check for PHI data handling
- Recommend encryption for sensitive data"
```

**Example: Add Company Policies**
```
Add to Consultant prompt:
"**COMPANY POLICIES:**
- All custom code requires security review
- Must use company naming conventions
- Always log decisions in project wiki"
```

### Changing Decision Frameworks

**Example: Custom OOB vs Custom Decision Tree**
```
Add to Consultant prompt:
"**DECISION TREE:**
1. Can OOB do it 100%? → Use OOB
2. Can OOB do 80%+? → Use OOB with minor config
3. Can OOB do 50-80%? → Evaluate custom vs process change
4. OOB does <50%? → Consider custom, but challenge requirements"
```

## Support

If you need help customizing:

1. **View Documentation**
   - See default prompts for examples
   - Check this guide for common scenarios

2. **Test Incrementally**
   - Make small changes
   - Test each change
   - Document results

3. **Reset if Needed**
   - You can always revert to defaults
   - No permanent harm from experimentation

## Changelog

### 2026-01-31
- Updated Consultant to ask questions before providing solutions
- Configured to strongly advocate for OOB
- Updated Orchestrator to bias toward Consultant for business problems
- Added comprehensive customization UI with guidance
