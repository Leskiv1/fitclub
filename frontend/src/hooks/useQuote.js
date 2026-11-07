import { useEffect, useState } from 'react';
import { quoteMembership } from '../api/memberships';

const QUOTE_DELAY_MS = 300;

// Server-side price (Facade -> Decorator -> Strategy), re-requested after each change.
// The result is accepted only for the current payload, so late answers cannot overwrite it.
export default function useQuote(payload) {
  const key = payload ? JSON.stringify(payload) : null;
  const [result, setResult] = useState({ key: null, quote: null, error: null });

  useEffect(() => {
    if (!key) return undefined;
    let active = true;
    const timer = setTimeout(() => {
      quoteMembership(JSON.parse(key)).then(
        (quote) => active && setResult({ key, quote, error: null }),
        (error) => active && setResult({ key, quote: null, error }),
      );
    }, QUOTE_DELAY_MS);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [key]);

  const pending = Boolean(key) && result.key !== key;
  return { quote: result.quote, error: pending ? null : result.error, pending };
}
