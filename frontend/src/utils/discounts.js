import { DISCOUNT_LABELS } from './format';

// One discount per purchase. Conditions are checked by the server (Strategy); here they are only explained
export const DISCOUNTS = [
  { value: 'none', label: 'Без знижки' },
  {
    value: 'student',
    label: DISCOUNT_LABELS.student,
    hint: 'Для студентів до 21 року. Потрібен номер студентського квитка.',
    reference: { placeholder: 'КВ12345678', label: 'Номер студентського квитка' },
  },
  {
    value: 'loyalty',
    label: DISCOUNT_LABELS.loyalty,
    hint: 'Для клієнтів, які оплатили 12 і більше абонементів.',
  },
  {
    value: 'promo',
    label: DISCOUNT_LABELS.promo,
    hint: 'Код з акції клубу.',
    reference: { placeholder: 'AUTUMN10', label: 'Промокод' },
  },
];

export const discountByValue = (value) => DISCOUNTS.find((d) => d.value === value);

// Request body part: null until a discount that needs a reference has one
export function buildDiscount(type, reference) {
  if (type === 'none') return null;
  if (!discountByValue(type).reference) return { type };
  return reference.trim() ? { type, reference: reference.trim() } : null;
}
