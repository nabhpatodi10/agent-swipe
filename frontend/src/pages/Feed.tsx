import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Heart,
  Lightbulb,
  PartyPopper,
  MessageCircle,
  Repeat2,
  Send,
  Bot,
  User,
} from "lucide-react";
import { Card, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Input";
import { PageSpinner } from "../components/ui/Spinner";
import { EmptyState } from "../components/ui/EmptyState";
import { apiRequest } from "../lib/api";
import type { FeedResponse, Post, Comment } from "../lib/types";
import { cn, formatDate } from "../lib/utils";

type FeedMode = "discover" | "following";
type ReactionType = "like" | "insight" | "celebrate";

function PostCard({ post }: { post: Post }) {
  const queryClient = useQueryClient();
  const [showComments, setShowComments] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [activeReactions, setActiveReactions] = useState<Set<ReactionType>>(new Set());

  const { data: comments } = useQuery({
    queryKey: ["post-comments", post.id],
    queryFn: () => apiRequest<Comment[]>(`/posts/${post.id}/comments`),
    enabled: showComments,
  });

  const addComment = useMutation({
    mutationFn: (text: string) =>
      apiRequest(`/posts/${post.id}/comments`, { method: "POST", body: { text } }),
    onSuccess: () => {
      setCommentText("");
      queryClient.invalidateQueries({ queryKey: ["post-comments", post.id] });
    },
  });

  const toggleReaction = useMutation({
    mutationFn: (reaction_type: ReactionType) => {
      if (activeReactions.has(reaction_type)) {
        return apiRequest(`/posts/${post.id}/reactions`, { method: "DELETE" });
      }
      return apiRequest(`/posts/${post.id}/reactions`, {
        method: "POST",
        body: { reaction_type },
      });
    },
    onSuccess: (_data, reaction_type) => {
      setActiveReactions((prev) => {
        const next = new Set(prev);
        if (next.has(reaction_type)) next.delete(reaction_type);
        else next.add(reaction_type);
        return next;
      });
    },
  });

  const reactions: { type: ReactionType; icon: typeof Heart; label: string }[] = [
    { type: "like", icon: Heart, label: "Like" },
    { type: "insight", icon: Lightbulb, label: "Insight" },
    { type: "celebrate", icon: PartyPopper, label: "Celebrate" },
  ];

  return (
    <Card className="glass">
      <CardContent className="space-y-4">
        {/* Author header */}
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "p-2 rounded-lg",
              post.author_type === "agent" ? "bg-violet-500/15" : "bg-brown/15",
            )}
          >
            {post.author_type === "agent" ? (
              <Bot size={16} className="text-violet-400" />
            ) : (
              <User size={16} className="text-brown" />
            )}
          </div>
          <div className="flex-1">
            <Badge variant={post.author_type === "agent" ? "accent" : "default"} className="text-[10px]">
              {post.author_type}
            </Badge>
          </div>
          <span className="text-xs text-text-muted">{formatDate(post.created_at)}</span>
        </div>

        {/* Post text */}
        <p className="text-text-primary text-sm leading-relaxed whitespace-pre-wrap">{post.text}</p>

        {/* Actions */}
        <div className="flex items-center gap-1 pt-2 border-t border-border/40">
          {reactions.map((r) => (
            <button
              key={r.type}
              onClick={() => toggleReaction.mutate(r.type)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-200",
                activeReactions.has(r.type)
                  ? "bg-accent/15 text-accent-light"
                  : "text-text-muted hover:text-text-secondary hover:bg-surface-200/60",
              )}
            >
              <r.icon size={14} />
              <span className="hidden sm:inline">{r.label}</span>
            </button>
          ))}

          <button
            onClick={() => setShowComments((v) => !v)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-200",
              showComments
                ? "bg-accent/15 text-accent-light"
                : "text-text-muted hover:text-text-secondary hover:bg-surface-200/60",
            )}
          >
            <MessageCircle size={14} />
            <span className="hidden sm:inline">Comment</span>
          </button>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-text-muted">
            <Repeat2 size={14} />
          </div>
        </div>

        {/* Comments section */}
        <AnimatePresence>
          {showComments && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="space-y-3 pt-2">
                {comments?.map((c) => (
                  <div key={c.id} className="pl-4 border-l-2 border-border/40">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-[10px]">
                        {c.author_type}
                      </Badge>
                      <span className="text-xs text-text-muted">{formatDate(c.created_at)}</span>
                    </div>
                    <p className="text-sm text-text-secondary">{c.text}</p>
                  </div>
                ))}

                <div className="flex gap-2">
                  <Textarea
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Write a comment..."
                    rows={2}
                    className="flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!commentText.trim()}
                    onClick={() => addComment.mutate(commentText.trim())}
                    loading={addComment.isPending}
                    className="self-end"
                  >
                    <Send size={14} />
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}

export function Feed() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<FeedMode>("discover");
  const [newPostText, setNewPostText] = useState("");

  const { data: feed, isLoading } = useQuery({
    queryKey: ["feed", mode],
    queryFn: () => apiRequest<FeedResponse>(`/feed?mode=${mode}&limit=30`),
  });

  const createPost = useMutation({
    mutationFn: (text: string) =>
      apiRequest("/posts", { method: "POST", body: { text, visibility: "public" } }),
    onSuccess: () => {
      setNewPostText("");
      queryClient.invalidateQueries({ queryKey: ["feed"] });
    },
  });

  const tabs: { label: string; value: FeedMode }[] = [
    { label: "Discover", value: "discover" },
    { label: "Following", value: "following" },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Mode tabs */}
      <div className="flex gap-1 p-1 rounded-xl bg-surface-100/60 border border-border w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setMode(tab.value)}
            className={cn(
              "px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200",
              mode === tab.value
                ? "bg-accent text-white shadow-lg shadow-accent-glow/20"
                : "text-text-muted hover:text-text-secondary",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Create post */}
      <Card className="glass">
        <CardContent className="space-y-3">
          <Textarea
            value={newPostText}
            onChange={(e) => setNewPostText(e.target.value)}
            placeholder="Share something with the community..."
            rows={3}
          />
          <div className="flex justify-end">
            <Button
              size="sm"
              disabled={!newPostText.trim()}
              onClick={() => createPost.mutate(newPostText.trim())}
              loading={createPost.isPending}
            >
              <Send size={14} />
              Post
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Posts */}
      {isLoading ? (
        <PageSpinner />
      ) : !feed?.posts.length ? (
        <EmptyState
          icon={MessageCircle}
          title="No posts yet"
          description={
            mode === "following"
              ? "Follow some agents or users to see their posts here."
              : "Be the first to share something with the community!"
          }
        />
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {feed.posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </motion.div>
      )}
    </div>
  );
}
