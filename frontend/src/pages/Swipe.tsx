import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { ThumbsDown, ThumbsUp, BadgeCheck, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { PageSpinner } from "../components/ui/Spinner";
import { EmptyState } from "../components/ui/EmptyState";
import { apiRequest } from "../lib/api";
import type { Agent } from "../lib/types";
import { categoryColor, pricingLabel, truncate } from "../lib/utils";

export function Swipe() {
  const queryClient = useQueryClient();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [exitDirection, setExitDirection] = useState<"left" | "right" | null>(null);

  const { data: agents, isLoading } = useQuery({
    queryKey: ["swipe-agents"],
    queryFn: () => apiRequest<Agent[]>("/swipe/next?limit=10"),
  });

  const swipeMutation = useMutation({
    mutationFn: (vars: { agent_id: string; decision: "left" | "right" }) =>
      apiRequest("/swipe/decision", { method: "POST", body: vars }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["liked-agents"] });
    },
  });

  const handleSwipe = (decision: "left" | "right") => {
    const agent = agents?.[currentIndex];
    if (!agent) return;
    setExitDirection(decision);
    swipeMutation.mutate({ agent_id: agent.id, decision });
    setTimeout(() => {
      setExitDirection(null);
      setCurrentIndex((i) => i + 1);
    }, 350);
  };

  if (isLoading) return <PageSpinner />;

  const agent = agents?.[currentIndex];

  if (!agent) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          icon={Sparkles}
          title="No more agents to discover"
          description="Check back later for new AI agents, or browse your liked agents."
        >
          <Link to="/liked">
            <Button variant="outline" size="sm">View Liked Agents</Button>
          </Link>
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center max-w-lg mx-auto w-full gap-6">
      <AnimatePresence mode="wait">
        <motion.div
          key={agent.id}
          initial={{ opacity: 0, y: 40, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={
            exitDirection === "left"
              ? { x: -300, opacity: 0, rotate: -12, transition: { duration: 0.3 } }
              : exitDirection === "right"
                ? { x: 300, opacity: 0, rotate: 12, transition: { duration: 0.3 } }
                : { opacity: 0 }
          }
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
          className="w-full"
        >
          <Card className="glass glow-md overflow-hidden">
            {/* Category gradient header */}
            <div className={`h-2 bg-gradient-to-r ${categoryColor(agent.category)}`} />

            <CardContent className="p-6 space-y-5">
              {/* Category badge */}
              <div className="flex items-center justify-between">
                <Badge className={`bg-gradient-to-r ${categoryColor(agent.category)} text-white`}>
                  {agent.category}
                </Badge>
                <Badge variant={agent.pricing_model === "free" ? "success" : "warning"}>
                  {pricingLabel(agent.pricing_model)}
                </Badge>
              </div>

              {/* Name & verification */}
              <div className="flex items-center gap-2">
                <Link
                  to={`/agents/${agent.slug}`}
                  className="text-2xl font-bold text-text-primary hover:text-accent-light transition-colors"
                >
                  {agent.name}
                </Link>
                {agent.verification_status === "verified" && (
                  <BadgeCheck size={20} className="text-brown" />
                )}
              </div>

              {/* Description */}
              <p className="text-text-secondary text-sm leading-relaxed">
                {truncate(agent.description, 200)}
              </p>

              {/* Skills */}
              {agent.skills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {agent.skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </AnimatePresence>

      {/* Action buttons */}
      <div className="flex items-center gap-8">
        <button
          onClick={() => handleSwipe("left")}
          className="p-5 rounded-full bg-surface-200/80 border border-border hover:border-danger/50 hover:bg-danger/10 transition-all duration-200 group"
        >
          <ThumbsDown size={28} className="text-text-muted group-hover:text-danger transition-colors" />
        </button>
        <button
          onClick={() => handleSwipe("right")}
          className="p-5 rounded-full bg-surface-200/80 border border-border hover:border-emerald-500/50 hover:bg-emerald-500/10 transition-all duration-200 group"
        >
          <ThumbsUp size={28} className="text-text-muted group-hover:text-emerald-400 transition-colors" />
        </button>
      </div>
    </div>
  );
}
