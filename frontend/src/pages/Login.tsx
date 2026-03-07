import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Brain, User, Lock, Mail, Eye, EyeOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import axios from "axios";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

const registerSchema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters"),
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;
type RegisterFormData = z.infer<typeof registerSchema>;

function FloatingOrbs() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute -top-32 -left-32 h-[500px] w-[500px] rounded-full bg-primary/10 blur-[100px] animate-float" />
      <div
        className="absolute top-1/4 -right-20 h-[400px] w-[400px] rounded-full bg-agent-architect/10 blur-[100px] animate-float"
        style={{ animationDelay: "1s" }}
      />
      <div
        className="absolute -bottom-16 left-1/4 h-[450px] w-[450px] rounded-full bg-agent-consultant/[0.08] blur-[100px] animate-float"
        style={{ animationDelay: "2s" }}
      />
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[300px] w-[300px] rounded-full bg-agent-orchestrator/[0.06] blur-[80px] animate-float"
        style={{ animationDelay: "3s" }}
      />
      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(148,197,233,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(148,197,233,0.3) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(148,197,233,0.04)_0%,_transparent_70%)]" />
    </div>
  );
}

export function LoginPage() {
  const { login, register: registerUser } = useAuth();
  const [activeTab, setActiveTab] = useState<"signin" | "register">("signin");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: "", email: "", password: "" },
  });

  const handleLogin = async (data: LoginFormData) => {
    setError(null);
    setIsLoading(true);
    try {
      await login(data.username.trim(), data.password);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const status = err.response?.status;
        const detail = (err.response?.data as { detail?: string })?.detail;
        if (status === 401) {
          setError("Invalid username or password.");
        } else if (status) {
          setError(detail ? `Login failed: ${detail}` : `Login failed (status ${status}).`);
        } else {
          setError("Login failed: unable to reach the server.");
        }
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (data: RegisterFormData) => {
    setError(null);
    setIsLoading(true);
    try {
      await registerUser(data.username.trim(), data.password, data.email.trim());
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const status = err.response?.status;
        const detail = (err.response?.data as { detail?: string })?.detail;
        if (status) {
          setError(detail ? `Registration failed: ${detail}` : `Registration failed (status ${status}).`);
        } else {
          setError("Registration failed: unable to reach the server.");
        }
      } else {
        setError("Registration failed. Please verify your details.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4">
      <FloatingOrbs />

      <div className="relative z-10 w-full max-w-md">
        {/* Glass card */}
        <div className="glass-glow rounded-2xl p-8 animate-glass-breathe ring-1 ring-white/[0.06]">
          {/* Logo */}
          <div className="mb-8 flex flex-col items-center gap-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 text-primary animate-pulse-glow">
              <Brain className="h-7 w-7" />
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Pragma AI
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Your pragmatic AI consultant...
              </p>
            </div>
          </div>

          {/* Tab switcher */}
          <div className="mb-6 flex rounded-xl glass-subtle p-1">
            <button
              onClick={() => { setActiveTab("signin"); setError(null); }}
              className={cn(
                "flex-1 rounded-lg py-2 text-sm font-medium transition-all",
                activeTab === "signin"
                  ? "bg-white/[0.08] text-foreground shadow-sm shadow-black/20 backdrop-blur-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Sign In
            </button>
            <button
              onClick={() => { setActiveTab("register"); setError(null); }}
              className={cn(
                "flex-1 rounded-lg py-2 text-sm font-medium transition-all",
                activeTab === "register"
                  ? "bg-white/[0.08] text-foreground shadow-sm shadow-black/20 backdrop-blur-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Register
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-4 rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {/* Sign In Form */}
          {activeTab === "signin" && (
            <form onSubmit={loginForm.handleSubmit(handleLogin)} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="login-username" className="text-sm text-foreground/80">
                  Username
                </Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="login-username"
                    placeholder="Enter your username"
                    className="pl-10 glass-input focus:border-primary/40"
                    disabled={isLoading}
                    {...loginForm.register("username")}
                  />
                </div>
                {loginForm.formState.errors.username && (
                  <p className="text-xs text-destructive">{loginForm.formState.errors.username.message}</p>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="login-password" className="text-sm text-foreground/80">
                  Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    className="pl-10 pr-10 glass-input focus:border-primary/40"
                    disabled={isLoading}
                    {...loginForm.register("password")}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {loginForm.formState.errors.password && (
                  <p className="text-xs text-destructive">{loginForm.formState.errors.password.message}</p>
                )}
              </div>

              <Button
                type="submit"
                className="mt-2 w-full bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  "Sign In"
                )}
              </Button>
            </form>
          )}

          {/* Register Form */}
          {activeTab === "register" && (
            <form onSubmit={registerForm.handleSubmit(handleRegister)} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="reg-username" className="text-sm text-foreground/80">
                  Username
                </Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="reg-username"
                    placeholder="Choose a username"
                    className="pl-10 glass-input focus:border-primary/40"
                    disabled={isLoading}
                    {...registerForm.register("username")}
                  />
                </div>
                {registerForm.formState.errors.username && (
                  <p className="text-xs text-destructive">{registerForm.formState.errors.username.message}</p>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="reg-email" className="text-sm text-foreground/80">
                  Email
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="reg-email"
                    type="email"
                    placeholder="you@company.com"
                    className="pl-10 glass-input focus:border-primary/40"
                    disabled={isLoading}
                    {...registerForm.register("email")}
                  />
                </div>
                {registerForm.formState.errors.email && (
                  <p className="text-xs text-destructive">{registerForm.formState.errors.email.message}</p>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="reg-password" className="text-sm text-foreground/80">
                  Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="reg-password"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Create a password (min 6 chars)"
                    className="pl-10 pr-10 glass-input focus:border-primary/40"
                    disabled={isLoading}
                    {...registerForm.register("password")}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {registerForm.formState.errors.password && (
                  <p className="text-xs text-destructive">{registerForm.formState.errors.password.message}</p>
                )}
              </div>

              <Button
                type="submit"
                className="mt-2 w-full bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  "Create Account"
                )}
              </Button>
            </form>
          )}

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-xs text-muted-foreground/60">
              Pragma AI · Powered by Claude
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
