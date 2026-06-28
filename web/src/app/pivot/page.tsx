import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import PivotBoard from "@/components/PivotBoard";

export default async function PivotPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  return <PivotBoard userEmail={user.email ?? ""} />;
}
