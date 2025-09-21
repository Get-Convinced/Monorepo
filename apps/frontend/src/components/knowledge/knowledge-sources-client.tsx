"use client";

import { useState } from "react";
import { KnowledgeSources } from "@/components/knowledge/knowledge-sources";

export function KnowledgeSourcesClient({ websites, files, integrations }: any) {
  const [fileState, setFileState] = useState(files);

  const handleUpdateFileTags = (fileId: number, newTags: string[]) => {
    setFileState((prev:any) =>
      prev.map((file: any) =>
        file.id === fileId ? { ...file, tags: newTags } : file
      )
    );
  };

  return (
    <KnowledgeSources
      websites={websites}
      files={fileState}
      integrations={integrations}
      onUpdateFileTags={handleUpdateFileTags}
    />
  );
}
