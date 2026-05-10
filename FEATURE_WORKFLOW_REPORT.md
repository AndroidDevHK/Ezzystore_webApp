# EzzyStore Feature Workflow Report

## Purpose

This document explains the main features of EzzyStore WebApp and how each one works in practice.

It is meant to answer:

- what feature exists
- what data it uses
- what happens when a user performs an action
- how balances, stock, sales, and profit are affected

## 1. Authentication And Access Control

### What it does

Handles login, logout, and role-based access.

### Roles

- `admin`
- `manager`

### How it works

1. User opens login page.
2. Username and password are checked against the `users` table.
3. If valid:
   - session stores user id, username, and role
4. If role is `admin`:
   - user goes to admin dashboard
5. If role is `manager`:
   - app checks assigned shop
   - if a shop exists, manager session also stores shop data
   - user goes to manager dashboard

### Important behavior

- manager access only works if the manager is assigned to a shop
- admin and manager routes are protected separately

## 2. Admin Shop Management

### What it does

Lets the admin create shops and assign managers.

### Main actions

- create shop
- create manager account
- assign manager to shop
- view shop list and assignment status

### How it works

1. Admin creates a shop.
2. Shop is stored in `shops`.
3. Admin creates a manager.
4. Manager user is stored in `users`.
5. Assignment is stored in `shop_managers`.

### Rules

- one shop can have only one manager
- one manager can be assigned to only one shop

## 3. Manager Dashboard

### What it does

Shows shop activity summary and gives entry points to all manager features.

### Main information shown

- product totals
- stock totals
- out-of-stock items
- digital cash
- counter cash
- wallet cash
- Easyload cash
- package profit
- quick action buttons

### How it works

The dashboard is built from:

- products
- stock batches
- sales
- service transactions
- system cash entries
- profit history
- customer data

The manager context builder prepares all page data before rendering.

## 4. Product Management

### What it does

Allows manager to manage the product catalog.

### Main actions

- create product
- update product
- view product with category and brand
- delete product safely

### How it works

1. Manager enters product name.
2. Manager selects category and optional brand.
3. Product is stored in `products`.
4. Product has:
   - current quantity
   - display price
   - reorder level
   - category
   - brand

### Safe deletion behavior

Product deletion is blocked if:

- sale history exists
- stock batch history exists
- current stock is greater than zero

This protects old records from being lost.

## 5. Brand Management

### What it does

Groups products under brands.

### Main actions

- create brand
- rename brand
- open brand detail page

### How it works

- Brands are stored per shop.
- Brand detail page filters products belonging to that brand.

## 6. Category Management

### What it does

Groups products under categories.

### Main actions

- create category
- rename category
- open category detail page

### How it works

- Categories are stored per shop.
- Category detail page filters products belonging to that category.

## 7. Stock Management

### What it does

Tracks inventory quantity and purchase history.

### Main actions

- add stock for one product
- add stock for multiple products in one restock operation
- record purchase rate
- record sale price
- record restock date
- inspect stock batch details
- inspect product purchase history

### How it works

When stock is added:

1. Product quantity increases in `products`
2. A detailed restock row is added in `stock_batches`

Each stock batch stores:

- product id
- quantity
- purchase rate
- sale price
- batch date
- created time

### Why stock batches matter

They are used for:

- purchase history
- stock history
- product costing
- reporting

## 8. Sales Recording

### What it does

Records product sales and updates stock and counter cash.

### Main actions

- select one or multiple products
- set quantity
- set sale price
- link optional customer
- confirm sale

### How it works

When a sale is recorded:

1. App validates selected products and quantities.
2. App checks stock availability.
3. App calculates sale line values.
4. Product quantity is reduced.
5. Sale header is stored in `sales`.
6. Sale items are stored in `sale_items`.
7. Counter cash gets a `Sale #id` cash-in entry.

### Cost behavior

Each sale item now stores:

- `unit_price`
- `unit_cost`

This is important because:

- profit reporting uses stored cost
- old reports do not change when new restocks happen later

## 9. Expense-Based Selling

### What it does

