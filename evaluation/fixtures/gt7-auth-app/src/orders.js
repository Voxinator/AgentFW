// orders.js — tiny in-memory order data, keyed by username.

'use strict';

const orders = new Map([
  ['alice', [
    { id: 'ord-1001', item: 'mechanical keyboard', total: 129.0, status: 'shipped' },
    { id: 'ord-1002', item: 'usb-c dock',          total: 89.5,  status: 'processing' },
  ]],
  ['bob', [
    { id: 'ord-2001', item: 'standing desk', total: 449.0, status: 'delivered' },
  ]],
]);

function ordersFor(username) {
  return orders.get(username) || [];
}

module.exports = { ordersFor };
