import {
  BarChartOutlined,
  CalendarOutlined,
  DashboardOutlined,
  HomeOutlined,
  IdcardOutlined,
  LoginOutlined,
  SettingOutlined,
  TagsOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { ADMIN, FRONT_DESK, TRAINER } from './roles';

// One place that says which role sees which section: the side menu, the role's start page
// and the route guards in App.jsx are all built from this list (a new section = a new line)
export const STAFF_MENU = [
  { path: '/staff/dashboard', label: 'Дашборд', icon: DashboardOutlined, roles: [ADMIN] },
  { path: '/staff/check-in', label: 'Реєстрація входу', icon: LoginOutlined, roles: FRONT_DESK },
  { path: '/staff/clients', label: 'Клієнти', icon: TeamOutlined, roles: FRONT_DESK },
  { path: '/staff/trainer', label: 'Мій кабінет', icon: IdcardOutlined, roles: [TRAINER] },
  { path: '/staff/schedule', label: 'Розклад', icon: CalendarOutlined, roles: [ADMIN] },
  { path: '/staff/trainers', label: 'Тренери', icon: IdcardOutlined, roles: [ADMIN] },
  { path: '/staff/halls', label: 'Зали', icon: HomeOutlined, roles: [ADMIN] },
  { path: '/staff/tariffs', label: 'Тарифи та знижки', icon: TagsOutlined, roles: [ADMIN] },
  { path: '/staff/reports', label: 'Звіти', icon: BarChartOutlined, roles: [ADMIN] },
  { path: '/staff/settings', label: 'Налаштування', icon: SettingOutlined, roles: [ADMIN] },
];

export const menuFor = (role) => STAFF_MENU.filter((item) => item.roles.includes(role));

export const staffHomeFor = (role) => menuFor(role)[0]?.path ?? '/403';

export const rolesFor = (path) => STAFF_MENU.find((item) => item.path === path).roles;
