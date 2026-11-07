import { Flex, Spin } from 'antd';

export default function PageSpinner() {
  return (
    <Flex justify="center" align="center" style={{ minHeight: 240 }}>
      <Spin size="large" />
    </Flex>
  );
}
