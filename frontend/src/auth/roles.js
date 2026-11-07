// Roles as the API returns them (backend/app/domain/models/enums.py: Role)
export const CLIENT = 'client';
export const STAFF_ROLES = ['trainer', 'reception', 'admin'];

// Where a user lands after signing in
export function homePathFor(user) {
  return user.role === CLIENT ? '/my' : '/staff';
}
