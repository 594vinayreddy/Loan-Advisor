"""
database.py — SQLAlchemy models + seed data for live loan rates.

Schema design:
  - LoanRate: one row per (bank, loan_type, borrower_category) combination
  - Rates are meant to be updated regularly (daily/weekly) via an ETL job
  - The chatbot queries this table for live rate comparisons

To update rates: call seed_rates() with fresh data, or write an ETL job
that fetches from bank APIs / RBI's published EBLR and updates rows.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/loan_rates.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class LoanRate(Base):
    __tablename__ = "loan_rates"

    id                  = Column(Integer, primary_key=True, index=True)
    bank_name           = Column(String(100), nullable=False, index=True)
    loan_type           = Column(String(50),  nullable=False, index=True)   # home | personal | car
    borrower_category   = Column(String(100), nullable=True)                # salaried / self-employed / general
    rate_min_pct        = Column(Float,       nullable=True)                # e.g. 8.75
    rate_max_pct        = Column(Float,       nullable=True)                # e.g. 11.50
    processing_fee      = Column(String(200), nullable=True)                # free-text — varies a lot
    max_tenure_months   = Column(Integer,     nullable=True)
    max_loan_amount     = Column(String(100), nullable=True)                # free-text (crore/lakh vary)
    benchmark           = Column(String(100), nullable=True)                # EBLR / MCLR / Fixed
    special_notes       = Column(Text,        nullable=True)
    last_updated        = Column(DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "bank":             self.bank_name,
            "loan_type":        self.loan_type,
            "category":         self.borrower_category,
            "rate":             f"{self.rate_min_pct}%–{self.rate_max_pct}%" if self.rate_max_pct else f"{self.rate_min_pct}%",
            "processing_fee":   self.processing_fee,
            "max_tenure":       f"{self.max_tenure_months} months" if self.max_tenure_months else "N/A",
            "max_loan":         self.max_loan_amount,
            "benchmark":        self.benchmark,
            "notes":            self.special_notes,
            "last_updated":     self.last_updated.strftime("%d %b %Y") if self.last_updated else "N/A",
        }


def get_db():
    """FastAPI dependency — yields a DB session, closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Seed data  (indicative rates as of June 2026 — update via ETL in production)
# NOTE: These are representative figures. Always verify with the bank before
#       presenting to end users as definitive rates.
# ---------------------------------------------------------------------------

