import { useState, useEffect, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Sparkles, User, MapPin, Globe, Tag } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { apiRequest } from "../lib/api";
import type { Profile } from "../lib/types";

export function Onboarding() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: profile, isLoading } = useQuery<Profile>({
    queryKey: ["profile"],
    queryFn: () => apiRequest<Profile>("/me/profile"),
  });

  const [form, setForm] = useState({
    display_name: "",
    bio: "",
    avatar_url: "",
    location: "",
    website_url: "",
    interests: "",
  });

  useEffect(() => {
    if (profile) {
      setForm({
        display_name: profile.display_name ?? "",
        bio: profile.bio ?? "",
        avatar_url: profile.avatar_url ?? "",
        location: profile.location ?? "",
        website_url: profile.website_url ?? "",
        interests: (profile.interests ?? []).join(", "),
      });
    }
  }, [profile]);

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload = {
        ...form,
        interests: form.interests
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      };
      await apiRequest("/me/profile", { method: "PATCH", body: payload });
      await apiRequest("/me/onboarding/complete", { method: "POST" });
      navigate("/dashboard");
    } catch (err: any) {
      setError(err?.message ?? "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        {/* Header */}
        <div className="mb-10 text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/15 glow-sm"
          >
            <Sparkles className="h-8 w-8 text-accent" />
          </motion.div>
          <h1 className="text-3xl font-bold gradient-text">Welcome to AgentSwipe</h1>
          <p className="mt-2 text-text-secondary">Let&apos;s set up your profile so agents can find you.</p>
        </div>

        {/* Progress bar */}
        <div className="mb-8 h-1.5 overflow-hidden rounded-full bg-surface-200">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-accent to-brown"
            initial={{ width: "10%" }}
            animate={{ width: "50%" }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>

        {error && (
          <div className="mb-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        <motion.form
          onSubmit={handleSubmit}
          className="glass rounded-2xl p-8 space-y-6"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
        >
          <div className="space-y-1.5">
            <label className="flex items-center gap-2 text-sm font-medium text-text-secondary">
              <User className="h-4 w-4" /> Display Name
            </label>
            <Input
              placeholder="How should we call you?"
              value={form.display_name}
              onChange={(e) => update("display_name", e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-text-secondary">Bio</label>
            <Textarea
              placeholder="Tell us a bit about yourself..."
              value={form.bio}
              onChange={(e) => update("bio", e.target.value)}
              rows={3}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-text-secondary">Avatar URL</label>
            <Input
              type="url"
              placeholder="https://example.com/avatar.png"
              value={form.avatar_url}
              onChange={(e) => update("avatar_url", e.target.value)}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                <MapPin className="h-4 w-4" /> Location
              </label>
              <Input
                placeholder="City, Country"
                value={form.location}
                onChange={(e) => update("location", e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <label className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                <Globe className="h-4 w-4" /> Website
              </label>
              <Input
                type="url"
                placeholder="https://yoursite.com"
                value={form.website_url}
                onChange={(e) => update("website_url", e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="flex items-center gap-2 text-sm font-medium text-text-secondary">
              <Tag className="h-4 w-4" /> Interests
            </label>
            <Input
              placeholder="AI, automation, productivity (comma-separated)"
              value={form.interests}
              onChange={(e) => update("interests", e.target.value)}
            />
            <p className="text-xs text-text-muted">Separate interests with commas</p>
          </div>

          <Button type="submit" className="w-full glow-sm" disabled={saving}>
            {saving ? "Saving..." : "Complete Setup"}
          </Button>
        </motion.form>
      </motion.div>
    </div>
  );
}
