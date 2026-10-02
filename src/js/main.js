// Initial skeleton. Hoàng Quân owns interactions and layer transitions, Xuân Quế owns the main charts.
// State shared across the 3 layers.
const state = {
  layer: 'region',      // 'region' | 'country' | 'indicator'
  indicator: null,
  year: null,
  country: 'Viet Nam',
  selectedCountries: [] // countries currently displayed
};

// JSON data is exported into the data/ folder by Lê Quân (see data/README.md).
// Example: fetch('../data/indicators.json').then(r => r.json()).then(init);
