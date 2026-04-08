import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Flag, CheckCircle2 } from "lucide-react";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { PageSpinner } from "../components/ui/Spinner";
import { EmptyState } from "../components/ui/EmptyState";
import { apiRequest } from "../lib/api";
import type { Report } from "../lib/types";
import { cn, formatDate } from "../lib/utils";

type StatusFilter = "open" | "all";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

function statusBadgeVariant(status: string) {
  switch (status) {
    case "open":
      return "warning";
    case "resolved":
      return "success";
    case "dismissed":
      return "default";
    default:
      return "default";
  }
}

function targetTypeBadgeVariant(type: string) {
  switch (type) {
    case "post":
      return "accent";
    case "comment":
      return "outline";
    case "agent":
      return "danger";
    default:
      return "default";
  }
}

export function AdminReports() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<StatusFilter>("open");

  const queryKey = ["admin", "reports", filter];

  const { data: reports, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      apiRequest<Report[]>(
        filter === "open" ? "/admin/reports?status_filter=open" : "/admin/reports",
      ),
  });

  const resolveMutation = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/admin/reports/${id}/resolve`, {
        method: "POST",
        body: { status: "resolved" },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "reports"] }),
  });

  if (isLoading) return <PageSpinner />;

  return (
    <div className="min-h-screen bg-surface-0">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2.5 rounded-xl bg-danger/15">
            <Flag size={24} className="text-danger" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Content Reports</h1>
            <p className="text-sm text-text-secondary">Review and resolve reported content</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-1 p-1 bg-surface-100 rounded-xl w-fit mb-6 border border-border/50">
          {(["open", "all"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 capitalize",
                filter === tab
                  ? "bg-surface-200 text-text-primary shadow-sm"
                  : "text-text-muted hover:text-text-secondary",
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Reports List */}
        {!reports?.length ? (
          <EmptyState
            icon={Flag}
            title="No reports"
            description={
              filter === "open"
                ? "There are no open content reports at this time."
                : "No content reports have been submitted yet."
            }
          />
        ) : (
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="space-y-3"
          >
            <AnimatePresence mode="popLayout">
              {reports.map((report) => (
                <motion.div key={report.id} variants={item} layout exit={{ opacity: 0, x: -20 }}>
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <Badge variant={targetTypeBadgeVariant(report.target_type)}>
                            {report.target_type}
                          </Badge>
                          <Badge variant={statusBadgeVariant(report.status)}>
                            {report.status}
                          </Badge>
                          <span className="text-xs text-text-muted truncate">
                            {formatDate(report.created_at)}
                          </span>
                        </div>
                        {report.status === "open" && (
                          <div className="shrink-0 ml-4">
                            <Button
                              size="sm"
                              variant="ghost"
                              loading={resolveMutation.isPending}
                              onClick={() => resolveMutation.mutate(report.id)}
                              className="text-success hover:bg-success/10"
                            >
                              <CheckCircle2 size={15} />
                              Resolve
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-text-muted text-xs uppercase tracking-wider">Reason</span>
                          <p className="text-text-primary text-sm mt-1 font-medium">{report.reason}</p>
                        </div>
                        <div>
                          <span className="text-text-muted text-xs uppercase tracking-wider">Reporter</span>
                          <p className="text-text-primary font-mono text-xs mt-1 truncate">
                            {report.reporter_user_id}
                          </p>
                        </div>
                      </div>
                      {report.details && (
                        <div className="mt-3 p-3 bg-surface-200/50 rounded-lg border border-border/30">
                          <span className="text-text-muted text-xs uppercase tracking-wider">Details</span>
                          <p className="text-text-secondary text-sm mt-1">{report.details}</p>
                        </div>
                      )}
                      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-muted">
                        {report.target_post_id && (
                          <span>Post: <span className="font-mono text-text-secondary">{report.target_post_id}</span></span>
                        )}
                        {report.target_comment_id && (
                          <span>Comment: <span className="font-mono text-text-secondary">{report.target_comment_id}</span></span>
                        )}
                        {report.target_agent_id && (
                          <span>Agent: <span className="font-mono text-text-secondary">{report.target_agent_id}</span></span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  );
}
