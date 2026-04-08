import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CheckCircle, Mail, Save, User as UserIcon } from "lucide-react";
import { apiRequest } from "../lib/api";
import type { Profile, User } from "../lib/types";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { PageSpinner } from "../components/ui/Spinner";
import { Avatar } from "../components/ui/Avatar";

export function Settings() {
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);

  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiRequest<User>("/users/me"),
  });

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => apiRequest<Profile>("/me/profile"),
  });

  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [location, setLocation] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [interests, setInterests] = useState("");

  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name ?? "");
      setBio(profile.bio ?? "");
      setAvatarUrl(profile.avatar_url ?? "");
      setLocation(profile.location ?? "");
      setWebsiteUrl(profile.website_url ?? "");
      setInterests(profile.interests?.join(", ") ?? "");
    }
  }, [profile]);

  const updateMut = useMutation({
    mutationFn: () =>
      apiRequest<Profile>("/me/profile", {
        method: "PATCH",
        body: {
          display_name: displayName,
          bio: bio || null,
          avatar_url: avatarUrl || null,
          location: location || null,
          website_url: websiteUrl || null,
          interests: interests
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  if (userLoading || profileLoading) return <PageSpinner />;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="gradient-text mb-8 text-3xl font-extrabold"
      >
        Settings
      </motion.h1>

      {/* Account info (read-only) */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
        <Card className="mb-6">
          <CardHeader>
            <h2 className="flex items-center gap-2 text-lg font-semibold text-text-primary">
              <UserIcon className="h-5 w-5 text-accent" /> Account
            </h2>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Avatar
                src={profile?.avatar_url}
                name={user?.full_name || user?.username || "U"}
                size="lg"
              />
              <div className="space-y-1">
                <p className="font-medium text-text-primary">@{user?.username}</p>
                <p className="flex items-center gap-1.5 text-sm text-text-muted">
                  <Mail className="h-3.5 w-3.5" /> {user?.email}
                </p>
                {user?.full_name && (
                  <p className="text-sm text-text-secondary">{user.full_name}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Profile form */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-text-primary">Profile</h2>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                updateMut.mutate();
              }}
              className="space-y-4"
            >
              <Input
                label="Display Name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your display name"
              />
              <Textarea
                label="Bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell us about yourself"
                rows={3}
              />
              <Input
                label="Avatar URL"
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://..."
              />
              <Input
                label="Location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="San Francisco, CA"
              />
              <Input
                label="Website URL"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://..."
              />
              <Input
                label="Interests (comma-separated)"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
                placeholder="AI, ML, web development"
              />

              <div className="flex items-center gap-3 pt-2">
                <Button
                  variant="primary"
                  type="submit"
                  disabled={updateMut.isPending}
                  className="glow-sm"
                >
                  <Save className="mr-1.5 h-4 w-4" />
                  {updateMut.isPending ? "Saving..." : "Save Changes"}
                </Button>

                {saved && (
                  <motion.span
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-1 text-sm text-success"
                  >
                    <CheckCircle className="h-4 w-4" /> Saved
                  </motion.span>
                )}
              </div>

              {updateMut.isError && (
                <p className="text-sm text-danger">{(updateMut.error as Error).message}</p>
              )}
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
