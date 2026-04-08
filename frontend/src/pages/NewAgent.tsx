import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bot, Code, DollarSign, Globe, Info, Sparkles } from "lucide-react";
import { apiRequest } from "../lib/api";
import type { Agent } from "../lib/types";
import { cn } from "../lib/utils";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Card, CardHeader, CardContent } from "../components/ui/Card";

type PricingModel = "free" | "freemium" | "paid";

export function NewAgent() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [skills, setSkills] = useState("");
  const [category, setCategory] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [requestUrl, setRequestUrl] = useState("");
  const [pricingModel, setPricingModel] = useState<PricingModel>("free");
  const [freeTierAvailable, setFreeTierAvailable] = useState(false);
  const [freeTierNotes, setFreeTierNotes] = useState("");

  const createMut = useMutation({
    mutationFn: () =>
      apiRequest<Agent>("/agents", {
        method: "POST",
        body: {
          name,
          description,
          skills: skills
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          category,
          github_url: githubUrl || null,
          website_url: websiteUrl || null,
          request_url: requestUrl || null,
          pricing_model: pricingModel,
          free_tier_available: freeTierAvailable,
          free_tier_notes: freeTierNotes || null,
        },
      }),
    onSuccess: (agent) => navigate(`/agents/${agent.slug}`),
  });

  const pricingOptions: { value: PricingModel; label: string; icon: typeof DollarSign }[] = [
    { value: "free", label: "Free", icon: Sparkles },
    { value: "freemium", label: "Freemium", icon: Info },
    { value: "paid", label: "Paid", icon: DollarSign },
  ];

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="gradient-text mb-8 text-3xl font-extrabold"
      >
        Create New Agent
      </motion.h1>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          createMut.mutate();
        }}
        className="space-y-6"
      >
        {/* Basic Info */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardHeader>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-text-primary">
                <Bot className="h-5 w-5 text-accent" /> Basic Information
              </h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My awesome agent"
                required
              />
              <Textarea
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What does your agent do?"
                rows={4}
                required
              />
              <Input
                label="Category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. productivity, coding, research"
                required
              />
              <Input
                label="Skills (comma-separated)"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                placeholder="NLP, code generation, data analysis"
              />
            </CardContent>
          </Card>
        </motion.div>

        {/* Links */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardHeader>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-text-primary">
                <Globe className="h-5 w-5 text-accent" /> Links
              </h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="GitHub URL"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/..."
              />
              <Input
                label="Website URL"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://..."
              />
              <Input
                label="Request URL (enables demo chat)"
                value={requestUrl}
                onChange={(e) => setRequestUrl(e.target.value)}
                placeholder="https://api.example.com/chat"
              />
            </CardContent>
          </Card>
        </motion.div>

        {/* Pricing */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card>
            <CardHeader>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-text-primary">
                <DollarSign className="h-5 w-5 text-accent" /> Pricing
              </h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-text-secondary">
                  Pricing Model
                </label>
                <div className="flex gap-2">
                  {pricingOptions.map((opt) => {
                    const Icon = opt.icon;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setPricingModel(opt.value)}
                        className={cn(
                          "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition",
                          pricingModel === opt.value
                            ? "border-accent bg-accent/20 text-accent-light"
                            : "border-border bg-surface-100 text-text-secondary hover:border-border-light"
                        )}
                      >
                        <Icon className="h-4 w-4" />
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <label className="flex items-center gap-3 text-sm text-text-secondary">
                <input
                  type="checkbox"
                  checked={freeTierAvailable}
                  onChange={(e) => setFreeTierAvailable(e.target.checked)}
                  className="h-4 w-4 rounded border-border bg-surface-100 accent-accent"
                />
                Free tier available
              </label>

              {freeTierAvailable && (
                <Input
                  label="Free Tier Notes"
                  value={freeTierNotes}
                  onChange={(e) => setFreeTierNotes(e.target.value)}
                  placeholder="e.g. 100 requests/month free"
                />
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Submit */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex justify-end gap-3"
        >
          <Button variant="ghost" type="button" onClick={() => navigate(-1)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={createMut.isPending || !name.trim() || !description.trim() || !category.trim()}
            className="glow-sm"
          >
            {createMut.isPending ? "Creating..." : "Create Agent"}
          </Button>
        </motion.div>

        {createMut.isError && (
          <p className="text-sm text-danger">{(createMut.error as Error).message}</p>
        )}
      </form>
    </div>
  );
}