Allows sale price to be calculated from cost plus expense percentage.

### How it works

1. Shop settings store an `expense_percent`.
2. If expense-based selling is selected:
   - app gets product cost
   - app calculates sale price = cost + configured percentage
3. That price is used in the sale

### Why it exists

It supports businesses that want cost-based selling instead of manual price entry.

## 10. Customer Management

### What it does

Stores customer records and links them to sales.

### Main actions

- create customer
- store name and phone
- search customer while selling
- delete customer

### How it works

1. Customer is stored in `customers`.
2. Sale may include a `customer_id`.
3. Reports and customer insights use this link.

### Extra behavior

The manager context also builds customer insights, such as:

- purchased item count
- total spent
- estimated purchase cost
- estimated profit percent
- last purchase date

## 11. Sale Return Flow

### What it does

Handles item returns from an existing sale.

### Main actions

- open sale return page for a sale
- choose items to return
- choose quantity to return
- confirm return

### How it works

1. App loads the original sale.
2. App checks what quantities are still returnable.
3. Manager chooses return items and quantities.
4. App restores stock for returned quantity.
5. App creates a new `return` sale entry linked by `reference_sale_id`.
6. App deducts refund amount from counter cash.
7. Original `sale_items.returned_quantity` is updated.

### Safety behavior

- return price is not trusted from browser input
- refund amount comes from original sale item data on server
- direct fake returns through the generic sales endpoint are blocked

### Supports

- partial returns
- full returns
- linked history

## 12. Counter Cash System

### What it does

Tracks physical/manual cash in the shop.

### Main actions

- manual cash in
- manual cash out
- automatic cash entries from business events
- cash history

### How it works

Counter cash is stored in `system_cash_entries`.

Each entry includes:

- amount
- type
  - `add`
  - `expense`
- message
- created time

### Counter cash changes automatically from

- product sales
- product returns
- wallet cash transfers
- Easyload purchase transfers
- wallet refresh sold differences
- Easyload refresh sold differences
- wallet profit moved to counter
- package profit

## 13. Wallet Cash Management

### Supported channels

- Easypaisa
- JazzCash

### Main actions

- cash in
- cash out
- profit in
- move wallet profit to counter
- refresh wallet balance

### How it works

Wallet activity is stored in `service_transactions`.

Important wallet entry types:

- `cash_in`
- `cash_out`
- `profit_in`

### Cash In workflow

1. Money is transferred from counter cash to wallet.
2. Wallet balance increases.
3. Counter cash decreases by same amount.

### Cash Out workflow

1. Wallet balance decreases.
2. No counter cash increase happens automatically unless the action is a refresh sale correction or profit transfer.

### Profit In workflow

1. Wallet profit is recorded.
2. Profit can be kept in wallet or moved to counter cash.

### Wallet Refresh workflow

This is for reconciling real wallet balance with system balance.

If actual balance is lower than system:

1. Difference is treated as sold wallet amount.
2. Wallet gets a `cash_out`.
3. Counter cash increases by sold amount.
4. Wallet profit for that sold amount is also added to counter cash.

If actual balance is higher than system:

1. Difference is treated as wallet increase.
2. Wallet gets a `cash_in`.

## 14. Wallet Profit Tracking

### What it does

Tracks wallet commission/profit separately from wallet cash.

### How it works

Wallet profit is recorded in `service_transactions` using `profit_in`.

If destination is:

- `wallet`
  - profit remains in wallet profit balance
- `counter`
  - wallet profit is also added to counter cash

This allows separate tracking of:

- wallet cash
- wallet profit
- wallet profit already moved to counter

## 15. Easyload Management

### Supported networks

- Zong
- Jazz/Warid
- Ufone
- Telenor

### Main actions

- purchase in
- out
- refresh actual Easyload balances
- inspect history

### How it works

Easyload activity also uses `service_transactions`.

Important Easyload entry types:

- `purchase_in`
- `out`
- `adjust_in`
- `adjust_out`

### Purchase In workflow

1. Counter cash is reduced by purchase amount.
2. Easyload balance increases.
3. Expected profit is auto-calculated by network commission rate.

