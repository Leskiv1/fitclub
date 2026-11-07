import { Button, Result } from 'antd';
import { Link } from 'react-router-dom';

export default function ForbiddenPage() {
  return (
    <Result
      status="403"
      title="403"
      subTitle="Ця сторінка недоступна для вашої ролі"
      extra={
        <Link to="/">
          <Button type="primary">На головну</Button>
        </Link>
      }
    />
  );
}
