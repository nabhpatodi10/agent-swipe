import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bot, PlusCircle, BadgeCheck, ExternalLink, Github } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { PageSpinner } from "../components/ui/Spinner";
import { EmptyState } from "../components/ui/EmptyState";
import { apiRequest } from "../lib/api";
import type { Agent } from "../lib/types";
import { formatDate, pricingLabel, categoryColor } from "../lib/utils";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export function MyAgents() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ["my-agents"],
    queryFn: () => apiRequest<Agent[]>("/agents/mine"),
  });

  if (isLoading) return <PageSpinner />;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Your Agents</h1>
          <p className="text-text-muted mt-1">
            Manage the AI agents you&apos;ve created
          </p>
        </div>
        <Link to="/agents/new">
          <Button>
            <PlusCircle size={16} />
            New Agent
          </Button>
        </Link>
      </div>

      {/* Agent list */}
      {!agents || agents.length === 0 ? (
        <EmptyState
          icon={Bot}
          title="No agents yet"
          description="Create your first AI agent and share it with the community."
        >
          <Link to="/agents/new">
            <Button>
              <PlusCircle size={16} />
              Create Agent
            </Button>
          </Link>
        </EmptyState>
      ) : (
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          {agents.map((agent) => (
            <motion.div variants={item} key={agent.id}>
              <Link to={`/agents/${agent.slug}`}>
                <Card hover glow className="glass group">
                  <CardContent className="space-y-3">
                    {/* Top row: category strip */}
                    <div className="flex items-center justify-between">
                      <Badge
                        className={`bg-gradient-to-r ${categoryColor(agent.category)} text-white text-[10px]`}
                      >
                        {agent.category}
                      </Badge>
                      <div className="flex items-center gap-2">
                        {agent.verification_status === "verified" && (
                          <span className="flex items-center gap-1 text-xs text-accent animate-pulse-ring rounded-full">
                            <BadgeCheck size={14} />
                            Verified
                          </span>
                        )}
                        <Badge variant={agent.is_active ? "success" : "danger"}>
                          {agent.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </div>
                    </div>

                    {/* Name & description */}
                    <div>
                      <h3 className="text-lg font-semibold text-text-primary group-hover:text-accent transition-colors">
                        {agent.name}
                      </h3>
                      <p className="text-sm text-text-muted mt-1 line-clamp-2">
                        {agent.description}
                      </p>
                    </div>

                    {/* Skills */}
                    <div className="flex flex-wrap gap-1.5">
                      {agent.skills.slice(0, 4).map((skill) => (
                        <Badge key={skill} variant="outline" className="text-[10px]">
                          {skill}
                        </Badge>
                      ))}
                      {agent.skills.length > 4 && (
                        <Badge variant="outline" className="text-[10px]">
                          +{agent.skills.length - 4}
                        </Badge>
                      )}
                    </div>

                    {/* Footer: pricing, links, date */}
                    <div className="flex items-center justify-between pt-2 border-t border-border/50">
                      <div className="flex items-center gap-3">
                        <Badge variant="accent" className="text-[10px]">
                          {pricingLabel(agent.pricing_model)}
                        </Badge>
                        {agent.github_url && (
                          <Github size={14} className="text-text-muted" />
                        )}
                        {agent.website_url && (
                          <ExternalLink size={14} className="text-text-muted" />
                        )}
                        {!agent.is_public && (
                          <Badge variant="warning" className="text-[10px]">
                            Private
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-text-muted">
                        {formatDate(agent.created_at)}
                      </span>
                    </div>
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
