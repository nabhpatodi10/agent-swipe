import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Heart, BadgeCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { PageSpinner } from "../components/ui/Spinner";
import { EmptyState } from "../components/ui/EmptyState";
import { apiRequest } from "../lib/api";
import type { AgentSummary } from "../lib/types";
import { categoryColor, truncate } from "../lib/utils";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export function Liked() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ["liked-agents"],
    queryFn: () => apiRequest<AgentSummary[]>("/me/liked-agents"),
  });

  if (isLoading) return <PageSpinner />;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Liked Agents</h1>
        <p className="text-text-muted text-sm mt-1">Agents you swiped right on</p>
      </div>

      {!agents || agents.length === 0 ? (
        <EmptyState
          icon={Heart}
          title="No liked agents yet"
          description="Start swiping to discover AI agents you love."
        >
          <Link to="/swipe">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors"
            >
              Start Swiping
            </motion.button>
          </Link>
        </EmptyState>
      ) : (
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {agents.map((agent) => (
            <motion.div variants={item} key={agent.id}>
              <Link to={`/agents/${agent.slug}`}>
                <Card hover glow className="glass h-full">
                  <div className={`h-1.5 bg-gradient-to-r ${categoryColor(agent.category)}`} />
                  <CardContent className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-text-primary">{agent.name}</span>
                      {agent.verification_status === "verified" && (
                        <BadgeCheck size={15} className="text-brown" />
                      )}
                    </div>
                    <Badge
                      className={`bg-gradient-to-r ${categoryColor(agent.category)} text-white text-[10px]`}
                    >
                      {agent.category}
                    </Badge>
                    <p className="text-text-secondary text-sm">
                      {truncate(agent.description, 120)}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
