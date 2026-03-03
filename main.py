from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- DATABASE CONFIGURATION ---
DATABASE_URL = "sqlite:///./bitespeed.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Contact(Base):
    __tablename__ = "Contact"
    id = Column(Integer, primary_key=True, index=True)
    phoneNumber = Column(String, nullable=True)
    email = Column(String, nullable=True)
    linkedId = Column(Integer, ForeignKey("Contact.id"), nullable=True) # ID of another Contact link [cite: 24]
    linkPrecedence = Column(String) # "primary" or "secondary" [cite: 24]
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletedAt = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)

# --- APP AND SCHEMAS ---
app = FastAPI()

class IdentifyRequest(BaseModel):
    email: Optional[str] = None
    phoneNumber: Optional[str] = None # Accepts number but logic treats as string for matching [cite: 40]

# --- CORE LOGIC ---
@app.post("/identify")
async def identify(req: IdentifyRequest):
    db = SessionLocal()
    try:
        email = req.email
        phone = str(req.phoneNumber) if req.phoneNumber else None

        if not email and not phone:
            raise HTTPException(status_code=400, detail="Email or Phone Number required")

        # 1. Find all contacts matching the input
        matches = db.query(Contact).filter(
            or_(Contact.email == email, Contact.phoneNumber == phone)
        ).all()

        if not matches:
            # Scenario: Brand New User [cite: 89]
            new_contact = Contact(email=email, phoneNumber=phone, linkPrecedence="primary")
            db.add(new_contact)
            db.commit()
            db.refresh(new_contact)
            return format_response(new_contact, [], db)

        # 2. Identify all Primary IDs involved in this web of contacts [cite: 26, 27]
        all_primary_ids = set()
        for m in matches:
            if m.linkPrecedence == "primary":
                all_primary_ids.add(m.id)
            else:
                all_primary_ids.add(m.linkedId)

        # Fetch all contacts in the entire connected chain
        connected_contacts = db.query(Contact).filter(
            or_(Contact.id.in_(all_primary_ids), Contact.linkedId.in_(all_primary_ids))
        ).order_by(Contact.createdAt).all()

        # The oldest contact becomes the absolute Primary [cite: 26]
        primary_contact = connected_contacts[0]

        # 3. Scenario: Merge two existing Primary contacts [cite: 144, 145]
        if len(all_primary_ids) > 1:
            for c in connected_contacts:
                if c.id != primary_contact.id and c.linkPrecedence == "primary":
                    c.linkPrecedence = "secondary"
                    c.linkedId = primary_contact.id
                    c.updatedAt = datetime.utcnow()
            db.commit()

        # 4. Scenario: Create Secondary if request has new info [cite: 91]
        existing_emails = {c.email for c in connected_contacts if c.email}
        existing_phones = {c.phoneNumber for c in connected_contacts if c.phoneNumber}

        if (email and email not in existing_emails) or (phone and phone not in existing_phones):
            new_secondary = Contact(
                email=email, 
                phoneNumber=phone, 
                linkedId=primary_contact.id, 
                linkPrecedence="secondary"
            )
            db.add(new_secondary)
            db.commit()
            connected_contacts.append(new_secondary)

        return format_response(primary_contact, connected_contacts, db)
    finally:
        db.close()

def format_response(primary, all_contacts, db):
    # Consolidate emails and phoneNumbers (Primary first) [cite: 48, 50, 53]
    emails = [primary.email] if primary.email else []
    phones = [primary.phoneNumber] if primary.phoneNumber else []
    secondary_ids = []

    for c in all_contacts:
        if c.id == primary.id:
            continue
        if c.email and c.email not in emails:
            emails.append(c.email)
        if c.phoneNumber and c.phoneNumber not in phones:
            phones.append(c.phoneNumber)
        secondary_ids.append(c.id)

    return {
        "contact": {
            "primaryContatctId": primary.id,
            "emails": list(dict.fromkeys(emails)), # Ensure uniqueness
            "phoneNumbers": list(dict.fromkeys(phones)),
            "secondaryContactIds": secondary_ids
        }
    }