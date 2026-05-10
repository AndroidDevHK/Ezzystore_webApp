# EzzyStore WebApp Functionality Overview

## Purpose

EzzyStore WebApp is a Flask + SQLite shop-management system for a small retail/mobile-service business. It combines:

- shop administration
- manager login and daily operations
- product and stock management
- sales and customer returns
- customer management
- counter cash tracking
- wallet cash tracking for Easypaisa and JazzCash
- Easyload balance tracking for multiple networks
- profit tracking and reporting

## Main Roles

### 1. Admin

Admin is responsible for system-level setup.

Admin features:

- create shops
- create manager accounts
- assign one manager to one shop
- view shop assignment overview

### 2. Manager

Manager is responsible for running one assigned shop.

Manager features:

- manage products, brands, and categories
- add and monitor stock
- record sales
- record customer returns
- manage customers
- track wallet cash, Easyload, counter cash, and profits
- view reports and history pages
- update shop settings

## Authentication And Access

The app has:

- login page
- role-based session handling
- admin-only routes
- manager-only routes

Manager access depends on being assigned to a shop.

## Shop And User Management

The app supports:

- creating shops
- creating manager users
- linking a manager to a shop
- one-manager-per-shop assignment model

This is handled mainly from the admin dashboard.

## Product Management

The app maintains a product catalog per shop.

Product features:

- create product
- edit product
- delete product when safe
- assign brand
- assign category
- set minimum stock / reorder level
- track current quantity

Safety behavior:

- product deletion is blocked when history exists
- deletion is also blocked if stock is still available

## Brand Management

Managers can:

- create brands
- rename brands
- view brand detail pages
- see products belonging to a brand

## Category Management

Managers can:

- create categories
- rename categories
- view category detail pages
- see products belonging to a category

## Stock And Restocking

The stock system tracks both current quantity and restock history.

Stock features:

- add stock to a single product
- add stock to multiple products in one restock run
- store purchase rate
- store sale price
- store batch date
- view restock history by day
- view purchase history by product

Data tracked in stock batches:

- product
- quantity
- purchase rate
- sale price
- restock date
- creation time

## Sales

Managers can record product sales.

Sale flow includes:

- selecting one or multiple products
- entering quantities
- entering sale prices
- optionally linking a customer
- automatically reducing stock
- automatically adding sale amount to counter cash

Sale data includes:

- sale type
- sold items
- quantity
- unit price
- unit cost
- total amount
- customer reference
- created time

## Expense-Based Selling

The app supports a pricing mode based on purchase cost plus configured expense percent.

This allows:

- automatic price calculation from cost
- use of shop settings expense percent

The app now stores unit cost on each sale item so profit reporting remains stable later.

## Customer Returns

The app supports returning items from an existing sale through a dedicated return flow.

Return features:

- open a specific sale
- choose returnable items
- choose return quantity
- restore stock
- create a return record linked to the original sale
- deduct refund amount from counter cash
- track partial and full returns

Return safety behavior:

- refund amount comes from server-side original sale data
- direct return posting through the generic sales endpoint is blocked

## Customer Management

Managers can:

- create customers
- store name and phone
- link customers to sales
- delete customers
- view customer-related activity indirectly through reports and sales pages

The app also calculates customer insights in manager context, such as:

- total purchased items
- sale total
- estimated purchase total
- profit percentage estimate
- last purchase

## Counter Cash Management

The app has a manual counter cash ledger.

Counter cash features:

- cash in
- cash out
- message / reason recording
- balance history
- day-wise cash history

Counter cash is also affected automatically by:

- sales received
- sale returns / refunds
- wallet transfers
- Easyload purchases
- package profit
- wallet refresh sale adjustments
- Easyload refresh sale adjustments

## Wallet Cash Management

The app tracks digital wallet cash for:

- Easypaisa
- JazzCash

Wallet features:

- cash in
- cash out
- profit in
- move wallet profit to counter cash
- wallet balance refresh
- wallet history

Wallet refresh behavior:

- if actual wallet balance is less than system balance, the difference is treated as sold wallet cash
- sold amount is added to counter cash
- wallet profit is also added to counter cash using configured wallet refresh profit logic

## Easyload Management

The app tracks Easyload balance for:

- Zong
- Jazz/Warid
- Ufone
- Telenor

Easyload features:

- purchase in
- out
- expected commission calculation
- balance refresh
- Easyload history

Easyload refresh behavior:

- if actual balance is less than system balance, the difference is treated as sold amount
- sold amount is added to counter cash
- positive reconciliation uses neutral adjustment logic so it matches the real entered balance exactly

## Package Profit Management

The app includes a dedicated package profit feature.

Package profit features:

- profit in
- profit out
- add directly to counter cash
- reverse mistaken entries
- show in profit history

This is stored as marked counter-cash activity so it is visible separately from normal manual cash movements.

## Finance Quick Actions

Manager quick actions include modal-driven finance workflows for:

- cash in
- out
- wallet profit
- package profit
- counter cash
- Easyload
- wallet refresh
- Easyload refresh

These workflows automate linked accounting entries between digital balances and counter cash.

## Profit Tracking

The app builds profit history from multiple sources.

Profit sources:

- product sale profit
- wallet profit
- Easyload profit
- package profit

Profit features:

- total profit summary
- day-wise profit history
- detailed profit history view

## Reports

The app supports date-based reporting.

Report features:

- daily sales report
- date range report
- sales and return totals
- item counts
- transaction counts
- detailed report page for a selected day

## Cash History And Audit Views

The app creates combined history views for:

- wallet cash
- Easyload
- counter cash
- all cash movements
- profit history

These views help managers inspect:

- source of cash movement
- before/after balance effects
- linked sale details
- notes and timing

## Shop Settings

Managers can update settings for their shop.

Settings features:

- expense percent
- hide sale prices option

These settings affect selling behavior and display behavior.

## Data Storage

Main persistent areas include:

- users
- shops
- shop managers
- brands
- categories
- products
- stock batches
- customers
- sales
- sale items
- shop settings
- service transactions
- system cash entries

## Internal Accounting Model

The app works with two main accounting layers:

### 1. Digital balances

Includes:

- wallet cash
- wallet profit
- Easyload balances

### 2. Counter cash

Includes:

- manual additions and expenses
- sale cash received
- return cash restored
- finance movements from wallet and Easyload flows
- package profit

## Safety Improvements Now Present

Current protections include:

- safer admin bootstrap
- no hardcoded default admin password
- server-side return refund calculation
- blocked unsafe product deletion
- stored sale cost for more stable profit calculation
- exact Easyload refresh reconciliation
- regression tests for critical business flows

## Current App Character

In practical terms, this app is a combined:

- inventory manager
- shop POS support tool
- service-wallet tracker
- Easyload tracker
- cashbook / ledger helper
- small-business reporting system

It is designed around one shop manager operating a single shop with both product sales and mobile-service cash operations.
