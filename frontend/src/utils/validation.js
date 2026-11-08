// Form rules that mirror the API schemas (ClientCreate / TrainerCreate), so most mistakes
// are caught before the request; the server still validates everything

const PHONE_RE = /^\+?\d{10,15}$/;

export const nameRules = [
  { required: true, whitespace: true, message: 'Введіть ПІБ' },
  { min: 2, max: 150, message: 'Від 2 до 150 символів' },
];

export const phoneRules = [
  { required: true, message: 'Введіть телефон' },
  { pattern: PHONE_RE, message: '10–15 цифр, наприклад +380671234567' },
];

// Spaces, dashes and brackets are removed as the user types, as the server does
export const normalizePhone = (value) => value.replace(/[\s\-()]/g, '');

export const emailRules = [{ required: true, type: 'email', message: 'Введіть коректний email' }];

export const passwordRules = [
  { required: true, min: 6, max: 128, message: 'Щонайменше 6 символів' },
];
