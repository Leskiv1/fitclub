import { useEffect, useState } from 'react';
import { Select } from 'antd';
import { searchClients } from '../api/clients';

const SEARCH_DELAY_MS = 300;

// Find a client by part of the name or phone (server-side search, Ф-1)
export default function ClientSearchSelect({ value, onChange, autoFocus }) {
  const [text, setText] = useState('');
  const [result, setResult] = useState({ text: null, options: [] });

  useEffect(() => {
    if (text.trim().length < 2) return undefined;
    let active = true;
    const timer = setTimeout(() => {
      searchClients({ q: text.trim(), limit: 10 }).then(
        (page) =>
          active &&
          setResult({
            text,
            options: page.items.map((c) => ({
              value: c.id,
              label: `${c.full_name} · ${c.phone}`,
            })),
          }),
        () => active && setResult({ text, options: [] }),
      );
    }, SEARCH_DELAY_MS);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [text]);

  const searching = text.trim().length >= 2 && result.text !== text;

  return (
    <Select
      showSearch={{ filterOption: false, onSearch: setText }}
      value={value}
      onChange={onChange}
      options={result.options}
      loading={searching}
      notFoundContent={text.trim().length < 2 ? 'Введіть 2+ символи' : 'Нікого не знайдено'}
      placeholder="ПІБ або телефон клієнта"
      size="large"
      autoFocus={autoFocus}
      style={{ width: '100%' }}
    />
  );
}
