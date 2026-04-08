import { Navigate, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { isAuthenticated } from "../../lib/auth";
import { apiRequest } from "../../lib/api";
import { Sidebar } from "./Sidebar";
import { PageSpinner } from "../ui/Spinner";
import type { User } from "../../lib/types";

export function AppLayout() {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  const { data: user, isLoading } = useQuery({
    queryKey: ["currentUser"],
    queryFn: () => apiRequest<User>("/users/me"),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) return <PageSpinner />;

  return (
    <div className="min-h-screen">
      <Sidebar user={user} />
      <main className="ml-64 min-h-screen textured-bg">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
