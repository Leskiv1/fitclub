// Ant Design theme based on the Stitch design tokens (docs/design/DESIGN.md)
const theme = {
  token: {
    colorPrimary: '#FF6B35',
    colorInfo: '#00668A',
    colorError: '#BA1A1A',
    colorBgLayout: '#F8F9FB',
    colorText: '#191C1E',
    fontFamily: "'Manrope', system-ui, -apple-system, 'Segoe UI', sans-serif",
    borderRadius: 8,
  },
  components: {
    Layout: {
      siderBg: '#2E3132',
      headerBg: '#FFFFFF',
      triggerBg: '#2E3132',
    },
    // Staff side menu: graphite background, orange active item
    Menu: {
      darkItemBg: '#2E3132',
      darkSubMenuItemBg: '#2E3132',
      darkItemColor: '#C3C6CE',
      darkItemHoverColor: '#FFFFFF',
      darkItemSelectedBg: '#FF6B35',
      darkItemSelectedColor: '#FFFFFF',
    },
  },
};

export default theme;
