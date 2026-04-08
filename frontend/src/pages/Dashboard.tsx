import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Heart, FolderOpen, Users, Compass, Zap, Rss, PlusCircle, BadgeCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { PageSpinner } from "../components/ui/Spinner";
import { apiRequest } from "../lib/api";
import type { Profile, AgentSummary, Collection, FollowEdge } from "../lib/types";
import { categoryColor } from "../lib/utils";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export function Dashboard() {
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => apiRequest<Profile>("/me/profile"),
  });

  const { data: likedAgents } = useQuery({
    queryKey: ["liked-agents"],
    queryFn: () => apiRequest<AgentSummary[]>("/me/liked-agents"),
  });

  const { data: collections } = useQuery({
    queryKey: ["collections"],
    queryFn: () => apiRequest<Collection[]>("/collections"),
  });

  const { data: following } = useQuery({
    queryKey: ["following"],
    queryFn: () => apiRequest<FollowEdge[]>("/me/following"),
  });

  if (profileLoading) return <PageSpinner />;

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const stats = [
    { label: "Liked Agents", value: likedAgents?.length ?? 0, icon: Heart, color: "text-accent" },
    { label: "Collections", value: collections?.length ?? 0, icon: FolderOpen, color: "text-brown" },
    { label: "Following", value: following?.length ?? 0, icon: Users, color: "text-brown-light" },
    { label: "Discover", value: null, icon: Compass, color: "text-accent-hover", link: "/swipe" },
  ];

  const quickActions = [
    { title: "Discover Agents", description: "Swipe through AI agents", icon: Zap, link: "/swipe", gradient: "from-accent to-accent-hover" },
    { title: "Browse Feed", description: "See what the community is sharing", icon: Rss, link: "/feed", gradient: "from-brown-light to-brown" },
    { title: "Create Agent", description: "Register your own AI agent", icon: PlusCircle, link: "/agents/new", gradient: "from-amber-700 to-amber-900" },
  ];

  const recentLiked = (likedAgents ?? []).slice(0, 4);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
        {/* Header */}
        <motion.div variants={item}>
          <h1 className="text-3xl font-bold gradient-text">
            Welcome back, {profile?.display_name ?? "Explorer"}
          </h1>
          <p className="text-text-muted mt-1">{today}</p>
        </motion.div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((s) => {
            const Inner = (
              <Card key={s.label} hover glow className="glass">
                <CardContent className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl bg-surface-200/60 ${s.color}`}>
                    <s.icon size={22} />
                  </div>
                  <div>
                    <p className="text-text-muted text-xs uppercase tracking-wide">{s.label}</p>
                    {s.value !== null ? (
                      <p className="text-2xl font-bold text-text-primary">{s.value}</p>
                    ) : (
                      <p className="text-sm font-medium text-accent-light">Explore &rarr;</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
            return (
              <motion.div variants={item} key={s.label}>
                {s.link ? <Link to={s.link}>{Inner}</Link> : Inner}
              </motion.div>
            );
          })}
        </div>

        {/* Quick actions */}
        <motion.div variants={item}>
          <h2 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {quickActions.map((a) => (
              <motion.div variants={item} key={a.title}>
                <Link to={a.link}>
                  <Card hover glow className="glass group">
                    <CardContent className="flex items-start gap-4">
                      <div className={`p-3 rounded-xl bg-gradient-to-br ${a.gradient} shadow-lg`}>
                        <a.icon size={20} className="text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-text-primary group-hover:text-accent-light transition-colors">
                          {a.title}
                        </p>
                        <p className="text-sm text-text-muted">{a.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Recent liked agents */}
        {recentLiked.length > 0 && (
          <motion.div variants={item}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text-primary">Recently Liked</h2>
              <Link to="/liked" className="text-sm text-accent-light hover:underline">
                View all
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {recentLiked.map((agent) => (
                <motion.div variants={item} key={agent.id}>
                  <Link to={`/agents/${agent.slug}`}>
                    <Card hover glow className="glass">
                      <CardContent>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold text-text-primary text-sm">{agent.name}</span>
                          {agent.verification_status === "verified" && (
                            <BadgeCheck size={14} className="text-brown" />
                          )}
                        </div>
                        <Badge
                          className={`bg-gradient-to-r ${categoryColor(agent.category)} text-white text-[10px]`}
                        >
                          {agent.category}
                        </Badge>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
