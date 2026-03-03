# Bitespeed Backend Task: Identity Reconciliation

This project is a web service designed to link different customer orders (made with different contact information) to the same person. It identifies and tracks customer identities across multiple purchases using email and phone number matching.

## 🚀 Live Demo
**Endpoint URL**: `https://your-render-app-link.onrender.com/identify`

## 🛠️ Tech Stack
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Deployment**: Render

## 📝 Problem Statement
Bitespeed needs a way to consolidate customer data. Contacts are linked if they share a common email or phone number. The oldest contact is treated as "primary," and all subsequent linked contacts are "secondary".

## ⚙️ Features
- **Identity Reconciliation**: Links contacts sharing common details.
- **Primary-Secondary Logic**: Automatically identifies the oldest record as the primary source of truth.
- **Dynamic Merging**: Converts primary contacts into secondary ones if an incoming request links two previously separate chains.

## 🚦 API Reference
### Identify Contact
**Endpoint**: `POST /identify`

**Request Body**:
```json
{
  "email": "mcfly@hillvalley.edu",
  "phoneNumber": "123456"
}
