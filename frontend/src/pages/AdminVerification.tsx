import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, CheckCircle, XCircle } from "lucide-react";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { PageSpinner } from "../components/ui/Spinner";
import { EmptyState } from "../components/ui/EmptyState";
import { apiRequest } from "../lib/api";
import type { VerificationRequest } from "../lib/types";
import { cn, formatDate } from "../lib/utils";

type StatusFilter = "pending" | "all";

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
    case "pending":
      return "warning";
    case "approved":
      return "success";
    case "rejected":
      return "danger";
    default:
      return "default";
  }
}

export function AdminVerification() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<StatusFilter>("pending");
  const [rejectTarget, setRejectTarget] = useState<VerificationRequest | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const queryKey = ["admin", "verification-requests", filter];

  const { data: requests, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      apiRequest<VerificationRequest[]>(
        filter === "pending"
          ? "/admin/verification-requests?status_filter=pending"
          : "/admin/verification-requests",
      ),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/admin/verification-requests/${id}/approve`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "verification-requests"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      apiRequest(`/admin/verification-requests/${id}/reject`, {
        method: "POST",
        body: { reason },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "verification-requests"] });
      setRejectTarget(null);
      setRejectReason("");
    },
  });

  if (isLoading) return <PageSpinner />;

  return (
    <div className="min-h-screen bg-surface-0">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2.5 rounded-xl bg-accent/15">
            <ShieldCheck size={24} className="text-accent-light" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Verification Requests</h1>
            <p className="text-sm text-text-secondary">Review and manage agent verification submissions</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-1 p-1 bg-surface-100 rounded-xl w-fit mb-6 border border-border/50">
          {(["pending", "all"] as const).map((tab) => (
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

        {/* Request List */}
        {!requests?.length ? (
          <EmptyState
            icon={ShieldCheck}
            title="No verification requests"
            description={
              filter === "pending"
                ? "There are no pending verification requests at this time."
                : "No verification requests have been submitted yet."
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
              {requests.map((req) => (
                <motion.div key={req.id} variants={item} layout exit={{ opacity: 0, x: -20 }}>
                  <Card>
                    <CardHeader>
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-3 min-w-0">
                          <Badge variant={statusBadgeVariant(req.status)}>{req.status}</Badge>
                          <span className="text-xs text-text-muted truncate">
                            {formatDate(req.created_at)}
                          </span>
                        </div>
                        {req.status === "pending" && (
                          <div className="flex items-center gap-2 shrink-0 ml-4">
                            <Button
                              size="sm"
                              variant="ghost"
                              loading={approveMutation.isPending}
                              onClick={() => approveMutation.mutate(req.id)}
                              className="text-success hover:bg-success/10"
                            >
                              <CheckCircle size={15} />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="danger"
                              onClick={() => setRejectTarget(req)}
                            >
                              <XCircle size={15} />
                              Reject
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-text-muted text-xs uppercase tracking-wider">Agent ID</span>
                          <p className="text-text-primary font-mono text-xs mt-1 truncate">{req.agent_id}</p>
                        </div>
                        <div>
                          <span className="text-text-muted text-xs uppercase tracking-wider">Submitted By</span>
                          <p className="text-text-primary font-mono text-xs mt-1 truncate">{req.submitted_by_user_id}</p>
                        </div>
                        <div>
                          <span className="text-text-muted text-xs uppercase tracking-wider">Evidence</span>
                          <p className="text-text-secondary text-xs mt-1 line-clamp-2">
                            {req.evidence_note || "No evidence provided"}
                          </p>
                        </div>
                      </div>
                      {req.rejection_reason && (
                        <div className="mt-3 p-3 bg-danger/5 border border-danger/15 rounded-lg">
                          <span className="text-danger text-xs font-medium">Rejection reason:</span>
                          <p className="text-text-secondary text-xs mt-1">{req.rejection_reason}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Reject Modal */}
        <Modal
          open={!!rejectTarget}
          onClose={() => {
            setRejectTarget(null);
            setRejectReason("");
          }}
          title="Reject Verification Request"
        >
          <div className="space-y-4">
            <p className="text-sm text-text-secondary">
              Provide a reason for rejecting the verification request for agent{" "}
              <span className="font-mono text-text-primary text-xs">{rejectTarget?.agent_id}</span>.
            </p>
            <Textarea
              placeholder="Enter rejection reason..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={4}
              className="w-full"
            />
            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={() => {
                  setRejectTarget(null);
                  setRejectReason("");
                }}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                loading={rejectMutation.isPending}
                disabled={!rejectReason.trim()}
                onClick={() => {
                  if (rejectTarget) {
                    rejectMutation.mutate({ id: rejectTarget.id, reason: rejectReason.trim() });
                  }
                }}
              >
                Reject Request
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
}
