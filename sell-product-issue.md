# Sell Product "Select products" Issue Review

## Summary
- Fixed markup issues that could prevent the sale picker modal from opening.
- Updated the sale picker layout to a table format (to match restock) as requested.

## Findings
- The stock picker modal had unclosed containers, which could corrupt the DOM tree and block later modals.
- The sale picker relied on the large inline script; if it fails, the open handler never binds.

## Fixes Applied
- Closed the missing `div` for the stock batch selector block so the markup is valid.
- Closed the missing `div` wrapping the stock picker table to prevent malformed modal markup.
- Added a small, isolated modal opener bound to `data-modal-open` so the sale picker opens even if the larger script fails.
- Converted the sale picker content to a table using the same structure/styles as the restock picker.
- Updated the sale picker filtering logic to target table rows.

## Files Updated
- `app/templates/manager.html`

## How to Verify
1. Open the manager Sell Product page.
2. Click "Select products".
3. Confirm the modal appears and shows a table list like the restock dialog.
4. Use the search box to filter; rows should hide/show.

## Notes
If the modal still fails to open, capture the browser console error so I can address any remaining runtime issues.
