import { Button, Result } from 'antd';
import { getErrorMessage } from '../utils/errors';

export default function LoadError({ error, onRetry }) {
  return (
    <Result
      status="warning"
      title="Не вдалося завантажити дані"
      subTitle={getErrorMessage(error)}
      extra={onRetry && <Button onClick={onRetry}>Спробувати ще раз</Button>}
    />
  );
}
