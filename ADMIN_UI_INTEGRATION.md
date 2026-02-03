# Admin UI Integration Guide

## New UI Components Created

✅ **Multi-Agent Management Component** - `frontend/src/components/admin/MultiAgentManagement.tsx`
  - Rollout percentage slider
  - User management table with toggles
  - Handoff analytics visualization
  - Live metrics cards

✅ **Superadmin Settings Component** - `frontend/src/components/admin/SuperadminSettings.tsx`
  - Agent prompt editor for all 4 agents
  - View default vs custom prompts
  - Reset to default functionality
  - Prompt status overview

✅ **UI Components** - `frontend/src/components/ui/`
  - `slider.tsx` - Slider component for rollout percentage
  - `switch.tsx` - Toggle switches for user management
  - `alert.tsx` - Alert banners
  - `use-toast.ts` - Toast notifications hook

## Integration Steps

### Step 1: Add Required Dependencies

```bash
cd frontend
npm install @radix-ui/react-slider @radix-ui/react-switch class-variance-authority
```

### Step 2: Update Admin.tsx Imports

Add these imports to `frontend/src/pages/Admin.tsx` after the existing imports:

```typescript
// Add these imports around line 56
import { MultiAgentManagement } from "@/components/admin/MultiAgentManagement";
import { SuperadminSettings } from "@/components/admin/SuperadminSettings";
```

### Step 3: Add State for Current User

Add this state hook in the AdminPage component (around line 100):

```typescript
const [currentUser, setCurrentUser] = useState<{is_superadmin?: boolean} | null>(null);

useEffect(() => {
  // Fetch current user info - you'll need to implement this
  // For now, you can check the user's cookies or context
  const fetchCurrentUser = async () => {
    try {
      // Call your auth endpoint to get current user
      // const user = await getCurrentUser();
      // setCurrentUser(user);

      // Temporary - check if user is admin from existing logic
      setCurrentUser({ is_superadmin: false }); // Update based on actual user
    } catch (error) {
      console.error("Failed to fetch current user");
    }
  };
  fetchCurrentUser();
}, []);
```

### Step 4: Wrap Content in Tabs

Replace the main return JSX (starting around line 320) with this tabbed structure:

```typescript
return (
  <div className="container mx-auto max-w-7xl px-4 py-8">
    <div className="mb-8 flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Admin Dashboard</h1>
        <p className="mt-1 text-muted-foreground">
          User analytics and system monitoring
        </p>
      </div>
      <div className="flex gap-2">
        <Badge variant="secondary">Admin</Badge>
        {currentUser?.is_superadmin && (
          <Badge variant="default">Superadmin</Badge>
        )}
      </div>
    </div>

    <Tabs defaultValue="overview" className="space-y-6">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="users">Users</TabsTrigger>
        <TabsTrigger value="multi-agent">Multi-Agent</TabsTrigger>
        {currentUser?.is_superadmin && (
          <TabsTrigger value="superadmin">Superadmin</TabsTrigger>
        )}
      </TabsList>

      {/* Overview Tab - Original analytics content */}
      <TabsContent value="overview">
        <div className="space-y-6">
          {/* Analytics Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Users"
              value={analytics.total_users}
              description={`${analytics.recent_signups} new this week`}
              icon={<Users className="h-4 w-4" />}
            />
            <StatCard
              title="Active Today"
              value={analytics.active_today}
              description={`${analytics.active_this_week} active this week`}
              icon={<Activity className="h-4 w-4" />}
            />
            <StatCard
              title="Total Prompts"
              value={analytics.total_prompts.toLocaleString()}
              description={`Across ${analytics.total_sessions} sessions`}
              icon={<MessageSquare className="h-4 w-4" />}
            />
            <StatCard
              title="Avg Session Time"
              value={formatDuration(analytics.avg_session_duration)}
              description="Average session duration"
              icon={<Clock className="h-4 w-4" />}
            />
          </div>

          {/* Tavily Configuration - Keep existing content */}
          {/* ... existing Tavily card ... */}
        </div>
      </TabsContent>

      {/* Users Tab - Move users table here */}
      <TabsContent value="users">
        {/* Move the entire users table Card here */}
        {/* ... existing users table content ... */}
      </TabsContent>

      {/* Multi-Agent Tab - NEW */}
      <TabsContent value="multi-agent">
        <MultiAgentManagement />
      </TabsContent>

      {/* Superadmin Tab - NEW (conditional) */}
      {currentUser?.is_superadmin && (
        <TabsContent value="superadmin">
          <SuperadminSettings />
        </TabsContent>
      )}
    </Tabs>
  </div>
);
```

## Quick Integration (Minimal Changes)

If you prefer to add tabs without restructuring the entire page, you can add the multi-agent section at the bottom:

### Add to Admin.tsx (after the users table, around line 650):

