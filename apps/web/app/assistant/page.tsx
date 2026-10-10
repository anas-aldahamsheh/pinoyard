"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCustomerSessionContext } from "@/lib/api";
import { Logo } from "@/components/ui/Logo";

export default function AssistantEntryPage() {
  const router = useRouter();

  useEffect(() => {
    sessionStorage.setItem("open_pino_yard_assistant", "1");
    let ignore = false;
    getCustomerSessionContext()
      .catch(() => null)
      .then((context) => {
        if (!ignore) router.replace(context ? "/menu" : "/");
      });
    return () => {
      ignore = true;
    };
  }, [router]);

  // A moment while we open the menu with the assistant's chat.
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-5 bg-canvas p-6" role="status" aria-busy="true">
      <Logo className="h-11" />
      <div className="h-1 w-36 overflow-hidden rounded-full bg-surface-3" aria-hidden="true">
        <div className="h-full w-1/3 animate-route rounded-full bg-brand rtl:[animation-direction:reverse]" />
      </div>
    </main>
  );
}
