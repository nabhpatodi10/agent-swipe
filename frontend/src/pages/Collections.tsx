import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  FolderOpen,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  Package,
  X,
} from "lucide-react";
import { apiRequest } from "../lib/api";
import type { Collection } from "../lib/types";
import { cn, formatDate, truncate } from "../lib/utils";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Modal } from "../components/ui/Modal";
import { PageSpinner } from "../components/ui/Spinner";
import { EmptyState } from "../components/ui/EmptyState";

export function Collections() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const { data: collections, isLoading } = useQuery({
    queryKey: ["collections"],
    queryFn: () => apiRequest<Collection[]>("/collections"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiRequest<Collection>("/collections", {
        method: "POST",
        body: { name, description: description || null },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      setCreateOpen(false);
      setName("");
      setDescription("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/collections/${id}`, { method: "DELETE" }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["collections"] }),
  });

  const removeItemMutation = useMutation({
    mutationFn: ({
      collectionId,
      agentId,
    }: {
      collectionId: string;
      agentId: string;
    }) =>
      apiRequest(`/collections/${collectionId}/items/${agentId}`, {
        method: "DELETE",
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["collections"] }),
  });

  if (isLoading) return <PageSpinner />;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-text-primary">Collections</h1>
        <Button variant="primary" onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Collection
        </Button>
      </div>

      {/* Create Modal */}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create Collection">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate();
          }}
          className="space-y-4"
        >
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My collection"
            required
          />
          <Textarea
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What is this collection for?"
            rows={3}
          />
          <div className="flex justify-end gap-3">
            <Button variant="ghost" type="button" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={createMutation.isPending || !name.trim()}>
              {createMutation.isPending ? "Creating..." : "Create"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Grid */}
      {!collections?.length ? (
        <EmptyState
          icon={FolderOpen}
          title="No collections yet"
          description="Create a collection to organize your favorite agents."
        />
      ) : (
        <motion.div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          initial="hidden"
          animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
        >
          {collections.map((col) => {
            const expanded = expandedId === col.id;
            return (
              <motion.div
                key={col.id}
                variants={{
                  hidden: { opacity: 0, y: 16 },
                  visible: { opacity: 1, y: 0 },
                }}
                className={cn(
                  "col-span-1",
                  expanded && "sm:col-span-2 lg:col-span-3"
                )}
              >
                <Card hover className="overflow-hidden">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <button
                        className="flex flex-1 items-center gap-2 text-left"
                        onClick={() => setExpandedId(expanded ? null : col.id)}
                      >
                        {expanded ? (
                          <ChevronDown className="h-4 w-4 text-text-muted" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-text-muted" />
                        )}
                        <div>
                          <h3 className="font-semibold text-text-primary">
                            {col.name}
                          </h3>
                          {col.description && (
                            <p className="mt-1 text-sm text-text-secondary">
                              {truncate(col.description, 80)}
                            </p>
                          )}
                        </div>
                      </button>

                      {!col.is_system && (
                        <button
                          onClick={() => deleteMutation.mutate(col.id)}
                          className="ml-2 rounded p-1 text-text-muted transition hover:bg-danger/20 hover:text-danger"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>

                    <div className="mt-3 flex items-center gap-2 text-xs text-text-muted">
                      <Package className="h-3.5 w-3.5" />
                      <span>{col.items.length} agents</span>
                      {col.is_system && <Badge variant="accent">System</Badge>}
                      <span className="ml-auto">{formatDate(col.created_at)}</span>
                    </div>
                  </CardHeader>

                  {/* Expanded items */}
                  <AnimatePresence>
                    {expanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <CardContent>
                          {col.items.length === 0 ? (
                            <p className="text-sm text-text-muted">
                              No agents in this collection.
                            </p>
                          ) : (
                            <ul className="space-y-2">
                              {col.items.map((agent) => (
                                <li
                                  key={agent.id}
                                  className="flex items-center justify-between rounded-lg bg-surface-100 px-3 py-2"
                                >
                                  <NavLink
                                    to={`/agents/${agent.slug}`}
                                    className="font-medium text-text-primary hover:text-accent-light"
                                  >
                                    {agent.name}
                                  </NavLink>

                                  <button
                                    onClick={() =>
                                      removeItemMutation.mutate({
                                        collectionId: col.id,
                                        agentId: agent.id,
                                      })
                                    }
                                    className="rounded p-1 text-text-muted transition hover:bg-danger/20 hover:text-danger"
                                  >
                                    <X className="h-3.5 w-3.5" />
                                  </button>
                                </li>
                              ))}
                            </ul>
                          )}
                        </CardContent>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
}