### Out workflow

1. Easyload balance decreases.

### Easyload Refresh workflow

If actual balance is lower than system:

1. Difference is treated as sold amount.
2. Easyload gets an `out` entry.
3. Counter cash increases by sold amount.

If actual balance is higher than system:

1. Difference is recorded as neutral adjustment.
2. Exact system balance is matched.
3. Extra commission is not added again.

## 16. Package Profit

### What it does

Tracks package-related profit entries directly in system cash.

### Main actions

- package profit in
- package profit out

### How it works

Package profit is stored as marked `system_cash_entries`.

This means:

- `profit in` increases counter cash
- `profit out` decreases counter cash

### Important note

Package profit currently does not have a true network field in the data model.

So the system supports:

- package profit totals
- package profit entry history

but not true network-wise package profit accounting yet.

## 17. Sales Reports

### What it does

Provides date-based sales reporting.

### Main actions

- open reports page
- choose date range
- inspect sales and returns
- open detail report for a single day

### What it shows

- total sales
- total returns
- sale count
- return count
- sold items
- returned items

## 18. Cash History

### What it does

Combines cash movement from different sources into history views.

### Sources included

- counter cash
- wallet
- Easyload
- wallet profit to counter
- package profit

### How it works

The app normalizes entries from different sources into common display rows.

This allows:

- daily cash summaries
- detail view for a selected day
- before/after balance effects
- source filtering

## 19. Profit History

### What it does

Shows daily profit collected from different profit sources.

### Profit sources

- stock sales profit
- wallet profit
- Easyload profit
- package profit

### How it works

The app builds a day-wise grouped history.

Each day may include:

- sale profit
- wallet profit
- Easyload profit
- package profit

Detail page shows per-entry breakdown.

## 20. Daily Report

### What it does

Shows today’s most important business totals in one section.

### What it shows

- daily total stock sale
- stock profit in PKR
- stock profit percentage
- wallet profit
  - Easypaisa
  - JazzCash
- Easyload profit
  - network wise
  - total
- package profit
  - recorded entries
  - total

### How it works

It calculates today’s data from:

- today’s sales
- today’s wallet profit entries
- today’s Easyload profit entries
- today’s package profit entries

## 21. Settings

### What it does

Stores shop-level configuration.

### Main settings

- expense percentage
- hide sale prices while selling

### How it works

Settings are stored in `shop_settings`.

These settings influence:

- expense-mode sale pricing
- sale UI display behavior

## 22. Drawer Navigation

### What it does

Provides manager-side app navigation.

### Current sections

- Overview
- Product Management
- Stock History
- Daily Report
- Sales Report
- Customer Ledger
- Cash History
- Profit History
- Settings

## 23. Quick Action Buttons

### What it does

Lets manager perform common actions quickly from floating action buttons.

### Actions available

- sell
- cash in
- out
- wallet profit
- package profit
- counter cash
- refresh wallet
- refresh Easyload

### Why it matters

It reduces clicks for daily operational finance tasks.

## 24. Internal Data Areas

The app mainly works with these storage areas:

- `users`
- `shops`
- `shop_managers`
- `brands`
- `categories`
- `products`
- `stock_batches`
- `customers`
- `sales`
- `sale_items`
- `shop_settings`
- `service_transactions`
- `system_cash_entries`

## 25. Current Business Logic Strengths

The system currently supports:

- linked stock and sales
- linked sales and returns
- linked digital balances and counter cash
- wallet reconciliation
- Easyload reconciliation
- package profit entries
- day-wise profit and cash reporting

## 26. Current Known Model Limitation

The most important current limitation is:

- package profit is not yet stored with a structured network/channel field

So if true package network-wise reporting is required later, the data model should be extended.

## Summary

EzzyStore currently works as a combined:

- inventory system
- shop sales system
- return management system
- customer ledger
- wallet cash manager
- Easyload manager
- profit tracker
- counter cashbook
- daily report and history system

Its core design links operational shop actions directly with accounting effects, so stock movement, digital balances, counter cash, and profit all stay connected inside one workflow.
