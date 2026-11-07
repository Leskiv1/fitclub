// The API answers every error as {"error": {"code", "message", "details"?}} (backend/app/api/errors.py)
export function getErrorCode(error) {
  return error?.response?.data?.error?.code ?? null;
}

export function getErrorMessage(error, fallback = 'Щось пішло не так. Спробуйте ще раз.') {
  if (!error?.response) return 'Сервер недоступний. Перевірте зʼєднання.';
  const body = error.response.data?.error;
  if (!body) return fallback;
  if (body.details?.length) {
    return body.details.map((d) => (d.field ? `${d.field}: ${d.message}` : d.message)).join('; ');
  }
  return body.message || fallback;
}