```typescript
{/* Multi-Agent Management Section */}
<div className="mt-8">
  <h2 className="text-xl font-semibold mb-4">Multi-Agent System</h2>
  <MultiAgentManagement />
</div>

{/* Superadmin Settings Section - Only for superadmins */}
{currentUser?.is_superadmin && (
  <div className="mt-8">
    <h2 className="text-xl font-semibold mb-4">Superadmin Settings</h2>
    <SuperadminSettings />
  </div>
)}
```

## Testing the UI

1. **Start the frontend:**
```bash
cd frontend
npm run dev
```

2. **Navigate to Admin page:**
   - Login as an admin user
   - Go to `/admin` route

3. **Test Multi-Agent Management:**
   - Try changing rollout percentage
   - Toggle multi-agent for specific users
   - View handoff analytics
   - Check user table updates

4. **Test Superadmin Settings** (if superadmin):
   - Edit agent prompts
   - View default prompts
   - Save custom prompts
   - Reset to defaults

## Troubleshooting

### Issue: Tabs component not found
```bash
# Make sure tabs component exists
ls frontend/src/components/ui/tabs.tsx
```

### Issue: Import errors
```bash
# Check if new components exist
ls frontend/src/components/admin/
ls frontend/src/components/ui/slider.tsx
ls frontend/src/components/ui/switch.tsx
ls frontend/src/components/ui/alert.tsx
ls frontend/src/components/ui/use-toast.ts
```

### Issue: Toast notifications not working
The toast hook is a simplified version. For full toast functionality, consider installing:
```bash
npm install sonner
```
Then replace the use-toast import with sonner.

### Issue: Radix UI not installed
```bash
npm install @radix-ui/react-slider @radix-ui/react-switch
```

## Component Features

### MultiAgentManagement Component
- ✅ Live rollout percentage control
- ✅ User table with multi-agent status
- ✅ Handoff analytics (last 30 days)
- ✅ Common handoff paths visualization
- ✅ Switch toggles for per-user control
- ✅ Remove override functionality
- ✅ Auto-refresh capability

### SuperadminSettings Component
- ✅ Tabbed interface for 4 agents
- ✅ Syntax-highlighted prompt editor
- ✅ View default prompts dialog
- ✅ Character count
- ✅ Unsaved changes indicator
- ✅ Save/discard functionality
- ✅ Reset to default button
- ✅ Prompt status overview

## Screenshots (What it Looks Like)

### Multi-Agent Tab
```
┌─────────────────────────────────────────────────────┐
│ Multi-Agent System Management                        │
│ [Alert] Control the rollout of the multi-agent...   │
├─────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │Rollout   │ │Users     │ │Handoff   │ │Total     ││
│ │Status    │ │Enabled   │ │Rate      │ │Handoffs  ││
│ │  50%     │ │  15      │ │  18.5%   │ │  45      ││
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
├─────────────────────────────────────────────────────┤
│ System Rollout Control                               │
│ ┌───────────────────────────────────────────────┐  │
│ │ Rollout Percentage            50%             │  │
│ │ [━━━━━━━━●━━━━━━━━━━━━━━━━━━]              │  │
│ │ 0%              50%              100%         │  │
│ │ [Update Rollout] [Disable All] [Enable All]  │  │
│ └───────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│ User Management                                      │
│ ┌───────────────────────────────────────────────┐  │
│ │Username│Email│Role│Status│Multi-Agent│Source│  │
│ │john_doe│...  │User│Active│    [●]    │rollout│  │
│ │admin   │...  │Admin│...   │    [●]    │override│  │
│ └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Superadmin Tab
```
┌─────────────────────────────────────────────────────┐
│ Agent System Prompts                                 │
│ ┌──────────┬──────────┬──────────┬──────────┐      │
│ │Consultant│Architect│Implementation│Orchestrator│   │
│ └──────────┴──────────┴──────────┴──────────┘      │
│                                                      │
│ Consultant Agent                                     │
│ Best practices and OOB configurations                │
│                                                      │
│ [Using Custom ✓]  2,451 characters                  │
│ [View Default] [Reset to Default]                   │
│                                                      │
│ ┌────────────────────────────────────────────────┐ │
│ │You are an expert ServiceNow consultant...      │ │
│ │                                                 │ │
│ │[Prompt text editor - 400px height]             │ │
│ │                                                 │ │
│ └────────────────────────────────────────────────┘ │
│                                                      │
│ • Unsaved changes                                   │
│              [Discard Changes] [Save Prompt]        │
└─────────────────────────────────────────────────────┘
```

## Next Steps

1. ✅ All components created
2. ✅ Service functions ready
3. ✅ Backend endpoints functional
4. 🔲 Integrate into Admin.tsx
5. 🔲 Test end-to-end
6. 🔲 Deploy to production

Follow the integration steps above to add the new tabs to your Admin page!
