import { useCallback, useEffect, useState } from 'react';
import { deleteDocument, listDocuments, uploadDocument } from '../api';
import type { StockDocument } from '../types';

export function useDocuments() {
  const [documents, setDocuments] = useState<StockDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // Leave existing list as-is on a transient failure — same pattern as
      // useConversations, since the header's backend-status dot already
      // surfaces an outage.
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await refresh();
      if (!cancelled) setIsLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const upload = useCallback(async (file: File, ticker?: string) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const doc = await uploadDocument(file, ticker);
      setDocuments((prev) => [doc, ...prev]);
      return doc;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Upload failed. Please try again.';
      setUploadError(message);
      throw err;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const remove = useCallback(async (docId: string) => {
    await deleteDocument(docId);
    setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
  }, []);

  return { documents, isLoading, isUploading, uploadError, upload, remove };
}
