import { useState } from 'react';
import { CheckOutlined, CreditCardOutlined } from '@ant-design/icons';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Flex,
  Input,
  Radio,
  Result,
  Row,
  Steps,
  Tag,
  Typography,
} from 'antd';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchOptions, fetchTariffs } from '../../api/catalog';
import { purchaseMembership } from '../../api/memberships';
import LoadError from '../../components/LoadError';
import PageSpinner from '../../components/PageSpinner';
import PriceSummary from '../../components/PriceSummary';
import useApi from '../../hooks/useApi';
import useQuote from '../../hooks/useQuote';
import { dayjs } from '../../utils/dates';
import { buildDiscount, discountByValue, DISCOUNTS } from '../../utils/discounts';
import { getErrorMessage } from '../../utils/errors';
import {
  formatMoney,
  sortTariffs,
  TARIFF_TYPE_LABELS,
  tariffSummary,
  visits,
} from '../../utils/format';

const { Title, Text } = Typography;
const DATE = 'DD.MM.YYYY';

async function loadCatalog() {
  const [tariffs, options] = await Promise.all([fetchTariffs(), fetchOptions()]);
  return {
    tariffs: sortTariffs(tariffs.filter((t) => t.is_active)),
    options: options.filter((o) => o.is_active),
  };
}

function SelectCard({ active, onClick, children }) {
  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={active}
      className={`select-card ${active ? 'select-card--active' : ''}`}
      onClick={onClick}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      style={{ padding: 16, background: active ? undefined : '#fff' }}
    >
      {children}
    </div>
  );
}