SEED_RATES = [
    # ── HOME LOANS ──────────────────────────────────────────────────────────
    dict(bank_name="HDFC Bank",         loan_type="home",     borrower_category="salaried",
         rate_min_pct=8.75, rate_max_pct=9.65,  processing_fee="Up to 0.5% + GST",
         max_tenure_months=360, max_loan_amount="No upper cap (profile-based)",
         benchmark="EBLR", special_notes="CIBIL 750+ gets best slab; LTV 65–90%"),

    dict(bank_name="ICICI Bank",        loan_type="home",     borrower_category="general",
         rate_min_pct=8.75, rate_max_pct=9.80,  processing_fee="Up to 2% + GST",
         max_tenure_months=360, max_loan_amount="Profile-based",
         benchmark="EBLR", special_notes="NRIs eligible; CIBIL min 700"),

    dict(bank_name="Axis Bank",         loan_type="home",     borrower_category="general",
         rate_min_pct=8.75, rate_max_pct=10.05, processing_fee="Up to 1% + GST, min ₹10,000",
         max_tenure_months=360, max_loan_amount="₹5 crore",
         benchmark="EBLR", special_notes="CIBIL 650 min; 750+ for best rates"),

    dict(bank_name="SBI",               loan_type="home",     borrower_category="general",
         rate_min_pct=8.50, rate_max_pct=9.85,  processing_fee="0.35% + GST, min ₹2k max ₹10k",
         max_tenure_months=360, max_loan_amount="Profile-based",
         benchmark="EBLR (RBI Repo linked)", special_notes="Apply via YONO app; Approval-in-Principle available"),

    dict(bank_name="Bank of Baroda",    loan_type="home",     borrower_category="general",
         rate_min_pct=8.40, rate_max_pct=10.60, processing_fee="0.50% + GST",
         max_tenure_months=360, max_loan_amount="Profile-based",
         benchmark="EBLR", special_notes="HUFs not eligible; NRI/PIO/OCI eligible"),

    dict(bank_name="Canara Bank",       loan_type="home",     borrower_category="general",
         rate_min_pct=8.40, rate_max_pct=11.25, processing_fee="0.50% + GST",
         max_tenure_months=360, max_loan_amount="Profile-based",
         benchmark="EBLR", special_notes="Entry age < 60; must close by 75"),

    dict(bank_name="IDFC FIRST Bank",   loan_type="home",     borrower_category="salaried",
         rate_min_pct=8.85, rate_max_pct=12.00, processing_fee="Up to 3% + GST",
         max_tenure_months=360, max_loan_amount="₹10 crore",
         benchmark="EBLR", special_notes="Assessed Income Programme available; CIBIL 750+ preferred"),

    dict(bank_name="Federal Bank",      loan_type="home",     borrower_category="general",
         rate_min_pct=8.80, rate_max_pct=10.30, processing_fee="0.50% + GST",
         max_tenure_months=360, max_loan_amount="Profile-based",
         benchmark="RBI Repo Rate linked", special_notes="NRI min income ₹50k/month"),

    dict(bank_name="IndusInd Bank",     loan_type="home",     borrower_category="general",
         rate_min_pct=8.75, rate_max_pct=10.75, processing_fee="Up to 1% + GST",
         max_tenure_months=360, max_loan_amount="Profile-based",
         benchmark="EBLR", special_notes="CIBIL 750+ preferred; LTV up to 90%"),

    dict(bank_name="Kotak Mahindra Bank", loan_type="home",   borrower_category="general",
         rate_min_pct=8.75, rate_max_pct=9.60,  processing_fee="Up to 0.5% + GST",
         max_tenure_months=360, max_loan_amount="Profile-based",
         benchmark="EBLR", special_notes="Home Loan eligibility details pending official research"),

    # ── PERSONAL LOANS ──────────────────────────────────────────────────────
    dict(bank_name="HDFC Bank",         loan_type="personal", borrower_category="salaried",
         rate_min_pct=10.50, rate_max_pct=21.00, processing_fee="Up to 2.5% + GST",
         max_tenure_months=60,  max_loan_amount="₹40 lakh",
         benchmark="Fixed", special_notes="EMI ₹2,162/lakh; min income ₹25k/month"),

    dict(bank_name="ICICI Bank",        loan_type="personal", borrower_category="general",
         rate_min_pct=10.50, rate_max_pct=19.00, processing_fee="Up to 2.50% + GST",
         max_tenure_months=60,  max_loan_amount="Profile-based",
         benchmark="Fixed", special_notes="100% digital; CIBIL 700+; pre-approved via iMobile"),

    dict(bank_name="Axis Bank",         loan_type="personal", borrower_category="salaried",
         rate_min_pct=11.25, rate_max_pct=22.00, processing_fee="Up to 2% + GST",
         max_tenure_months=60,  max_loan_amount="Profile-based",
         benchmark="Fixed", special_notes="CIBIL 720+; existing customers min income ₹15k"),

    dict(bank_name="SBI",               loan_type="personal", borrower_category="salaried",
         rate_min_pct=11.15, rate_max_pct=14.30, processing_fee="1% + GST",
         max_tenure_months=60,  max_loan_amount="Profile-based",
         benchmark="Fixed", special_notes="Xpress Credit: salary a/c with SBI required; CIBIL 750+"),

    dict(bank_name="Kotak Mahindra Bank", loan_type="personal", borrower_category="salaried",
         rate_min_pct=10.99, rate_max_pct=24.00, processing_fee="Up to 3% + GST",
         max_tenure_months=72,  max_loan_amount="₹40 lakh",
         benchmark="Fixed", special_notes="Salaried only; CIBIL 685+; grad degree required"),

    dict(bank_name="IndusInd Bank",     loan_type="personal", borrower_category="general",
         rate_min_pct=10.49, rate_max_pct=31.56, processing_fee="Up to 3.5% + GST",
         max_tenure_months=60,  max_loan_amount="₹5 lakh (digital route)",
         benchmark="Fixed", special_notes="100% digital up to ₹5L; only PAN+Aadhaar needed"),

    dict(bank_name="Bank of Baroda",    loan_type="personal", borrower_category="general",
         rate_min_pct=11.05, rate_max_pct=18.75, processing_fee="1–2% + GST, min ₹1k max ₹10k",
         max_tenure_months=60,  max_loan_amount="Profile-based",
         benchmark="Fixed", special_notes="CIBIL 701+; govt employees with BoB a/c: zero fee"),

    dict(bank_name="AU Small Finance Bank", loan_type="personal", borrower_category="general",
         rate_min_pct=14.00, rate_max_pct=26.00, processing_fee="Up to 3% + GST",
         max_tenure_months=60,  max_loan_amount="Profile-based",
         benchmark="Fixed", special_notes="Aadhaar-linked mobile for quick disbursal; income floor not disclosed"),

    dict(bank_name="IDFC FIRST Bank",   loan_type="personal", borrower_category="general",
         rate_min_pct=9.99,  rate_max_pct=28.00, processing_fee="Up to 2% + GST",
         max_tenure_months=60,  max_loan_amount="₹10 lakh (FIRSTmoney)",
         benchmark="Fixed", special_notes="No foreclosure charges; CIBIL 710+; min income ₹10k"),

    dict(bank_name="Punjab National Bank", loan_type="personal", borrower_category="salaried",
         rate_min_pct=11.50, rate_max_pct=16.00, processing_fee="1% + GST",
         max_tenure_months=60,  max_loan_amount="₹10 lakh (general); ₹15 lakh (doctors)",
         benchmark="Fixed", special_notes="Guarantee required (no collateral); PNB salary a/c preferred"),

    # ── CAR LOANS ────────────────────────────────────────────────────────────
    dict(bank_name="HDFC Bank",         loan_type="car",      borrower_category="general",
         rate_min_pct=8.90,  rate_max_pct=10.50, processing_fee="Up to 0.4% + GST",
         max_tenure_months=84,  max_loan_amount="₹25 lakh (new); ₹2.5 crore (pre-owned)",
         benchmark="Fixed", special_notes="Xpress 30-min disbursal; 100% on-road funding on select models; EV up to 96m"),

    dict(bank_name="ICICI Bank",        loan_type="car",      borrower_category="general",
         rate_min_pct=8.90,  rate_max_pct=11.00, processing_fee="Up to 2% + GST",
         max_tenure_months=84,  max_loan_amount="100% on-road price",
         benchmark="Fixed", special_notes="Instant disbursal for pre-approved; CIBIL 700+ recommended"),

    dict(bank_name="Axis Bank",         loan_type="car",      borrower_category="salaried",
         rate_min_pct=9.20,  rate_max_pct=11.50, processing_fee="Up to 1% + GST",
         max_tenure_months=84,  max_loan_amount="Profile-based",
         benchmark="Fixed", special_notes="Existing customer route: AQB ₹1L for 2 qtrs; income ₹4–6L p.a."),

    dict(bank_name="SBI",               loan_type="car",      borrower_category="general",
         rate_min_pct=8.70,  rate_max_pct=10.20, processing_fee="Up to 0.5% + GST",
         max_tenure_months=84,  max_loan_amount="48x net monthly income (salaried)",
         benchmark="EBLR", special_notes="EV up to 96m; Assured Car Loan for FD holders (no income proof)"),

    dict(bank_name="Bank of Baroda",    loan_type="car",      borrower_category="general",
         rate_min_pct=8.80,  rate_max_pct=11.00, processing_fee="0.5% + GST",
         max_tenure_months=84,  max_loan_amount="2x annual income (salaried); 3x (self-employed)",
         benchmark="Fixed", special_notes="No foreclosure charges; CIBIL 701+; 90% of on-road price"),

    dict(bank_name="IndusInd Bank",     loan_type="car",      borrower_category="general",
         rate_min_pct=8.90,  rate_max_pct=12.00, processing_fee="Up to 2% + GST",
         max_tenure_months=84,  max_loan_amount="100% of car value",
         benchmark="Fixed", special_notes="CIBIL 600+; min income ₹3L p.a.; 2yr city residence"),

    dict(bank_name="Canara Bank",       loan_type="car",      borrower_category="general",
         rate_min_pct=8.80,  rate_max_pct=10.80, processing_fee="0.25% + GST",
         max_tenure_months=84,  max_loan_amount="Profile-based",
         benchmark="Fixed", special_notes="Product: Canara Mobile; min income ₹3L p.a.; net take-home 40%+ after EMI"),

    dict(bank_name="AU Small Finance Bank", loan_type="car",  borrower_category="general",
         rate_min_pct=10.00, rate_max_pct=18.00, processing_fee="Up to 2% + GST",
         max_tenure_months=60,  max_loan_amount="100% ex-showroom",
         benchmark="Fixed", special_notes="Assessed income accepted; disbursal 48h; foreclosure 5%/<1yr, 3% thereafter"),
]


def seed_rates():
    """Populate the DB with seed rates. Skips rows that already exist."""
    db = SessionLocal()
    try:
        existing = db.query(LoanRate).count()
        if existing == 0:
            for row in SEED_RATES:
                db.add(LoanRate(**row, last_updated=datetime.utcnow()))
            db.commit()
            print(f"✅  Seeded {len(SEED_RATES)} rate rows.")
        else:
            print(f"ℹ️   DB already has {existing} rate rows — skipping seed.")
    finally:
        db.close()