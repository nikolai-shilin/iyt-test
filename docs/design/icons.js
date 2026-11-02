/* Base icon set — the single source for the flows and the exported SVG files.
   24×24 grid, 2px stroke, round caps and joins, no fill (currentColor). Keep 2px clear of the edges.
   Some basic glyphs follow Lucide (ISC License, see icons/LICENSE-lucide.txt); transport, transfer and
   transport and manager glyphs are drawn for the mini app. */

// Plane, top view, nose to the right; turned and scaled for arrival / departure.
const PLANE = 'M19.5 10.5H14L10 3.5H8l2 7H6L4.5 7.5H3l.8 4.5-.8 4.5h1.5L6 13.5h4l-2 7h2l4-7h5.5a1.5 1.5 0 0 0 0-3z';
// A scaled-down plane keeps the 2px line by widening its stroke in its own units (2 / scale).
const planeAt = (deg, dy = 0, s = 1) =>
  `<path transform="translate(12 ${12 + dy}) rotate(${deg}) scale(${s}) translate(-12 -12)"${s === 1 ? '' : ` stroke-width="${+(2 / s).toFixed(3)}"`} d="${PLANE}"/>`;

const RYC_ICON_GROUPS = [
  ['route', 'Маршрут и точки'],
  ['vehicle', 'Машина, люди, багаж'],
  ['time', 'Время'],
  ['talk', 'Связь'],
  ['money', 'Цена и оплата'],
  ['status', 'Статусы'],
  ['action', 'Действия'],
  ['manager', 'Менеджер'],
  ['included', 'Что включено'],
];

