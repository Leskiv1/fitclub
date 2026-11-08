import { Alert, Card, Divider, Flex, Typography } from 'antd';
import { getErrorMessage } from '../utils/errors';
import { DISCOUNT_LABELS, formatMoney } from '../utils/format';

const { Text } = Typography;

// Price breakdown from POST /memberships/quote (tariff + options − discount)
export default function PriceSummary({ quote, error, pending, bordered = true }) {
  return (
    <Card
      className={bordered ? 'soft-card' : undefined}
      variant={bordered ? 'outlined' : 'borderless'}
      title="Розрахунок вартості"
      size={bordered ? undefined : 'small'}
    >
      {error && <Alert type="error" showIcon title={getErrorMessage(error)} />}
      {!quote && !error && <Text type="secondary">Оберіть тариф</Text>}
      {quote && (
        <Flex vertical gap={8} style={{ opacity: pending ? 0.5 : 1 }}>
          {quote.lines.map((line) => (
            <Flex key={line.name} justify="space-between" gap={8}>
              <Text>{line.name}</Text>
              <Text>{formatMoney(line.amount)}</Text>
            </Flex>
          ))}
          {quote.discount && (
            <Flex justify="space-between" gap={8}>
              <Text type="success">
                Знижка «{DISCOUNT_LABELS[quote.discount.type]}» −{quote.discount.percent}%
              </Text>
              <Text type="success">−{formatMoney(quote.discount.amount)}</Text>
            </Flex>
          )}
          <Divider style={{ margin: '8px 0' }} />
          <Flex justify="space-between" align="baseline">
            <Text strong>Разом до сплати</Text>
            <span className="price">{formatMoney(quote.total)}</span>
          </Flex>
        </Flex>
      )}
    </Card>
  );
}
