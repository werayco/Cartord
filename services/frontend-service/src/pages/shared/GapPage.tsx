import type { ReactNode } from "react";
import { PageHeader } from "../../components/ui/StatCard";
import { GapNotice } from "../../components/ui/feedback";

export function GapPage({ title, subtitle, gapTitle, children }: { title: string; subtitle: string; gapTitle: string; children: ReactNode }) {
  return (
    <>
      <PageHeader title={title} subtitle={subtitle} />
      <GapNotice title={gapTitle}>{children}</GapNotice>
    </>
  );
}