const RYC_ICONS = [
  // route
  { name: 'plane', group: 'route', ru: 'Аэропорт', svg: planeAt(-45) },
  { name: 'plane-arrival', group: 'route', ru: 'Прилёт, забрать в аэропорту', svg: planeAt(25, -2.5, 0.8) + '<path d="M3 21h18"/>' },
  { name: 'plane-departure', group: 'route', ru: 'Вылет, отвезти в аэропорт', svg: planeAt(-25, -2.5, 0.8) + '<path d="M3 21h18"/>' },
  { name: 'anchor', group: 'route', ru: 'Марина', svg: '<path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/><circle cx="12" cy="5" r="3"/>' },
  { name: 'yacht', group: 'route', ru: 'Яхта', svg: '<path d="M11 3 4 15h7z"/><path d="M13.5 6.5v8.5h5.5z"/><path d="M3 18h18l-1.6 2.5a1 1 0 0 1-.8.5H5.4a1 1 0 0 1-.8-.5z"/>' },
  { name: 'pin', group: 'route', ru: 'Место на карте', svg: '<path d="M20 10c0 5-5.5 10.2-7.4 11.8a1 1 0 0 1-1.2 0C9.5 20.2 4 15 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>' },
  { name: 'pin-add', group: 'route', ru: 'Добавить остановку', svg: '<path d="M20 10c0 5-5.5 10.2-7.4 11.8a1 1 0 0 1-1.2 0C9.5 20.2 4 15 4 10a8 8 0 0 1 16 0"/><path d="M12 7v6M9 10h6"/>' },
  { name: 'route', group: 'route', ru: 'Маршрут', svg: '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h8.5a3.5 3.5 0 0 0 0-7h-9a3.5 3.5 0 0 1 0-7H16"/>' },
  { name: 'map', group: 'route', ru: 'Карта', svg: '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>' },
  { name: 'locate', group: 'route', ru: 'Моё местоположение', svg: '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>' },
  { name: 'search', group: 'route', ru: 'Поиск', svg: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>' },
  { name: 'bed', group: 'route', ru: 'Отель', svg: '<path d="M3 18V6M3 13h18v5M21 13a3 3 0 0 0-3-3h-7v3"/><circle cx="7" cy="10" r="2"/>' },
  { name: 'home', group: 'route', ru: 'Вилла, дом', svg: '<path d="M3 11 12 4l9 7"/><path d="M5 9.5V20h14V9.5"/><path d="M10 20v-5h4v5"/>' },
  { name: 'cart', group: 'route', ru: 'Супермаркет', svg: '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.4a2 2 0 0 0 2 1.6h8.6a2 2 0 0 0 2-1.6L22 7H6"/>' },

  // vehicle, people, luggage
  { name: 'van', group: 'vehicle', ru: 'Минивэн · Vito / Transporter', svg: '<path d="M5 17H3v-6l2-5h11l5 5v6h-2"/><path d="M9.5 17h5M3 11h18M10 6v5"/><circle cx="7.5" cy="17" r="2"/><circle cx="16.5" cy="17" r="2"/>' },
  { name: 'bus', group: 'vehicle', ru: 'Sprinter, до 12 мест', svg: '<path d="M4.5 17H2V7a2 2 0 0 1 2-2h14l4 5v7h-2"/><path d="M8.5 17h7.5M2 10h20M7 5v5M12 5v5M17 5v5"/><circle cx="6.5" cy="17" r="2"/><circle cx="18" cy="17" r="2"/>' },
  { name: 'driver', group: 'vehicle', ru: 'Водитель', svg: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5"/><path d="M12 14.5V21M9.6 11.3 3.3 9.6M14.4 11.3l6.3-1.7"/>' },
  { name: 'plate', group: 'vehicle', ru: 'Номер машины', svg: '<rect x="2" y="7" width="20" height="10" rx="2"/><path d="M6 12h2M10.5 12h3M16 12h2"/>' },
  { name: 'user', group: 'vehicle', ru: 'Пассажир', svg: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>' },
  { name: 'users', group: 'vehicle', ru: 'Пассажиры', svg: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>' },
  { name: 'child', group: 'vehicle', ru: 'Ребёнок', svg: '<circle cx="12" cy="7.5" r="3.5"/><path d="M7 21v-2.5a5 5 0 0 1 10 0V21"/><path d="M10.5 7h.01M13.5 7h.01"/>' },
  { name: 'seat', group: 'vehicle', ru: 'Детское кресло', svg: '<path d="M7 3h3.5A1.5 1.5 0 0 1 12 4.5V12l5 1.2a2 2 0 0 1 1.5 1.9V19H7.5A1.5 1.5 0 0 1 6 17.5V4a1 1 0 0 1 1-1z"/><path d="M4 21h16M9 9h3"/>' },
  { name: 'luggage', group: 'vehicle', ru: 'Багаж', svg: '<rect x="6" y="7" width="12" height="13" rx="2"/><path d="M9 7V4h6v3M10 20v1.5M14 20v1.5M10 11v5M14 11v5"/>' },
  { name: 'board', group: 'vehicle', ru: 'Крупногабарит, SUP', svg: '<path d="M18.5 3.5c1.6 1.6-1.2 7.4-6.3 12.6S2.6 22.1 2 21.5s.3-5.5 5.4-10.6 9.5-9 11.1-7.4z"/><path d="m9 15 1.5 1.5M13 11l1.5 1.5"/>' },

  // time
  { name: 'clock', group: 'time', ru: 'Время', svg: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>' },
  { name: 'calendar', group: 'time', ru: 'Дата', svg: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>' },
  { name: 'wait', group: 'time', ru: 'Ожидание на остановке', svg: '<path d="M5 3h14M5 21h14"/><path d="M7 3v2.5a5 5 0 0 0 2.2 4.1L12 12l2.8-2.4A5 5 0 0 0 17 5.5V3"/><path d="M7 21v-2.5a5 5 0 0 1 2.2-4.1L12 12l2.8 2.4a5 5 0 0 1 2.2 4.1V21"/>' },
  { name: 'delay', group: 'time', ru: 'Задержка рейса', svg: '<path d="M21 12.5A9 9 0 1 1 11.5 3"/><path d="M12 7v5l3 2"/><path d="M19 3v4M19 10h.01"/>' },

  // talk
  { name: 'chat', group: 'talk', ru: 'Сообщение менеджеру', svg: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' },
  { name: 'phone', group: 'talk', ru: 'Позвонить', svg: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>' },
  { name: 'send', group: 'talk', ru: 'Отправить', svg: '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>' },
  { name: 'bell', group: 'talk', ru: 'Напоминание', svg: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>' },
  { name: 'sign', group: 'talk', ru: 'Встреча с табличкой', svg: '<rect x="3" y="4" width="18" height="10" rx="1.5"/><path d="M7 9h10M8 14v7M16 14v7"/>' },

  // money
  { name: 'euro', group: 'money', ru: 'Цена, €', svg: '<path d="M4 10h12M4 14h9M19 6a7.7 7.7 0 0 0-5.2-2A7.9 7.9 0 0 0 6 12c0 4.4 3.5 8 7.8 8 2 0 3.8-.8 5.2-2"/>' },
  { name: 'cash', group: 'money', ru: 'Наличными водителю', svg: '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>' },
  { name: 'estimate', group: 'money', ru: 'Оценка стоимости', svg: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M8 13h3M8 17h6"/>' },

  // status
  { name: 'check', group: 'status', ru: 'Готово', svg: '<path d="M20 6 9 17l-5-5"/>' },
  { name: 'check-circle', group: 'status', ru: 'Подтверждён', svg: '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.5 2.5L16 9.5"/>' },
  { name: 'alert', group: 'status', ru: 'Внимание', svg: '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>' },
  { name: 'info', group: 'status', ru: 'Подсказка', svg: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>' },
  { name: 'x', group: 'status', ru: 'Закрыть, отменить', svg: '<path d="M18 6 6 18M6 6l12 12"/>' },
  { name: 'shield', group: 'status', ru: 'Страховка, приватность', svg: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>' },
  { name: 'star', group: 'status', ru: 'Оценка поездки', svg: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>' },

  // actions
  { name: 'plus', group: 'action', ru: 'Добавить', svg: '<path d="M5 12h14M12 5v14"/>' },
  { name: 'minus', group: 'action', ru: 'Убавить', svg: '<path d="M5 12h14"/>' },
  { name: 'edit', group: 'action', ru: 'Изменить', svg: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>' },
  { name: 'trash', group: 'action', ru: 'Удалить', svg: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>' },
  { name: 'copy', group: 'action', ru: 'Копировать', svg: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>' },
  { name: 'swap', group: 'action', ru: 'Обратный трансфер', svg: '<path d="M7 4v16M7 4 3 8M7 4l4 4M17 20V4M17 20l-4-4M17 20l4-4"/>' },
  { name: 'grip', group: 'action', ru: 'Перетащить', svg: '<path d="M9 6h.01M15 6h.01M9 12h.01M15 12h.01M9 18h.01M15 18h.01" stroke-width="3"/>' },
  { name: 'back', group: 'action', ru: 'Назад', svg: '<path d="m15 18-6-6 6-6"/>' },
  { name: 'next', group: 'action', ru: 'Дальше', svg: '<path d="M5 12h14M13 6l6 6-6 6"/>' },
  { name: 'down', group: 'action', ru: 'Раскрыть', svg: '<path d="m6 9 6 6 6-6"/>' },
  { name: 'filter', group: 'action', ru: 'Фильтр', svg: '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>' },
  { name: 'refresh', group: 'action', ru: 'Повторить поездку', svg: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>' },
  { name: 'more', group: 'action', ru: 'Ещё', svg: '<circle cx="12" cy="12" r="9"/><path d="M8 12h.01M12 12h.01M16 12h.01" stroke-width="2.5"/>' },

  // manager
  { name: 'inbox', group: 'manager', ru: 'Входящие', svg: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z"/>' },
  { name: 'schedule', group: 'manager', ru: 'Расписание', svg: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18M7 14h4M7 17h7"/>' },
  { name: 'board-view', group: 'manager', ru: 'Диспетчерская', svg: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M15 4v16"/><path d="M5.5 8h1M11.5 8h1M17.5 8h1M11.5 11h1"/>' },
  { name: 'take', group: 'manager', ru: 'Взять запрос', svg: '<path d="M18 11V6a2 2 0 0 0-4 0v1M14 10V4a2 2 0 0 0-4 0v2M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.9-5.9-2.4L3.6 16.6a2 2 0 0 1 2.8-2.9L8 15"/>' },
  { name: 'decline', group: 'manager', ru: 'Отклонить', svg: '<circle cx="12" cy="12" r="9"/><path d="m5.7 5.7 12.6 12.6"/>' },

  // included
  { name: 'snow', group: 'included', ru: 'Кондиционер', svg: '<path d="M12 2v20M2 12h20M5 5l14 14M19 5 5 19"/><path d="m9 4 3 2 3-2M9 20l3-2 3 2M4 9l2 3-2 3M20 9l-2 3 2 3"/>' },
  { name: 'drop', group: 'included', ru: 'Холодная вода', svg: '<path d="M12 2.7 6.3 9a7 7 0 1 0 11.4 0z"/>' },
  { name: 'wifi', group: 'included', ru: 'Wi-Fi', svg: '<path d="M5 12.6a10 10 0 0 1 14 0M8.5 16.1a5 5 0 0 1 7 0M2 8.8a15 15 0 0 1 20 0"/><path d="M12 20h.01"/>' },

  // Telegram chrome in the mockups only — not part of the app set.
  { name: 'dots', group: 'chrome', ru: 'Меню Telegram', svg: '<circle cx="5" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="19" cy="12" r="1.5" fill="currentColor"/>' },
  { name: 'clip', group: 'chrome', ru: 'Вложение', svg: '<path d="m21.4 11-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5"/>' },
  { name: 'mic', group: 'chrome', ru: 'Голосовое', svg: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10a7 7 0 0 1-14 0M12 19v3"/>' },
  { name: 'status', group: 'chrome', ru: 'Статус-бар iOS', svg: '<path d="M2 18h2v-3H2zM6 18h2v-6H6zM10 18h2V9h-2zM14 18h2V6h-2z" fill="currentColor" stroke="none"/><rect x="17.5" y="8" width="5" height="9" rx="1.5"/>' },
];

const RYC_ICON_INDEX = Object.fromEntries(RYC_ICONS.map(i => [i.name, i]));

function rycIcon(name, size = 24, attrs = '') {
  const i = RYC_ICON_INDEX[name];
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="2" ` +
    `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" ${attrs}>${i ? i.svg : ''}</svg>`;
}

// "64 иконки", "21 иконка", "65 иконок".
function rycIconsCount(n) {
  const a = n % 10, b = n % 100;
  const w = a === 1 && b !== 11 ? 'иконка' : a >= 2 && a <= 4 && (b < 12 || b > 14) ? 'иконки' : 'иконок';
  return `${n} ${w}`;
}

if (typeof module !== 'undefined') module.exports = { RYC_ICONS, RYC_ICON_GROUPS, rycIcon };
