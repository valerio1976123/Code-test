import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../auth/AuthProvider";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "admin@example.com", password: "password" },
  });

  return (
    <div className="flex min-h-full items-center justify-center bg-slate-50 px-4 py-10">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-3"
            onSubmit={form.handleSubmit(async (v) => {
              await login(v.email, v.password);
              toast.success("Logged in");
              nav("/");
            })}
          >
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Email</div>
              <Input
                autoComplete="email"
                {...form.register("email")}
                placeholder="you@example.com"
              />
            </div>
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-700">Password</div>
              <Input
                type="password"
                autoComplete="current-password"
                {...form.register("password")}
              />
            </div>

            {form.formState.errors.email?.message ? (
              <div className="text-xs text-red-600">
                {form.formState.errors.email.message}
              </div>
            ) : null}

            <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