// Ф-5: membership purchase in 4 steps — tariff, options, discount, payment (simulated)
export default function PurchasePage() {
  const [searchParams] = useSearchParams();
  const { data: catalog, error, reload } = useApi(loadCatalog);
  const [step, setStep] = useState(0);
  const [tariffId, setTariffId] = useState(() => Number(searchParams.get('tariff')) || null);
  const [optionIds, setOptionIds] = useState([]);
  const [discountType, setDiscountType] = useState('none');
  const [reference, setReference] = useState('');
  const [paying, setPaying] = useState(false);
  const [payError, setPayError] = useState(null);
  const [purchased, setPurchased] = useState(null);

  const tariff = catalog?.tariffs.find((t) => t.id === tariffId) ?? null;
  const payload = tariff
    ? {
        tariff_id: tariff.id,
        option_ids: optionIds,
        discount: buildDiscount(discountType, reference),
      }
    : null;
  const { quote, error: quoteError, pending } = useQuote(purchased ? null : payload);

  if (error && !catalog) return <LoadError error={error} onRetry={reload} />;
  if (!catalog) return <PageSpinner />;

  if (purchased) {
    return (
      <Result
        status="success"
        title="Абонемент оформлено"
        subTitle={`${purchased.tariff.name}: ${dayjs(purchased.start_date).format(DATE)} – ${dayjs(
          purchased.end_date,
        ).format(DATE)}. Сплачено ${formatMoney(purchased.total_price)}.`}
        extra={[
          <Link key="my" to="/my">
            <Button type="primary">Мій абонемент</Button>
          </Link>,
          <Link key="schedule" to="/my/schedule">
            <Button>Записатися на заняття</Button>
          </Link>,
        ]}
      />
    );
  }

  const toggleOption = (id) =>
    setOptionIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]));

  const pay = async () => {
    setPaying(true);
    setPayError(null);
    try {
      setPurchased(await purchaseMembership(payload));
    } catch (err) {
      setPayError(err);
      setPaying(false);
    }
  };

  const discount = discountByValue(discountType);
  const missingReference = Boolean(discount.reference) && !reference.trim();
  const canGoNext =
    (step === 0 && tariff) ||
    step === 1 ||
    (step === 2 && !missingReference && !quoteError && !pending);
  const startsLater = quote && quote.start_date > dayjs().format('YYYY-MM-DD');

  return (
    <>
      <Title level={2} className="page-title">
        Оформлення абонемента
      </Title>
      <Text className="page-subtitle">Тариф, опції та знижка — ціна рахується одразу</Text>

      <Steps
        current={step}
        onChange={(next) => next < step && setStep(next)}
        items={[
          { title: 'Тариф', content: tariff?.name },
          { title: 'Опції' },
          { title: 'Знижка' },
          { title: 'Оплата' },
        ]}
        style={{ marginBottom: 24 }}
      />

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={15}>
          {step === 0 && (
            <Row gutter={[16, 16]}>
              {catalog.tariffs.map((t) => (
                <Col key={t.id} xs={24} sm={12}>
                  <SelectCard active={t.id === tariffId} onClick={() => setTariffId(t.id)}>
                    <Flex vertical gap={4}>
                      <Flex justify="space-between">
                        <Tag color="orange">{TARIFF_TYPE_LABELS[t.type]}</Tag>
                        {t.id === tariffId && (
                          <CheckOutlined style={{ color: 'var(--fc-primary)' }} />
                        )}
                      </Flex>
                      <Text strong style={{ fontSize: 16 }}>
                        {t.name}
                      </Text>
                      <span className="price">{formatMoney(t.price)}</span>
                      <Text type="secondary">{tariffSummary(t)}</Text>
                    </Flex>
                  </SelectCard>
                </Col>
              ))}
            </Row>
          )}

          {step === 1 && (
            <Flex vertical gap={12}>
              <Text type="secondary">Необовʼязково: додайте послуги до абонемента</Text>
              {catalog.options.map((o) => (
                <SelectCard
                  key={o.id}
                  active={optionIds.includes(o.id)}
                  onClick={() => toggleOption(o.id)}
                >
                  <Flex justify="space-between" align="center" gap={12}>
                    <Checkbox checked={optionIds.includes(o.id)} tabIndex={-1}>
                      <Text strong>{o.name}</Text>
                    </Checkbox>
                    <Text strong style={{ color: 'var(--fc-primary-dark)' }}>
                      +{formatMoney(o.price)}
                    </Text>
                  </Flex>
                </SelectCard>
              ))}
            </Flex>
          )}

          {step === 2 && (
            <Flex vertical gap={16}>
              <Text type="secondary">Одна знижка на покупку. Умови перевіряє система.</Text>
              <Radio.Group
                value={discountType}
                onChange={(e) => setDiscountType(e.target.value)}
                style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
              >
                {DISCOUNTS.map((d) => (
                  <Radio key={d.value} value={d.value}>
                    <Text strong>{d.label}</Text>
                    {d.hint && (
                      <Text type="secondary" style={{ display: 'block' }}>
                        {d.hint}
                      </Text>
                    )}
                  </Radio>
                ))}
              </Radio.Group>
              {discount.reference && (
                <div style={{ maxWidth: 320 }}>
                  <Text>{discount.reference.label}</Text>
                  <Input
                    value={reference}
                    onChange={(e) => setReference(e.target.value)}
                    placeholder={discount.reference.placeholder}
                    maxLength={50}
                    style={{ marginTop: 4 }}
                  />
                </div>
              )}
            </Flex>
          )}

          {step === 3 && quote && (
            <Card className="soft-card">
              <Flex vertical gap={12}>
                <Text>
                  Тариф: <Text strong>{tariff.name}</Text>
                </Text>
                <Text>
                  Діє: <Text strong>{dayjs(quote.start_date).format(DATE)}</Text> –{' '}
                  <Text strong>{dayjs(quote.end_date).format(DATE)}</Text>
                  {quote.visits_left !== null && ` · ${visits(quote.visits_left)}`}
                </Text>
                {startsLater && (
                  <Alert
                    type="info"
                    showIcon
                    title="Новий абонемент почнеться після закінчення поточного"
                  />
                )}
                <Radio checked>
                  <CreditCardOutlined /> Онлайн-оплата карткою
                </Radio>
                <Text type="secondary">
                  Навчальний проєкт: оплата імітується, кошти не списуються.
                </Text>
                {payError && <Alert type="error" showIcon title={getErrorMessage(payError)} />}
                <Button
                  type="primary"
                  size="large"
                  block
                  loading={paying}
                  disabled={pending || Boolean(quoteError)}
                  onClick={pay}
                >
                  Оплатити {formatMoney(quote.total)}
                </Button>
              </Flex>
            </Card>
          )}

          <Flex justify="space-between" style={{ marginTop: 24 }}>
            <Button disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
              Назад
            </Button>
            {step < 3 && (
              <Button type="primary" disabled={!canGoNext} onClick={() => setStep((s) => s + 1)}>
                Далі
              </Button>
            )}
          </Flex>
        </Col>

        <Col xs={24} lg={9}>
          <PriceSummary quote={quote} error={quoteError} pending={pending} />
        </Col>
      </Row>
    </>
  );
}
