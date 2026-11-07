import { ArrowLeftOutlined } from '@ant-design/icons';
import { Button } from 'antd';
import { Link } from 'react-router-dom';

// Top-left "back to the landing page" button on sign in / sign up
export default function BackHomeLink() {
  return (
    <Link to="/" className="back-home">
      <Button type="text" icon={<ArrowLeftOutlined />}>
        На головну
      </Button>
    </Link>
  );
}
