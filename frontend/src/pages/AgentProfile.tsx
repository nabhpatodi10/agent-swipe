import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  BadgeCheck,
  ExternalLink,
  Github,
  Globe,
  Heart,
  Key,
  Plus,
  Pencil,
  Send,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  X,
} from "lucide-react";
import { apiRequest } from "../lib/api";
import type {
  Agent,
  AgentCredential,
  AgentCredentialSecret,
  DemoChatResponse,
  FollowEdge,
  User,
  VerificationRequest,
} from "../lib/types";
import { cn, categoryColor, formatDate, pricingLabel } from "../lib/utils";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import { PageSpinner, Spinner } from "../components/ui/Spinner";

export function AgentProfile() {
  const { slug } = useParams<{ slug: string }>();
  const queryClient = useQueryClient();

  const { data: agent, isLoading: agentLoading } = useQuery({
    queryKey: ["agent", slug],
    queryFn: () => apiRequest<Agent>(`/agents/${slug}`),
    enabled: !!slug,
  });

  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiRequest<User>("/users/me"),
  });

  const isOwner = !!(agent && user && agent.owner_user_id === user.id);

  if (agentLoading) return <PageSpinner />;
  if (!agent) return <p className="py-20 text-center text-text-muted">Agent not found.</p>;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* Hero */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <div className="flex flex-wrap items-start gap-4">
          <div className="flex-1">
            <h1 className="gradient-text text-4xl font-extrabold">{agent.name}</h1>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span
                className={cn(
                  "inline-block rounded-full bg-gradient-to-r px-3 py-0.5 text-xs font-semibold text-white",
                  categoryColor(agent.category)
                )}
              >
                {agent.category}
              </span>

              {agent.verification_status === "verified" && (
                <span className="inline-flex items-center gap-1 text-brown">
                  <BadgeCheck className="h-5 w-5 animate-pulse-ring" />
                  <span className="text-xs font-medium">Verified</span>
                </span>
              )}

              <Badge variant={agent.pricing_model === "free" ? "success" : agent.pricing_model === "paid" ? "warning" : "accent"}>
                {pricingLabel(agent.pricing_model)}
              </Badge>
            </div>

            <p className="mt-4 text-text-secondary">{agent.description}</p>

            {/* Skills */}
            {agent.skills.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {agent.skills.map((s) => (
                  <Badge key={s} variant="outline">
                    {s}
                  </Badge>
                ))}
              </div>
            )}

            {/* Links */}
            <div className="mt-4 flex gap-3">
              {agent.github_url && (
                <a
                  href={agent.github_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-text-muted transition hover:text-accent-light"
                >
                  <Github className="h-4 w-4" /> GitHub
                </a>
              )}
              {agent.website_url && (
                <a
                  href={agent.website_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-text-muted transition hover:text-accent-light"
                >
                  <Globe className="h-4 w-4" /> Website
                </a>
              )}
            </div>

            {agent.free_tier_available && agent.free_tier_notes && (
              <p className="mt-3 text-sm text-success">
                Free tier: {agent.free_tier_notes}
              </p>
            )}
          </div>
        </div>
      </motion.section>

      {/* Owner sections */}
      {isOwner && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="space-y-6"
        >
          <EditAgentSection agent={agent} />
          <CredentialsSection agentId={agent.id} />
          <VerificationSection agentId={agent.id} />
        </motion.div>
      )}

      {/* Non-owner actions */}
      {!isOwner && user && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="space-y-6"
        >
          <FollowButton agentId={agent.id} />
          <SwipeButtons agentId={agent.id} />
        </motion.div>
      )}

      {/* Demo chat */}
      {agent.request_url && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="mt-8"
        >
          <DemoChat agentId={agent.id} />
        </motion.div>
      )}
    </div>
  );
}

/* ---------- Sub-components ---------- */

