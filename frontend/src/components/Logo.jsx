import { ThunderboltFilled } from '@ant-design/icons';
import { Link } from 'react-router-dom';

export default function Logo({ to = '/', light = false }) {
  return (
    <Link to={to} className={`logo ${light ? 'logo--light' : ''}`}>
      <span className="logo__mark">
        <ThunderboltFilled />
      </span>
      FitClub
    </Link>
  );
}
