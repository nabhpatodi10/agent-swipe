import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { setAccessToken } from "../lib/auth";
import { PageSpinner } from "../components/ui/Spinner";

export function GoogleCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.replace("#", ""));
    const token = params.get("access_token");

    if (token) {
      setAccessToken(token);
      navigate("/dashboard", { replace: true });
    } else {
      setError("No access token found. Authentication failed.");
    }
  }, [navigate]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-0">
        <div className="glass rounded-2xl p-8 text-center max-w-md">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-500/15">
            <span className="text-2xl">!</span>
          </div>
          <h2 className="text-xl font-semibold text-text-primary">Authentication Failed</h2>
          <p className="mt-2 text-text-muted">{error}</p>
          <a href="/login" className="mt-4 inline-block text-sm font-medium text-accent hover:underline">
            Back to login
          </a>
        </div>
      </div>
    );
  }

  return <PageSpinner />;
}
