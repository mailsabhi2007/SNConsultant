import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Loader2, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { animations } from "@/lib/animations";
import { gradients, patterns, shadows } from "@/lib/visualEffects";
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

export function LoginPage() {
  const { login, register: registerUser } = useAuth();
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
    <div className={cn("relative flex min-h-screen items-center justify-center overflow-hidden p-4", gradients.subtlePrimary)}>
      {/* Animated background pattern */}
      <div className={cn("absolute inset-0 opacity-40", patterns.mesh)} />
      <div className={cn("absolute inset-0 opacity-20", patterns.dots)} />

      {/* Floating gradient orb */}
      <motion.div
        className={cn("absolute -top-32 -left-32 h-96 w-96 rounded-full blur-3xl opacity-20", gradients.mesh)}
        animate={{
          y: [0, -20, 0],
          x: [0, 20, 0],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      <motion.div
        {...animations.fadeInScale}
        className="w-full max-w-md relative z-10"
      >
        <Card className={cn("border-border/50 backdrop-blur-xl bg-background/80", shadows.medium)}>
          <CardHeader className="space-y-4 text-center">
            <motion.div
              className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10"
              whileHover={{ scale: 1.1, rotate: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <Bot className="h-6 w-6 text-primary" />
            </motion.div>
            <div>
              <CardTitle className="text-2xl">Welcome back</CardTitle>
              <CardDescription className="mt-1">
                Sign in to continue your ServiceNow consulting workflow.
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent>
            <Tabs defaultValue="login" className="w-full" onValueChange={() => setError(null)}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="register">Register</TabsTrigger>
              </TabsList>

              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mt-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive"
                >
                  {error}
                </motion.div>
              )}

              <TabsContent value="login" className="mt-4">
                <form onSubmit={loginForm.handleSubmit(handleLogin)} className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="login-username" className="text-sm font-medium">
                      Username
                    </label>
                    <Input
                      id="login-username"
                      placeholder="Enter your username"
                      {...loginForm.register("username")}
                    />
                    {loginForm.formState.errors.username && (
                      <p className="text-xs text-destructive">
                        {loginForm.formState.errors.username.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="login-password" className="text-sm font-medium">
                      Password
                    </label>
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="Enter your password"
                      {...loginForm.register("password")}
                    />
                    {loginForm.formState.errors.password && (
                      <p className="text-xs text-destructive">
                        {loginForm.formState.errors.password.message}
                      </p>
                    )}
                  </div>

                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                    <Button type="submit" className="w-full" disabled={isLoading}>
                      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Sign In
                    </Button>
                  </motion.div>

                  <p className="text-center text-xs text-muted-foreground">
                    Your session stays active for 30 minutes.
                  </p>
                </form>
              </TabsContent>

              <TabsContent value="register" className="mt-4">
                <form onSubmit={registerForm.handleSubmit(handleRegister)} className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="register-username" className="text-sm font-medium">
                      Username
                    </label>
                    <Input
                      id="register-username"
                      placeholder="Choose a username"
                      {...registerForm.register("username")}
                    />
                    {registerForm.formState.errors.username && (
                      <p className="text-xs text-destructive">
                        {registerForm.formState.errors.username.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="register-email" className="text-sm font-medium">
                      Email
                    </label>
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="Enter your email"
                      {...registerForm.register("email")}
                    />
                    {registerForm.formState.errors.email && (
                      <p className="text-xs text-destructive">
                        {registerForm.formState.errors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="register-password" className="text-sm font-medium">
                      Password
                    </label>
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="Create a password"
                      {...registerForm.register("password")}
                    />
                    <p className="text-xs text-muted-foreground">Minimum 6 characters</p>
                    {registerForm.formState.errors.password && (
                      <p className="text-xs text-destructive">
                        {registerForm.formState.errors.password.message}
                      </p>
                    )}
                  </div>

                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                    <Button type="submit" className="w-full" disabled={isLoading}>
                      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Create Account
                    </Button>
                  </motion.div>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