function EditAgentSection({ agent }: { agent: Agent }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: agent.name,
    description: agent.description,
    skills: agent.skills.join(", "),
    category: agent.category,
    github_url: agent.github_url ?? "",
    website_url: agent.website_url ?? "",
    request_url: agent.request_url ?? "",
    pricing_model: agent.pricing_model,
    free_tier_available: agent.free_tier_available,
    free_tier_notes: agent.free_tier_notes ?? "",
    is_public: agent.is_public,
    is_active: agent.is_active,
  });

  function update(field: string, value: string | boolean) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  const saveMut = useMutation({
    mutationFn: () =>
      apiRequest<Agent>(`/agents/${agent.id}`, {
        method: "PATCH",
        body: {
          name: form.name,
          description: form.description,
          skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
          category: form.category,
          github_url: form.github_url || null,
          website_url: form.website_url || null,
          request_url: form.request_url || null,
          pricing_model: form.pricing_model,
          free_tier_available: form.free_tier_available,
          free_tier_notes: form.free_tier_notes || null,
          is_public: form.is_public,
          is_active: form.is_active,
        },
      }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["agent", agent.slug] });
      queryClient.invalidateQueries({ queryKey: ["agent", updated.slug] });
      queryClient.invalidateQueries({ queryKey: ["my-agents"] });
      setOpen(false);
    },
  });

  return (
    <>
      <Button variant="outline" onClick={() => setOpen(true)}>
        <Pencil className="mr-1.5 h-4 w-4" /> Edit Agent
      </Button>

      <Modal open={open} onClose={() => setOpen(false)} title="Edit Agent" className="max-w-2xl">
        <form
          onSubmit={(e) => { e.preventDefault(); saveMut.mutate(); }}
          className="space-y-4"
        >
          <Input label="Name" value={form.name} onChange={(e) => update("name", e.target.value)} required />
          <Textarea label="Description" value={form.description} onChange={(e) => update("description", e.target.value)} rows={3} required />
          <Input label="Skills (comma-separated)" value={form.skills} onChange={(e) => update("skills", e.target.value)} required />
          <Input label="Category" value={form.category} onChange={(e) => update("category", e.target.value)} required />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="GitHub URL" value={form.github_url} onChange={(e) => update("github_url", e.target.value)} />
            <Input label="Website URL" value={form.website_url} onChange={(e) => update("website_url", e.target.value)} />
          </div>
          <Input label="Request URL (for demo)" value={form.request_url} onChange={(e) => update("request_url", e.target.value)} />

          <div className="flex flex-wrap items-center gap-4">
            <label className="text-sm font-medium text-text-secondary">Pricing</label>
            <div className="flex gap-2">
              {(["free", "freemium", "paid"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => update("pricing_model", p)}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-xs font-medium border transition-all cursor-pointer",
                    form.pricing_model === p
                      ? "bg-accent text-white border-accent"
                      : "bg-surface-100 text-text-secondary border-border hover:border-accent/50"
                  )}
                >
                  {pricingLabel(p)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-6">
            <label className="inline-flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={form.free_tier_available}
                onChange={(e) => update("free_tier_available", e.target.checked)}
                className="accent-accent"
              />
              Free tier available
            </label>
            <label className="inline-flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_public}
                onChange={(e) => update("is_public", e.target.checked)}
                className="accent-accent"
              />
              Public
            </label>
            <label className="inline-flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => update("is_active", e.target.checked)}
                className="accent-accent"
              />
              Active
            </label>
          </div>

          {form.free_tier_available && (
            <Input label="Free tier notes" value={form.free_tier_notes} onChange={(e) => update("free_tier_notes", e.target.value)} />
          )}

          {saveMut.isError && (
            <p className="text-sm text-danger">{(saveMut.error as Error).message}</p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" type="button" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saveMut.isPending}>Save Changes</Button>
          </div>
        </form>
      </Modal>
    </>
  );
}

function CredentialsSection({ agentId }: { agentId: string }) {
  const queryClient = useQueryClient();
  const [newLabel, setNewLabel] = useState("");
  const [newSecret, setNewSecret] = useState<AgentCredentialSecret | null>(null);

  const { data: creds } = useQuery({
    queryKey: ["credentials", agentId],
    queryFn: () => apiRequest<AgentCredential[]>(`/agents/${agentId}/credentials`),
  });

  const createMut = useMutation({
    mutationFn: () =>
      apiRequest<AgentCredentialSecret>(`/agents/${agentId}/credentials`, {
        method: "POST",
        body: { label: newLabel || null },
      }),
    onSuccess: (data) => {
      setNewSecret(data);
      setNewLabel("");
      queryClient.invalidateQueries({ queryKey: ["credentials", agentId] });
    },
  });

  const revokeMut = useMutation({
    mutationFn: (credId: string) =>
      apiRequest(`/agents/${agentId}/credentials/${credId}`, { method: "DELETE" }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["credentials", agentId] }),
  });

  return (
    <Card>
      <CardHeader>
        <h2 className="flex items-center gap-2 text-lg font-semibold text-text-primary">
          <Key className="h-5 w-5 text-accent" /> Manage Credentials
        </h2>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* New secret display */}
        {newSecret && (
          <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm">
            <p className="font-medium text-warning">Save this secret now -- it will not be shown again.</p>
            <code className="mt-1 block break-all text-text-primary">{newSecret.secret}</code>
            <Button variant="ghost" size="sm" className="mt-2" onClick={() => setNewSecret(null)}>
              Dismiss
            </Button>
          </div>
        )}

        {/* Create form */}
        <div className="flex items-end gap-2">
          <Input
            label="Label (optional)"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            placeholder="e.g. production"
          />
          <Button variant="primary" size="sm" onClick={() => createMut.mutate()} disabled={createMut.isPending}>
            <Plus className="mr-1 h-4 w-4" /> Create
          </Button>
        </div>

        {/* List */}
        {creds?.map((c) => (
          <div
            key={c.id}
            className="flex items-center justify-between rounded-lg bg-surface-100 px-3 py-2 text-sm"
          >
            <div>
              <span className="font-mono text-text-primary">{c.key_id}</span>
              {c.label && <span className="ml-2 text-text-muted">({c.label})</span>}
              {!c.is_active && <Badge variant="danger" className="ml-2">Revoked</Badge>}
            </div>
            {c.is_active && (
              <button
                onClick={() => revokeMut.mutate(c.id)}
                className="rounded p-1 text-text-muted hover:bg-danger/20 hover:text-danger"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function VerificationSection({ agentId }: { agentId: string }) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");

  const { data: requests } = useQuery({
    queryKey: ["verification", agentId],
    queryFn: () =>
      apiRequest<VerificationRequest[]>(`/agents/${agentId}/verification-requests`),
  });

  const submitMut = useMutation({
    mutationFn: () =>
      apiRequest(`/agents/${agentId}/verification-requests`, {
        method: "POST",
        body: { evidence_note: note },
      }),
    onSuccess: () => {
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["verification", agentId] });
    },
  });

  return (
    <Card>
      <CardHeader>
        <h2 className="flex items-center gap-2 text-lg font-semibold text-text-primary">
          <ShieldCheck className="h-5 w-5 text-brown" /> Verification
        </h2>
      </CardHeader>
      <CardContent className="space-y-4">
        {requests?.map((r) => (
          <div key={r.id} className="rounded-lg bg-surface-100 px-3 py-2 text-sm">
            <div className="flex items-center justify-between">
              <Badge
                variant={
                  r.status === "approved"
                    ? "success"
                    : r.status === "rejected"
                    ? "danger"
                    : "warning"
                }
              >
                {r.status}
              </Badge>
              <span className="text-text-muted">{formatDate(r.created_at)}</span>
            </div>
            {r.evidence_note && (
              <p className="mt-1 text-text-secondary">{r.evidence_note}</p>
            )}
            {r.rejection_reason && (
              <p className="mt-1 text-danger">{r.rejection_reason}</p>
            )}
          </div>
        ))}

        <div className="space-y-2">
          <Textarea
            label="Evidence note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Why should this agent be verified?"
            rows={3}
          />
          <Button
            variant="primary"
            size="sm"
            onClick={() => submitMut.mutate()}
            disabled={submitMut.isPending || !note.trim()}
          >
            Submit Verification Request
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function FollowButton({ agentId }: { agentId: string }) {
  const queryClient = useQueryClient();
  const followBody = { target_type: "agent" as const, target_agent_id: agentId };

  const { data: following } = useQuery({
    queryKey: ["following"],
    queryFn: () => apiRequest<FollowEdge[]>("/me/following"),
  });

  const isFollowing = following?.some(
    (f) => f.target_type === "agent" && f.target_agent_id === agentId
  );

  const followMut = useMutation({
    mutationFn: () =>
      apiRequest("/follows", { method: "POST", body: followBody }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["following"] }),
  });

  const unfollowMut = useMutation({
    mutationFn: () =>
      apiRequest("/follows", { method: "DELETE", body: followBody }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["following"] }),
  });

  const pending = followMut.isPending || unfollowMut.isPending;

  return (
    <Button
      variant={isFollowing ? "outline" : "primary"}
      onClick={() => (isFollowing ? unfollowMut.mutate() : followMut.mutate())}
      disabled={pending}
    >
      {isFollowing ? (
        <><X className="mr-1.5 h-4 w-4" /> Unfollow</>
      ) : (
        <><Heart className="mr-1.5 h-4 w-4" /> Follow</>
      )}
    </Button>
  );
}

function SwipeButtons({ agentId }: { agentId: string }) {
  const queryClient = useQueryClient();

  const { data: likedAgents } = useQuery({
    queryKey: ["liked-agents"],
    queryFn: () => apiRequest<{ id: string }[]>("/me/liked-agents"),
  });

  const isLiked = likedAgents?.some((a) => a.id === agentId);

  const swipeMut = useMutation({
    mutationFn: (decision: "left" | "right") =>
      apiRequest("/swipe/decision", {
        method: "POST",
        body: { agent_id: agentId, decision },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["liked-agents"] });
      queryClient.invalidateQueries({ queryKey: ["swipe-agents"] });
    },
  });

  return (
    <div className="flex gap-3">
      <Button
        variant={isLiked === false || isLiked === undefined ? "danger" : "outline"}
        onClick={() => swipeMut.mutate("left")}
        disabled={swipeMut.isPending}
      >
        <ThumbsDown className="mr-1.5 h-4 w-4" />
        {isLiked === false ? "Passed" : "Pass"}
      </Button>
      <Button
        variant={isLiked ? "secondary" : "primary"}
        onClick={() => swipeMut.mutate("right")}
        disabled={swipeMut.isPending}
        className={isLiked ? "" : "glow-sm"}
      >
        <ThumbsUp className="mr-1.5 h-4 w-4" />
        {isLiked ? "Liked" : "Like"}
      </Button>
    </div>
  );
}

function DemoChat({ agentId }: { agentId: string }) {
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<{ role: "user" | "agent"; text: string }[]>([]);

  const sendMut = useMutation({
    mutationFn: (msg: string) =>
      apiRequest<DemoChatResponse>(`/agents/${agentId}/demo`, {
        method: "POST",
        body: { message: msg },
      }),
    onSuccess: (data, msg) => {
      setHistory((h) => [
        ...h,
        { role: "user", text: msg },
        { role: "agent", text: data.reply },
      ]);
      setMessage("");
    },
  });

  return (
    <Card glow>
      <CardHeader>
        <h2 className="text-lg font-semibold text-text-primary">Demo Chat</h2>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="max-h-64 space-y-2 overflow-y-auto rounded-lg bg-surface-100 p-3">
          {history.length === 0 && (
            <p className="text-sm text-text-muted">Send a message to try out this agent.</p>
          )}
          {history.map((m, i) => (
            <div
              key={i}
              className={cn(
                "rounded-lg px-3 py-2 text-sm",
                m.role === "user"
                  ? "ml-auto max-w-[70%] bg-accent/20 text-text-primary"
                  : "mr-auto max-w-[70%] bg-surface-200 text-text-secondary"
              )}
            >
              {m.text}
            </div>
          ))}
          {sendMut.isPending && (
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Spinner size="sm" /> Thinking...
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (message.trim()) sendMut.mutate(message.trim());
          }}
          className="flex gap-2"
        >
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1"
          />
          <Button
            variant="primary"
            type="submit"
            disabled={sendMut.isPending || !message.trim()}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
