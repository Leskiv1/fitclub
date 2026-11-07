import { useState } from 'react';
import { Alert, Checkbox, Col, Form, Input, Modal, Radio, Row, Select } from 'antd';
import { fetchOptions, fetchTariffs } from '../../api/catalog';
import { purchaseMembership } from '../../api/memberships';
import useApi from '../../hooks/useApi';
import useQuote from '../../hooks/useQuote';
import { buildDiscount, discountByValue, DISCOUNTS } from '../../utils/discounts';
import { getErrorMessage } from '../../utils/errors';
import { formatMoney, sortTariffs, tariffSummary } from '../../utils/format';
import PriceSummary from '../PriceSummary';

async function loadCatalog() {
  const [tariffs, options] = await Promise.all([fetchTariffs(), fetchOptions()]);
  return {
    tariffs: sortTariffs(tariffs.filter((t) => t.is_active)),
    options: options.filter((o) => o.is_active),
  };
}

// Ф-5 at the reception: the same purchase facade as the client's page, but for a chosen client
// and paid in cash or by card
export default function SellMembershipModal({ clientId, open, onClose, onSold }) {
  const { data: catalog } = useApi(loadCatalog);
  const [tariffId, setTariffId] = useState(null);
  const [optionIds, setOptionIds] = useState([]);
  const [discountType, setDiscountType] = useState('none');
  const [reference, setReference] = useState('');
  const [payment, setPayment] = useState('cash');
  const [paying, setPaying] = useState(false);
  const [payError, setPayError] = useState(null);

  const payload = tariffId
    ? {
        client_id: clientId,
        tariff_id: tariffId,
        option_ids: optionIds,
        discount: buildDiscount(discountType, reference),
      }
    : null;
  const { quote, error: quoteError, pending } = useQuote(open ? payload : null);
  const discount = discountByValue(discountType);

  const pay = async () => {
    setPaying(true);
    setPayError(null);
    try {
      onSold(await purchaseMembership(payload, payment));
    } catch (err) {
      setPayError(err);
    } finally {
      setPaying(false);
    }
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="Оформлення абонемента"
      width={820}
      destroyOnHidden
      okText={quote ? `Оплатити ${formatMoney(quote.total)}` : 'Оплатити'}
      okButtonProps={{ disabled: !quote || pending || Boolean(quoteError), loading: paying }}
      onOk={pay}
      cancelText="Скасувати"
    >
      <Row gutter={24}>
        <Col xs={24} md={13}>
          <Form layout="vertical">
            <Form.Item label="Тариф" required>
              <Select
                value={tariffId}
                onChange={setTariffId}
                placeholder="Оберіть тариф"
                loading={!catalog}
                options={(catalog?.tariffs ?? []).map((t) => ({
                  value: t.id,
                  label: `${t.name} — ${formatMoney(t.price)} (${tariffSummary(t)})`,
                }))}
              />
            </Form.Item>
            <Form.Item label="Додаткові опції">
              <Checkbox.Group
                value={optionIds}
                onChange={setOptionIds}
                options={(catalog?.options ?? []).map((o) => ({
                  value: o.id,
                  label: `${o.name} (+${formatMoney(o.price)})`,
                }))}
              />
            </Form.Item>
            <Form.Item label="Знижка" extra={discount.hint}>
              <Select
                value={discountType}
                onChange={(v) => {
                  setDiscountType(v);
                  setReference('');
                }}
                options={DISCOUNTS.map((d) => ({ value: d.value, label: d.label }))}
              />
            </Form.Item>
            {discount.reference && (
              <Form.Item label={discount.reference.label}>
                <Input
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                  placeholder={discount.reference.placeholder}
                  maxLength={50}
                />
              </Form.Item>
            )}
            <Form.Item label="Оплата">
              <Radio.Group
                value={payment}
                onChange={(e) => setPayment(e.target.value)}
                optionType="button"
                options={[
                  { value: 'cash', label: 'Готівка' },
                  { value: 'card', label: 'Картка (термінал)' },
                ]}
              />
            </Form.Item>
          </Form>
        </Col>
        <Col xs={24} md={11}>
          <PriceSummary quote={quote} error={quoteError} pending={pending} bordered={false} />
          {payError && (
            <Alert
              type="error"
              showIcon
              title={getErrorMessage(payError)}
              style={{ marginTop: 12 }}
            />
          )}
        </Col>
      </Row>
    </Modal>
  );
}
