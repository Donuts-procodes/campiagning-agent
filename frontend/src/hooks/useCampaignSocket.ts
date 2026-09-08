import { useCallback, useEffect, useRef, useState } from 'react';

interface SocketState {
  current_node: string | null;
  next_nodes: string[];
  verification: Record<string, unknown> | null;
  hitl: Record<string, unknown> | null;
  execution: Record<string, unknown> | null;
  revision_count: number;
  error: string | null;
}

const INITIAL_STATE: SocketState = {
  current_node: null,
  next_nodes: [],
  verification: null,
  hitl: null,
  execution: null,
  revision_count: 0,
  error: null,
};

export function useCampaignSocket(threadId: string | null) {
  const [state, setState] = useState<SocketState>(INITIAL_STATE);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const unmountedRef = useRef(false);

  const clearReconnectTimeout = () => {
    if (reconnectTimeoutRef.current !== null) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  };

  const connect = useCallback(() => {
    if (!threadId || unmountedRef.current) return;
    clearReconnectTimeout();
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/${threadId}?api_key=default_dev_key`);

    ws.onopen = () => {
      setConnected(true);
      retryRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'state_update' && msg.data) {
          setState((current) => ({ ...current, ...msg.data }));
        }
        if (msg.type === 'error') {
          setState((current) => ({ ...current, error: msg.message || 'WebSocket error' }));
        }
      } catch {
        /* ignore parse errors */
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (!unmountedRef.current && retryRef.current < 10) {
        retryRef.current += 1;
        reconnectTimeoutRef.current = window.setTimeout(connect, Math.min(1000 * retryRef.current, 5000));
      }
    };

    ws.onerror = () => ws.close();
    wsRef.current = ws;
  }, [threadId]);

  useEffect(() => {
    unmountedRef.current = false;
    retryRef.current = 0;
    setState(INITIAL_STATE);
    connect();
    return () => {
      unmountedRef.current = true;
      clearReconnectTimeout();
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect, threadId]);

  return { state, connected };
}
