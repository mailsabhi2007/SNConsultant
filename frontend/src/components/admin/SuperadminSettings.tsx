import { useEffect, useState } from "react";
import {
  Code,
  RotateCcw,
  Save,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  RefreshCw
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  getAllAgentPrompts,
  getAgentPrompt,
  updateAgentPrompt,
  resetAgentPrompt,
  AgentPrompt,
  AgentPromptDetail,
} from "@/services/admin";
import { useToast } from "@/components/ui/use-toast";

const AGENT_NAMES = [
  {
    id: 'consultant',
    label: 'Consultant Agent',
    description: 'Business process consulting - Asks context questions, drives toward OOB',
    role: 'BUSINESS CONSULTANT',
    guidance: 'Customize to control how the agent gathers business context, when to ask clarifying questions, and how strongly to advocate for OOB solutions vs custom approaches.',
    keyAspects: [
      'Question-asking behavior before providing solutions',
      'Number and depth of clarifying questions',
      'OOB vs Custom decision framework',
      'Risk presentation for custom solutions',
      'Tone (consultative, educational, etc.)'
    ]
  },
  {
    id: 'solution_architect',
    label: 'Solution Architect Agent',
    description: 'Technical implementation - Custom code, scripts, schema design',
    role: 'TECHNICAL ARCHITECT',
    guidance: 'Customize to control code quality standards, documentation requirements, security practices, and when to suggest alternatives to custom code.',
    keyAspects: [
      'Code quality and best practices enforcement',
      'Security and performance considerations',
      'Documentation requirements',
      'When to challenge custom requests',
      'Integration patterns and standards'
    ]
  },
  {
    id: 'implementation',
    label: 'Implementation Agent',
    description: 'Live instance troubleshooting - Diagnostics, errors, debugging',
    role: 'IMPLEMENTATION SPECIALIST',
    guidance: 'Customize to control troubleshooting methodology, diagnostic depth, permission handling, and escalation criteria.',
    keyAspects: [
      'Diagnostic methodology and depth',
      'Permission request handling',
      'Log analysis approach',
      'When to escalate issues',
      'Root cause analysis depth'
    ]
  },
  {
    id: 'orchestrator',
    label: 'Orchestrator',
    description: 'Query routing - Determines which specialist handles each query',
    role: 'ROUTING ORCHESTRATOR',
    guidance: 'Customize to control how queries are classified as business vs technical, bias toward certain agents, and routing decision criteria.',
    keyAspects: [
      'Business vs technical classification',
      'Default agent when uncertain',
      'Keywords and patterns for routing',
      'Bias toward Consultant for ambiguous queries',
      'Handoff threshold tuning'
    ]
  },
];

interface PromptEditorProps {
  agentName: string;
  agentLabel: string;
  onSaved: () => void;
}

