# Selector Policy

## Objective

Keep selectors stable through UI refactors.

## Rules

1. Prefer semantic selectors (role/label).
2. Prefer dedicated test IDs over CSS structure selectors.
3. Avoid nth-child and deeply nested CSS chains.
4. Avoid text selectors for highly dynamic copy.

## Contract with frontend teams

- Add/maintain test IDs for critical flows.
- Treat removed/changed test IDs as test-breaking changes.

## Selector review checklist

- Is selector unique?
- Is selector user-intent aligned?
- Will minor layout changes break it?
