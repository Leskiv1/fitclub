// Roles as the API returns them (backend/app/domain/models/enums.py: Role)
export const CLIENT = 'client';
export const TRAINER = 'trainer';
export const RECEPTION = 'reception';
export const ADMIN = 'admin';

export const STAFF_ROLES = [TRAINER, RECEPTION, ADMIN];
// Same groups as STAFF_ONLY / ADMIN_ONLY in backend/app/api/deps.py
export const FRONT_DESK = [RECEPTION, ADMIN];

export const ROLE_LABELS = {
  [CLIENT]: 'Клієнт',
  [TRAINER]: 'Тренер',
  [RECEPTION]: 'Рецепція',
  [ADMIN]: 'Адміністратор',
};

// Where a user lands after signing in; /staff then opens the first menu item of the role
export function homePathFor(user) {
  return user.role === CLIENT ? '/my' : '/staff';
}
