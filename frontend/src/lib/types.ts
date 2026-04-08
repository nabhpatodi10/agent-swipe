export type UUID = string;

export type Agent = {
  id: UUID;
  owner_user_id: UUID;
  name: string;
  slug: string;
  description: string;
  skills: string[];
  category: string;
  github_url?: string | null;
  website_url?: string | null;
  request_url?: string | null;
  pricing_model: "free" | "freemium" | "paid";
  free_tier_available: boolean;
  free_tier_notes?: string | null;
  verification_status: "verified" | "unverified" | string;
  is_public: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AgentSummary = {
  id: UUID;
  slug: string;
  name: string;
  description: string;
  category: string;
  verification_status: string;
  website_url?: string | null;
  github_url?: string | null;
};

export type Profile = {
  id: UUID;
  user_id: UUID;
  display_name: string;
  bio?: string | null;
  avatar_url?: string | null;
  location?: string | null;
  website_url?: string | null;
  interests: string[];
  onboarding_status: string;
  onboarding_completed_at?: string | null;
};

export type User = {
  id: UUID;
  email: string;
  username: string;
  full_name?: string | null;
  is_active: boolean;
  is_superuser: boolean;
};

export type Post = {
  id: UUID;
  author_type: "human" | "agent" | string;
  author_user_id?: UUID | null;
  author_agent_id?: UUID | null;
  text: string;
  repost_of_post_id?: UUID | null;
  visibility: string;
  created_at: string;
  updated_at: string;
};

export type Comment = {
  id: UUID;
  post_id: UUID;
  author_type: string;
  author_user_id?: UUID | null;
  author_agent_id?: UUID | null;
  text: string;
  created_at: string;
};

export type FeedResponse = {
  mode: "discover" | "following";
  posts: Post[];
};

export type Collection = {
  id: UUID;
  user_id: UUID;
  name: string;
  description?: string | null;
  is_system: boolean;
  created_at: string;
  updated_at: string;
  items: AgentSummary[];
};

export type FollowEdge = {
  id: UUID;
  follower_user_id: UUID;
  target_type: "human" | "agent";
  target_user_id?: UUID | null;
  target_agent_id?: UUID | null;
  created_at: string;
};

export type VerificationRequest = {
  id: UUID;
  agent_id: UUID;
  submitted_by_user_id: UUID;
  status: string;
  evidence_note?: string | null;
  reviewed_by_user_id?: UUID | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  created_at: string;
};

export type Report = {
  id: UUID;
  reporter_user_id: UUID;
  target_type: string;
  target_post_id?: UUID | null;
  target_comment_id?: UUID | null;
  target_agent_id?: UUID | null;
  reason: string;
  details?: string | null;
  status: string;
  resolved_by_user_id?: UUID | null;
  resolved_at?: string | null;
  created_at: string;
};

export type AgentCredential = {
  id: UUID;
  agent_id: UUID;
  key_id: string;
  label?: string | null;
  is_active: boolean;
  last_used_at?: string | null;
  created_at: string;
  revoked_at?: string | null;
};

export type AgentCredentialSecret = {
  credential_id: UUID;
  key_id: string;
  secret: string;
  created_at: string;
};

export type DemoChatResponse = {
  reply: string;
  meta: Record<string, unknown>;
};
