# API Endpoints Reference

Base URL: `http://127.0.0.1:8000/api/v1`

---

## Health
- `GET  http://127.0.0.1:8000/api/v1/health`

## Accounts
- `POST   http://127.0.0.1:8000/api/v1/accounts/` — Create account
- `GET    http://127.0.0.1:8000/api/v1/accounts/` — List accounts
- `GET    http://127.0.0.1:8000/api/v1/accounts/{account_id}` — Get account by ID
- `PUT    http://127.0.0.1:8000/api/v1/accounts/{account_id}` — Update account
- `DELETE http://127.0.0.1:8000/api/v1/accounts/{account_id}` — Delete account
- `GET    http://127.0.0.1:8000/api/v1/accounts/{account_id}/balance` — Get account balance

## Users
- `POST   http://127.0.0.1:8000/api/v1/users/` — Create user
- `GET    http://127.0.0.1:8000/api/v1/users/` — List users
- `GET    http://127.0.0.1:8000/api/v1/users/me` — Get current user
- `GET    http://127.0.0.1:8000/api/v1/users/{user_id}` — Get user by ID
- `PUT    http://127.0.0.1:8000/api/v1/users/{user_id}` — Update user
- `DELETE http://127.0.0.1:8000/api/v1/users/{user_id}` — Delete user

## Transactions
- `POST   http://127.0.0.1:8000/api/v1/transactions/` — Create transaction
- `GET    http://127.0.0.1:8000/api/v1/transactions/` — List transactions
- `GET    http://127.0.0.1:8000/api/v1/transactions/{transaction_id}` — Get transaction by ID
- `PUT    http://127.0.0.1:8000/api/v1/transactions/{transaction_id}` — Update transaction
- `DELETE http://127.0.0.1:8000/api/v1/transactions/{transaction_id}` — Delete transaction
- `GET    http://127.0.0.1:8000/api/v1/transactions/summary/categories` — Get category summary

## Cards
- `POST   http://127.0.0.1:8000/api/v1/cards/` — Create card
- `GET    http://127.0.0.1:8000/api/v1/cards/` — List cards
- `GET    http://127.0.0.1:8000/api/v1/cards/{card_id}` — Get card by ID
- `PUT    http://127.0.0.1:8000/api/v1/cards/{card_id}` — Update card
- `DELETE http://127.0.0.1:8000/api/v1/cards/{card_id}` — Delete card
- `POST   http://127.0.0.1:8000/api/v1/cards/{card_id}/block` — Block card
- `POST   http://127.0.0.1:8000/api/v1/cards/{card_id}/unblock` — Unblock card
- `GET    http://127.0.0.1:8000/api/v1/cards/{card_id}/transactions` — Get card transactions

## Merchants
- `POST   http://127.0.0.1:8000/api/v1/merchants/` — Create merchant
- `GET    http://127.0.0.1:8000/api/v1/merchants/` — List merchants
- `GET    http://127.0.0.1:8000/api/v1/merchants/{merchant_id}` — Get merchant by ID
- `PUT    http://127.0.0.1:8000/api/v1/merchants/{merchant_id}` — Update merchant
- `DELETE http://127.0.0.1:8000/api/v1/merchants/{merchant_id}` — Delete merchant
- `GET    http://127.0.0.1:8000/api/v1/merchants/{merchant_id}/transactions` — Get merchant transactions
- `GET    http://127.0.0.1:8000/api/v1/merchants/popular_categories` — Get popular categories

## Recommendations
- `POST   http://127.0.0.1:8000/api/v1/recommendations/analyze_spending` — Analyze user spending
- `POST   http://127.0.0.1:8000/api/v1/recommendations/personalized` — Personalized recommendations
- `GET    http://127.0.0.1:8000/api/v1/recommendations/products` — Get recommended products

## Risk
- `POST   http://127.0.0.1:8000/api/v1/risk/assess` — Assess risk
- `GET    http://127.0.0.1:8000/api/v1/risk/score/{user_id}` — Get risk score

## Behavioral
- `POST   http://127.0.0.1:8000/api/v1/behavioral/analyze` — Analyze behavior
