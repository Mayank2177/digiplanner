# Receipt Vault Analyzer — Backend

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/signup` | No | Create account, returns JWT |
| POST | `/api/v1/auth/login` | No | Returns JWT |
| GET | `/api/v1/auth/me` | Yes | Current user's profile |
| PUT | `/api/v1/auth/budget` | Yes | Update monthly budget |
| GET | `/api/v1/receipts` | Yes | List/search receipts |
| GET | `/api/v1/receipts/{bill_id}` | Yes | Single receipt |
| PATCH | `/api/v1/receipts/{bill_id}` | Yes | Edit a receipt |
| DELETE | `/api/v1/receipts/{bill_id}` | Yes | Delete a receipt |
| POST | `/api/v1/receipts/upload` | Yes | Upload image/PDF → real OCR → saved receipt |
| GET | `/api/v1/budget/summary` | Yes | Spend vs budget this month |
| GET | `/api/v1/analytics/spend-by-category` | Yes | Category breakdown |
| GET | `/api/v1/analytics/subscriptions` | Yes | Detected recurring charges |
| POST | `/api/v1/erp/sync` | Yes | Simulated ERP export payload |

All authenticated endpoints expect: `Authorization: Bearer <token>`

---

## 8. What's still simulated (be aware, not fixed here)

- **ERP sync** (`/api/v1/erp/sync`) formats your receipts into SAP/Oracle/
  ERPNext-shaped JSON but does not actually call any live ERP system. Real
  integration needs each vendor's SDK + OAuth credentials.
- **Google/Microsoft OAuth** — see note above.
