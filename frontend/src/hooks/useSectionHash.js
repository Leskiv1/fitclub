import { useEffect } from 'react';

// A section is "current" while it crosses a thin line at ~45% of the viewport height
const ACTIVE_LINE = '-45% 0px -54% 0px';

function replaceHash(id) {
  const { pathname, search, hash } = window.location;
  const next = id ? `#${id}` : '';
  if (hash === next) return;
  // Keep React Router's history.state, and replace instead of push: scrolling must not add history steps
  window.history.replaceState(window.history.state, '', `${pathname}${search}${next}`);
}

// Scroll-spy for a one-page layout: the URL hash follows the section in view (<section id="...">)
// and disappears outside of them. An initial hash scrolls to its section once the content is ready.
export default function useSectionHash(ready, ids) {
  const key = ids.join(',');

  useEffect(() => {
    if (!ready) return undefined;
    const sections = key
      .split(',')
      .map((id) => document.getElementById(id))
      .filter(Boolean);

    const initial = document.getElementById(window.location.hash.slice(1));
    if (initial) initial.scrollIntoView();

    const visible = new Set();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) visible.add(entry.target.id);
          else visible.delete(entry.target.id);
        }
        replaceHash(sections.find((s) => visible.has(s.id))?.id);
      },
      { rootMargin: ACTIVE_LINE },
    );
    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, [ready, key]);
}

export function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
