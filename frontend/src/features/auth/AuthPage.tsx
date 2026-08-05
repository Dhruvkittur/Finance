/**
 * FinPilot AI — Authentication Page
 * ====================================
 * Login + Registration with animated transitions.
 * Premium glassmorphism UI with gradient background.
 */

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Bot, TrendingUp, Shield, Zap, ArrowRight, Loader2, Mail, Lock, User, Building2 } from "lucide-react";

import { authAPI } from "@/lib/api";
import { setUser } from "@/app/slices/authSlice";

// ── Zod Schemas ────────────────────────────────────────────────────────────────

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

const registerSchema = z.object({
  email: z.string().email("Enter a valid email"),
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  organization: z.string().optional(),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirmPassword: z.string(),
}).refine((d) => d.password === d.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type LoginForm = z.infer<typeof loginSchema>;
type RegisterForm = z.infer<typeof registerSchema>;

// ── Feature List ───────────────────────────────────────────────────────────────

const FEATURES = [
  { icon: Bot, label: "17 Autonomous AI Agents", color: "text-blue-400" },
  { icon: TrendingUp, label: "Real-time Financial Analysis", color: "text-emerald-400" },
  { icon: Shield, label: "Enterprise Security & RBAC", color: "text-violet-400" },
  { icon: Zap, label: "Streaming AI Responses", color: "text-amber-400" },
];

// ── Input Field ────────────────────────────────────────────────────────────────

function InputField({
  id, label, type = "text", icon: Icon, placeholder, register, error,
}: {
  id: string; label: string; type?: string; icon: any; placeholder: string;
  register: any; error?: string;
}) {
  const [showPw, setShowPw] = useState(false);
  const actualType = type === "password" ? (showPw ? "text" : "password") : type;

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {label}
      </label>
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={15} />
        <input
          id={id}
          type={actualType}
          placeholder={placeholder}
          {...register}
          className="w-full bg-secondary border border-border rounded-lg pl-9 pr-10 py-2.5 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all"
        />
        {type === "password" && (
          <button
            type="button"
            onClick={() => setShowPw(!showPw)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
          >
            {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        )}
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs text-red-400"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
}

// ── Auth Page ──────────────────────────────────────────────────────────────────

export default function AuthPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");

  const loginForm = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });
  const registerForm = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  const handleLogin = async (data: LoginForm) => {
    setError("");
    try {
      const res = await authAPI.login(data.email, data.password);
      dispatch(setUser({
        user: res.data.user,
        accessToken: res.data.access_token,
        refreshToken: res.data.refresh_token,
      }));
      navigate("/dashboard");
    } catch (err: any) {
      let errorMessage = "Login failed. Please try again.";
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        errorMessage = detail.map((d: any) => d.msg).join(", ");
      } else if (typeof detail === "string") {
        errorMessage = detail;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    }
  };

  const handleRegister = async (data: RegisterForm) => {
    setError("");
    try {
      const res = await authAPI.register({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        organization: data.organization,
      });
      dispatch(setUser({
        user: res.data.user,
        accessToken: res.data.access_token,
        refreshToken: res.data.refresh_token,
      }));
      navigate("/dashboard");
    } catch (err: any) {
      let errorMessage = "Registration failed. Please try again.";
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        errorMessage = detail.map((d: any) => d.msg).join(", ");
      } else if (typeof detail === "string") {
        errorMessage = detail;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    }
  };

  return (
    <div className="min-h-screen bg-background flex overflow-hidden">
      {/* ── Left Panel: Branding ─────────────────────────────────────────────── */}
      <div className="hidden lg:flex flex-col w-1/2 relative overflow-hidden p-12">
        {/* Animated background blobs */}
        <div className="absolute inset-0 bg-grid opacity-30" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-blob" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-600/20 rounded-full blur-3xl animate-blob animation-delay-2000" />

        <div className="relative z-10 flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-2xl shadow-glow-md">
              🤖
            </div>
            <div>
              <div className="text-xl font-bold gradient-text">FinPilot AI</div>
              <div className="text-xs text-muted-foreground">Enterprise Platform</div>
            </div>
          </div>

          {/* Hero Text */}
          <div className="flex-1 flex flex-col justify-center">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-4xl font-bold text-foreground leading-tight mb-4"
            >
              Autonomous AI Workforce
              <br />
              <span className="gradient-text-hero">for Modern Finance</span>
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-muted-foreground text-base mb-8 leading-relaxed"
            >
              17 intelligent agents collaborate autonomously to understand financial
              documents, detect fraud, ensure compliance, and deliver executive insights—
              all in real-time.
            </motion.p>

            {/* Features */}
            <div className="space-y-3">
              {FEATURES.map((feature, i) => (
                <motion.div
                  key={feature.label}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + i * 0.1 }}
                  className="flex items-center gap-3"
                >
                  <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
                    <feature.icon size={16} className={feature.color} />
                  </div>
                  <span className="text-sm text-muted-foreground">{feature.label}</span>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Agent count badge */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="glass rounded-xl p-4 flex items-center gap-4"
          >
            <div className="flex -space-x-2">
              {["🤖","🔍","📊","⚠️","✅"].map((emoji, i) => (
                <div key={i} className="w-8 h-8 rounded-full bg-secondary border-2 border-background flex items-center justify-center text-sm">
                  {emoji}
                </div>
              ))}
            </div>
            <div>
              <div className="text-sm font-semibold text-foreground">17 AI Agents Ready</div>
              <div className="text-xs text-muted-foreground">Processing your documents intelligently</div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* ── Right Panel: Auth Form ────────────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-xl">🤖</div>
            <div className="font-bold text-lg gradient-text">FinPilot AI</div>
          </div>

          {/* Tab Toggle */}
          <div className="flex bg-secondary rounded-xl p-1 mb-8 border border-border">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(""); }}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  mode === m
                    ? "bg-primary text-primary-foreground shadow-glow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {m === "login" ? "Sign In" : "Create Account"}
              </button>
            ))}
          </div>

          {/* Form Header */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground">
              {mode === "login" ? "Welcome back" : "Get started"}
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {mode === "login"
                ? "Sign in to your FinPilot AI account"
                : "Create your enterprise account"}
            </p>
          </div>

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Forms */}
          <AnimatePresence mode="wait">
            {mode === "login" ? (
              <motion.form
                key="login"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                onSubmit={loginForm.handleSubmit(handleLogin)}
                className="space-y-4"
              >
                <InputField id="login-email" label="Email" icon={Mail} placeholder="you@company.com"
                  register={loginForm.register("email")} error={loginForm.formState.errors.email?.message} />
                <InputField id="login-password" label="Password" type="password" icon={Lock} placeholder="••••••••"
                  register={loginForm.register("password")} error={loginForm.formState.errors.password?.message} />

                <button
                  type="submit"
                  disabled={loginForm.formState.isSubmitting}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg font-medium text-sm transition-all shadow-glow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loginForm.formState.isSubmitting ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <> Sign In <ArrowRight size={14} /> </>
                  )}
                </button>

                {/* Demo credentials hint */}
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">
                    Demo: <span className="text-primary">demo@finpilot.ai</span> / <span className="text-primary">Demo@FinPilot2024</span>
                  </p>
                </div>
              </motion.form>
            ) : (
              <motion.form
                key="register"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                onSubmit={registerForm.handleSubmit(handleRegister)}
                className="space-y-4"
              >
                <InputField id="reg-name" label="Full Name" icon={User} placeholder="Jane Smith"
                  register={registerForm.register("full_name")} error={registerForm.formState.errors.full_name?.message} />
                <InputField id="reg-email" label="Work Email" icon={Mail} placeholder="you@company.com"
                  register={registerForm.register("email")} error={registerForm.formState.errors.email?.message} />
                <InputField id="reg-org" label="Organization (optional)" icon={Building2} placeholder="Acme Corp"
                  register={registerForm.register("organization")} />
                <InputField id="reg-password" label="Password" type="password" icon={Lock} placeholder="Min 8 characters"
                  register={registerForm.register("password")} error={registerForm.formState.errors.password?.message} />
                <InputField id="reg-confirm" label="Confirm Password" type="password" icon={Lock} placeholder="Repeat password"
                  register={registerForm.register("confirmPassword")} error={registerForm.formState.errors.confirmPassword?.message} />

                <button
                  type="submit"
                  disabled={registerForm.formState.isSubmitting}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg font-medium text-sm transition-all shadow-glow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {registerForm.formState.isSubmitting ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <> Create Account <ArrowRight size={14} /> </>
                  )}
                </button>
              </motion.form>
            )}
          </AnimatePresence>

          {/* Footer */}
          <p className="text-center text-xs text-muted-foreground mt-6">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
