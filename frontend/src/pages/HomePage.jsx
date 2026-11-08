import { useState } from 'react';
import {
  ClockCircleOutlined,
  EnvironmentOutlined,
  MailOutlined,
  PhoneOutlined,
} from '@ant-design/icons';
import { Button, Card, Col, Empty, Flex, Row, Tag, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { fetchOptions, fetchSettings, fetchTariffs, fetchTrainers } from '../api/catalog';
import { fetchWeekSessions } from '../api/sessions';
import heroTrainer from '../assets/hero-trainer.jpg';
import { CLIENT } from '../auth/roles';
import useAuth from '../auth/useAuth';
import LoadError from '../components/LoadError';
import PageSpinner from '../components/PageSpinner';
import SessionRow from '../components/SessionRow';
import TrainerAvatar from '../components/TrainerAvatar';
import WeekDayPicker from '../components/WeekDayPicker';
import useApi from '../hooks/useApi';
import useSectionHash, { scrollToSection } from '../hooks/useSectionHash';
import { clubTime, dayjs, ISO_DATE, weekStart } from '../utils/dates';
import {
  formatMoney,
  groupOpeningHours,
  sortTariffs,
  TARIFF_TYPE_LABELS,
  tariffSummary,
  WEEKDAYS_SHORT,
} from '../utils/format';

const { Title, Text, Paragraph } = Typography;

// Sections the hero buttons lead to; the URL hash follows them while scrolling
const SECTION_IDS = ['tariffs', 'schedule'];

async function loadLanding() {
  const [tariffs, options, trainers, settings, sessions] = await Promise.all([
    fetchTariffs(),
    fetchOptions(),
    fetchTrainers(),
    fetchSettings(),
    fetchWeekSessions({ kind: 'group' }),
  ]);
  return {
    tariffs: sortTariffs(tariffs.filter((t) => t.is_active)),
    options: options.filter((o) => o.is_active),
    trainers,
    settings,
    sessions,
  };
}

function workDays(trainer) {
  const days = [...new Set(trainer.work_shifts.map((s) => s.weekday))].sort();
  return days.map((d) => WEEKDAYS_SHORT[d]).join(', ');
}

function HeroStat({ value, label }) {
  return (
    <div className="hero__stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

// Every card has the same rows in the same order; the description stretches,
// so prices line up and the "Обрати" buttons sit on one line across a row
function TariffCard({ tariff, canBuy }) {
  return (
    <Card className="soft-card tariff-card">
      <Tag color="orange" className="tariff-card__tag">
        {TARIFF_TYPE_LABELS[tariff.type]}
      </Tag>
      <Title level={4} ellipsis={{ tooltip: tariff.name }} className="tariff-card__name">
        {tariff.name}
      </Title>
      <span className="price">{formatMoney(tariff.price)}</span>
      <Text type="secondary">{tariffSummary(tariff)}</Text>
      <Paragraph className="tariff-card__description">{tariff.description}</Paragraph>
      {canBuy && (
        <Link to={`/my/purchase?tariff=${tariff.id}`}>
          <Button type="primary" size="large" block>
            Обрати
          </Button>
        </Link>
      )}
    </Card>
  );
}

// Public landing: tariffs, trainers, this week's group schedule, club hours (guest use cases)
export default function HomePage() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useApi(loadLanding);
  const monday = weekStart(dayjs());
  const [day, setDay] = useState(() => (dayjs().day() + 6) % 7);
  useSectionHash(Boolean(data), SECTION_IDS);

  if (loading && !data) return <PageSpinner />;
  if (error && !data) return <LoadError error={error} onRetry={reload} />;

  // Guests are asked to sign in first (RequireRole), clients go straight to the purchase
  const canBuy = !user || user.role === CLIENT;
  const { tariffs, options, trainers, settings, sessions } = data;
  const selectedDate = monday.add(day, 'day').format(ISO_DATE);
  const daySessions = sessions.filter(
    (s) => clubTime(s.start_at).format(ISO_DATE) === selectedDate,
  );

  return (
    <>
      <section className="hero">
        <div className="hero__inner">
          <div className="hero__content">
            <h1>FitClub — простір твоєї трансформації</h1>
            <p>
              Сучасний фітнес-клуб: групові програми, персональні тренування з сертифікованими
              тренерами та абонементи під ваш ритм.
            </p>
            <Flex gap={12} wrap>
              <Button type="primary" size="large" onClick={() => scrollToSection('tariffs')}>
                Обрати абонемент
              </Button>
              <Button size="large" ghost onClick={() => scrollToSection('schedule')}>
                Розклад занять
              </Button>
            </Flex>
            <div className="hero__stats">
              <HeroStat value={trainers.length} label="тренерів" />
              <HeroStat value={sessions.length} label="групових занять цього тижня" />
              <HeroStat value={tariffs.length} label="тарифів" />
            </div>
          </div>
          <div className="hero__photo">
            <img src={heroTrainer} alt="Тренер FitClub у залі клубу" />
          </div>
        </div>
      </section>

      <div className="page" style={{ paddingTop: 0 }}>
        <section id="tariffs" className="section">
          <Title level={2}>Тарифи та абонементи</Title>
          <Text className="page-subtitle">Ціна залежить від тарифу, опцій і знижки</Text>
          <Row gutter={[24, 24]}>
            {tariffs.map((tariff) => (
              <Col key={tariff.id} xs={24} md={12} lg={8}>
                <TariffCard tariff={tariff} canBuy={canBuy} />
              </Col>
            ))}
          </Row>
          {options.length > 0 && (
            <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
              Додаткові опції до абонемента:{' '}
              {options.map((o) => `${o.name} (+${formatMoney(o.price)})`).join(' · ')}
            </Text>
          )}
        </section>

        <section className="section">
          <Title level={2}>Наші тренери</Title>
          <Text className="page-subtitle">Персональні заняття — у кабінеті клієнта</Text>
          <Row gutter={[16, 16]}>
            {trainers.map((trainer) => (
              <Col key={trainer.id} xs={24} md={12}>
                <Card className="soft-card" style={{ height: '100%' }}>
                  <Flex gap={16}>
                    <TrainerAvatar trainer={trainer} size={64} />
                    <Flex vertical gap={4} style={{ minWidth: 0 }}>
                      <Title level={5} style={{ margin: 0 }}>
                        {trainer.full_name}
                      </Title>
                      <Text type="secondary">{trainer.specialization}</Text>
                      {trainer.bio && (
                        <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0 }}>
                          {trainer.bio}
                        </Paragraph>
                      )}
                      {trainer.work_shifts.length > 0 && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          Працює: {workDays(trainer)}
                        </Text>
                      )}
                    </Flex>
                  </Flex>
                </Card>
              </Col>
            ))}
          </Row>
        </section>

        <section id="schedule" className="section">
          <Flex justify="space-between" align="end" wrap gap={8}>
            <div>
              <Title level={2}>Розклад групових занять</Title>
              <Text className="page-subtitle">Поточний тиждень</Text>
            </div>
            {canBuy && (
              <Link to="/my/schedule">
                <Button>Записатися на заняття</Button>
              </Link>
            )}
          </Flex>
          <WeekDayPicker monday={monday} value={day} onChange={setDay} />
          <Flex vertical gap={12} style={{ marginTop: 16 }}>
            {daySessions.length ? (
              daySessions.map((s) => <SessionRow key={s.id} session={s} />)
            ) : (
              <Empty description="Цього дня групових занять немає" />
            )}
          </Flex>
        </section>

        <section className="section">
          <Title level={2}>Контакти та години роботи</Title>
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} md={12}>
              <Card className="soft-card" style={{ height: '100%' }}>
                <Flex vertical gap={8}>
                  <Text>
                    <EnvironmentOutlined /> м. Київ, вул. Спортивна, 14
                  </Text>
                  <Text>
                    <PhoneOutlined /> +380 44 123 45 67
                  </Text>
                  <Text>
                    <MailOutlined /> info@fitclub.example
                  </Text>
                </Flex>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card className="soft-card" style={{ height: '100%' }}>
                <Flex vertical gap={8}>
                  <Text strong>
                    <ClockCircleOutlined /> Години роботи
                  </Text>
                  {groupOpeningHours(settings.opening_hours).map((row) => (
                    <Flex key={row.days} justify="space-between">
                      <Text>{row.days}</Text>
                      <Text strong>{row.hours}</Text>
                    </Flex>
                  ))}
                </Flex>
              </Card>
            </Col>
          </Row>
        </section>
      </div>
    </>
  );
}