function PromptEditor({ agentName, agentLabel, onSaved }: PromptEditorProps) {
  const [promptDetail, setPromptDetail] = useState<AgentPromptDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState('');
  const [showDefault, setShowDefault] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadPrompt();
  }, [agentName]);

  const loadPrompt = async () => {
    setIsLoading(true);
    try {
      const data = await getAgentPrompt(agentName);
      setPromptDetail(data);
      setEditedPrompt(data.custom_prompt || data.default_prompt);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load agent prompt",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editedPrompt.trim() || editedPrompt.length < 10) {
      toast({
        title: "Error",
        description: "Prompt is too short (minimum 10 characters)",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    try {
      await updateAgentPrompt(agentName, editedPrompt);
      toast({
        title: "Success",
        description: `${agentLabel} prompt updated successfully`,
      });
      onSaved();
      loadPrompt();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update prompt",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset to the default prompt? This cannot be undone.')) {
      return;
    }

    setIsSaving(true);
    try {
      await resetAgentPrompt(agentName);
      toast({
        title: "Success",
        description: `${agentLabel} prompt reset to default`,
      });
      onSaved();
      loadPrompt();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to reset prompt",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const hasChanges = editedPrompt !== (promptDetail?.custom_prompt || promptDetail?.default_prompt);
  const isUsingCustom = promptDetail?.is_using_custom || false;

  return (
    <div className="space-y-4">
      {/* Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant={isUsingCustom ? 'default' : 'secondary'}>
            {isUsingCustom ? (
              <>
                <CheckCircle2 className="mr-1 h-3 w-3" />
                Using Custom
              </>
            ) : (
              'Using Default'
            )}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {editedPrompt.length} characters
          </span>
        </div>

        <div className="flex gap-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                {showDefault ? <EyeOff className="mr-2 h-4 w-4" /> : <Eye className="mr-2 h-4 w-4" />}
                View Default
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Default Prompt - {agentLabel}</DialogTitle>
                <DialogDescription>
                  This is the original default prompt that ships with the system
                </DialogDescription>
              </DialogHeader>
              <pre className="p-4 bg-muted rounded-lg text-sm whitespace-pre-wrap">
                {promptDetail?.default_prompt}
              </pre>
            </DialogContent>
          </Dialog>

          {isUsingCustom && (
            <Button variant="outline" size="sm" onClick={handleReset} disabled={isSaving}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Reset to Default
            </Button>
          )}
        </div>
      </div>

      {/* Editor */}
      <Textarea
        value={editedPrompt}
        onChange={(e) => setEditedPrompt(e.target.value)}
        className="min-h-[400px] font-mono text-sm"
        placeholder="Enter system prompt..."
      />

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {hasChanges && (
            <span className="text-orange-600">• Unsaved changes</span>
          )}
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setEditedPrompt(promptDetail?.custom_prompt || promptDetail?.default_prompt || '')}
            disabled={!hasChanges || isSaving}
          >
            Discard Changes
          </Button>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
          >
            {isSaving ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Prompt
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function SuperadminSettings() {
  const [prompts, setPrompts] = useState<AgentPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    setIsLoading(true);
    try {
      const data = await getAllAgentPrompts();
      setPrompts(data.prompts);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load agent prompts",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Warning */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Superadmin Settings</AlertTitle>
        <AlertDescription>
          These settings control the core behavior of the multi-agent system. Changes take effect immediately and affect all users. Always test changes carefully.
        </AlertDescription>
      </Alert>

      {/* Prompt Editors */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Agent System Prompts
          </CardTitle>
          <CardDescription>
            Customize the system prompts for each agent. These prompts define the agent's personality, capabilities, and behavior.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="consultant" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              {AGENT_NAMES.map((agent) => (
                <TabsTrigger key={agent.id} value={agent.id}>
                  {agent.label.split(' ')[0]}
                </TabsTrigger>
              ))}
            </TabsList>

            {AGENT_NAMES.map((agent) => (
              <TabsContent key={agent.id} value={agent.id} className="space-y-4">
                {/* Agent Info & Guidance */}
                <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg">{agent.label}</h3>
                      <Badge variant="outline">{agent.role}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{agent.description}</p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium mb-2">Customization Guidance:</h4>
                    <p className="text-sm text-muted-foreground mb-3">{agent.guidance}</p>

                    <div className="text-sm">
                      <span className="font-medium">Key aspects you can tune:</span>
                      <ul className="mt-2 space-y-1 ml-4 list-disc text-muted-foreground">
                        {agent.keyAspects.map((aspect, idx) => (
                          <li key={idx}>{aspect}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                <PromptEditor
                  agentName={agent.id}
                  agentLabel={agent.label}
                  onSaved={loadPrompts}
                />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Prompt Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Prompt Status Overview</CardTitle>
          <CardDescription>
            Quick view of which agents are using custom prompts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {AGENT_NAMES.map((agent) => {
              const prompt = prompts.find(p => p.agent_name === agent.id);
              const isCustom = prompt?.is_active || false;

              return (
                <div key={agent.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="font-medium">{agent.label}</div>
                    <div className="text-sm text-muted-foreground">{agent.description}</div>
                  </div>
                  <Badge variant={isCustom ? 'default' : 'outline'}>
                    {isCustom ? 'Custom' : 'Default'}
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
