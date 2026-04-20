"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          EXPO LEAD FOLLOW-UP AUTOMATION — by Pragya Arya                   ║
║          Built for DJK India | Marketing Executive Application             ║
║                                                                              ║
║  What this does:                                                             ║
║  Takes a CSV of EXPO leads (from badge scanner / manual capture)            ║
║  and generates personalised follow-up email sequences for every lead —      ║
║  segmented by product interest, scored by engagement level,                 ║
║  and ready to load into any email tool (Mailchimp, HubSpot, Stripo).       ║
║                                                                              ║
║  HOW TO USE:                                                                 ║
║  1. Export your EXPO leads as a CSV (see SAMPLE_LEADS below for columns)    ║
║  2. Run: python expo_lead_automation.py                                      ║
║  3. Find outputs in /output/ folder:                                         ║
║     - email_sequences.json  → all personalised emails                       ║
║     - followup_calendar.csv → prioritised 14-day follow-up schedule         ║
║     - summary_report.txt    → stats + top priority leads                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import csv
import json
import os
from datetime import datetime, timedelta

# ── OUTPUT FOLDER ─────────────────────────────────────────────────────────────
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

EXPO_NAME    = "ENGIMACH 2026"
EXPO_DATE    = datetime(2026, 12, 5)   # adjust to actual EXPO date
COMPANY_NAME = "DJK India"
SENDER_NAME  = "Pragya Arya"
SENDER_EMAIL = "marketing@djkindia.co.in"

# ── SAMPLE LEADS DATA ─────────────────────────────────────────────────────────
# Replace with your actual CSV export. Column headers MUST match these exactly.
# engagement: "high" = stopped, long conversation, asked for quote
#             "medium" = had a brief exchange, took brochure
#             "low" = badge scan only, no conversation

SAMPLE_LEADS = [
    {
        "id": "L001",
        "name": "Rajesh Kumar",
        "title": "Head of Production",
        "company": "Sun Pharma Ltd",
        "email": "rajesh.kumar@sunpharma.com",
        "phone": "+91-98100-00001",
        "city": "Ahmedabad",
        "product_interest": "Injection Molding Machines",
        "engagement": "high",
        "notes": "Expanding line 3, evaluating 2 machines for Q3 2026. Wants technical spec sheet."
    },
    {
        "id": "L002",
        "name": "Priya Mehta",
        "title": "VP Procurement",
        "company": "Dixon Technologies",
        "email": "priya.mehta@dixon.in",
        "phone": "+91-98100-00002",
        "city": "Noida",
        "product_interest": "SMT / PCB Inspection Machines",
        "engagement": "high",
        "notes": "Comparing 3 vendors. Needs ROI calculation and lead time. Follow up within 48 hrs."
    },
    {
        "id": "L003",
        "name": "Arvind Shenoy",
        "title": "Plant Manager",
        "company": "Tata AutoComp",
        "email": "arvind.shenoy@tataautocomp.com",
        "phone": "+91-98100-00003",
        "city": "Pune",
        "product_interest": "Die Casting Equipment",
        "engagement": "medium",
        "notes": "Interested in die casting automation. Currently using older models."
    },
    {
        "id": "L004",
        "name": "Sunita Rao",
        "title": "Facilities Director",
        "company": "Apollo Hospitals",
        "email": "sunita.rao@apollohospitals.com",
        "phone": "+91-98100-00004",
        "city": "Chennai",
        "product_interest": "Medical Device Manufacturing Equipment",
        "engagement": "medium",
        "notes": "Exploring options for sterile packaging line. No immediate timeline."
    },
    {
        "id": "L005",
        "name": "Deepak Joshi",
        "title": "Engineering Manager",
        "company": "Bosch India",
        "email": "deepak.joshi@bosch.com",
        "phone": "+91-98100-00005",
        "city": "Bangalore",
        "product_interest": "Industrial Chillers",
        "engagement": "low",
        "notes": "Badge scan only. Picked up brochure."
    },
    {
        "id": "L006",
        "name": "Anita Verma",
        "title": "CEO",
        "company": "Plasticraft Pvt Ltd",
        "email": "anita@plasticraft.in",
        "phone": "+91-98100-00006",
        "city": "Gurgaon",
        "product_interest": "Injection Molding Machines",
        "engagement": "high",
        "notes": "Startup scaling fast. Wants demo + financing options. Very warm lead."
    },
    {
        "id": "L007",
        "name": "Mohammed Farooq",
        "title": "Purchase Manager",
        "company": "Cipla Ltd",
        "email": "m.farooq@cipla.com",
        "phone": "+91-98100-00007",
        "city": "Mumbai",
        "product_interest": "Medical Device Manufacturing Equipment",
        "engagement": "medium",
        "notes": "Replacing 5-year-old line. Budget approved for Q1 next year."
    },
    {
        "id": "L008",
        "name": "Neel Bhattacharya",
        "title": "Technology Head",
        "company": "Wipro Infrastructure",
        "email": "neel.b@wipro.com",
        "phone": "+91-98100-00008",
        "city": "Hyderabad",
        "product_interest": "SMT / PCB Inspection Machines",
        "engagement": "low",
        "notes": "General interest. Long evaluation cycle."
    }
]

# ── LEAD SCORING ──────────────────────────────────────────────────────────────

ENGAGEMENT_SCORES = {"high": 10, "medium": 5, "low": 1}

TITLE_SCORES = {
    "ceo": 8, "coo": 8, "cfo": 8, "vp": 7, "director": 6,
    "head": 5, "manager": 4, "engineer": 3, "officer": 3
}

def score_lead(lead):
    score = ENGAGEMENT_SCORES.get(lead["engagement"].lower(), 1)
    title_lower = lead["title"].lower()
    for keyword, pts in TITLE_SCORES.items():
        if keyword in title_lower:
            score += pts
            break
    return score

def priority_label(score):
    if score >= 15: return "HOT 🔥"
    if score >= 9:  return "WARM"
    return "NURTURE"

# ── EMAIL TEMPLATES ───────────────────────────────────────────────────────────
# Three tiers: high-engagement (personalised + direct CTA),
#              medium (value + soft CTA), low (awareness + content)

TEMPLATES = {

    "high": {
        "email_1": {
            "day": 1,
            "subject": "Great speaking at {expo} — next step for {company}",
            "body": """Hi {first_name},

It was genuinely great connecting with you at {expo} yesterday.

As you mentioned — {notes_summary} — I wanted to make sure you have exactly what you need to move this forward quickly.

I've attached our full technical specification sheet for {product}. A few things in there I think you'll find directly relevant to your situation at {company}:

  → Cycle times and output capacity (line 3 expansion)
  → Integration specs with existing production setups
  → ROI benchmark data from three similar deployments in India

Our technical team in {city} can walk you through a live demo at your facility — typically takes 90 minutes and we bring all the data specific to your line configuration.

Are you available for a brief call this week to set that up?

Warm regards,
{sender_name}
{company_name}
{sender_email}""",
        },
        "email_2": {
            "day": 4,
            "subject": "ROI data you asked about — {product} for {company}",
            "body": """Hi {first_name},

Following up on the spec sheet I sent — wanted to share something I think is more useful: actual ROI numbers.

We recently helped a company similar to {company} (same sector, comparable scale) reduce their per-unit production cost by 18% within 6 months of deployment. I can share the full case study if helpful.

Also — our team in {city} has availability this Friday for a 30-minute call if you'd like to go through numbers specific to your setup.

Would that work?

{sender_name}
{company_name}""",
        },
        "email_3": {
            "day": 10,
            "subject": "Last note from me — {product} for {company}",
            "body": """Hi {first_name},

I know evaluation decisions at scale take time — no pressure at all.

Just wanted to leave this with you: our team can put together a tailored proposal for {company} in 48 hours if and when you're ready to compare formally. We'd include lead time, warranty, after-sales support in {city}, and financing options if needed.

When the time is right, just reply to this email.

{sender_name}
{company_name}""",
        }
    },

    "medium": {
        "email_1": {
            "day": 2,
            "subject": "From {expo} — resources for {company}",
            "body": """Hi {first_name},

Thank you for visiting the DJK India stall at {expo} — it was great to meet you.

I've attached our brochure for {product}, along with a short case study from a recent deployment in the {sector} sector that might be relevant to what you're looking at.

No action needed right now — just wanted to make sure you had everything in one place.

If any questions come up as you evaluate options, I'm happy to help.

{sender_name}
{company_name}
{sender_email}""",
        },
        "email_2": {
            "day": 7,
            "subject": "One thing worth knowing about {product}",
            "body": """Hi {first_name},

A quick note — since we spoke at {expo}, we've had a few questions from other {sector} companies about after-sales support and maintenance cycles for {product}.

I put together a short FAQ that addresses the most common concerns. Attaching it here in case it's useful for your evaluation.

Happy to connect for 20 minutes if you'd like to go deeper on any of this.

{sender_name}
{company_name}""",
        }
    },

    "low": {
        "email_1": {
            "day": 3,
            "subject": "DJK India — resources from {expo}",
            "body": """Hi {first_name},

Thanks for stopping by our stall at {expo}.

I've attached our product catalogue — {product} is on pages 4–7, along with specs and a summary of recent customer deployments.

If you're ever evaluating options in this space, we'd be happy to put together a detailed proposal for {company}.

Best,
{sender_name}
{company_name}
{sender_email}""",
        }
    }
}

# ── SECTOR LOOKUP ─────────────────────────────────────────────────────────────

PRODUCT_SECTOR_MAP = {
    "Injection Molding Machines": "plastics & manufacturing",
    "SMT / PCB Inspection Machines": "electronics manufacturing",
    "Die Casting Equipment": "automotive & metal casting",
    "Medical Device Manufacturing Equipment": "healthcare & pharma",
    "Industrial Chillers": "industrial cooling & HVAC",
    "Water Treatment Systems": "utilities & process industries",
}

# ── EMAIL GENERATOR ───────────────────────────────────────────────────────────

def notes_summary(notes):
    """Extract a 1-line conversational summary from notes for email personalisation."""
    if not notes or len(notes) < 10:
        return "your interest in our solutions"
    sentences = notes.split(".")
    return sentences[0].strip().lower() if sentences else notes[:60]

def generate_emails(lead, expo_date):
    tier       = lead["engagement"].lower()
    templates  = TEMPLATES.get(tier, TEMPLATES["low"])
    first_name = lead["name"].split()[0]
    sector     = PRODUCT_SECTOR_MAP.get(lead["product_interest"], "industrial manufacturing")

    emails = []
    for key, tmpl in templates.items():
        send_date = expo_date + timedelta(days=tmpl["day"])
        body = tmpl["body"].format(
            first_name     = first_name,
            expo           = EXPO_NAME,
            company        = lead["company"],
            product        = lead["product_interest"],
            city           = lead["city"],
            sector         = sector,
            notes_summary  = notes_summary(lead.get("notes", "")),
            sender_name    = SENDER_NAME,
            sender_email   = SENDER_EMAIL,
            company_name   = COMPANY_NAME,
        )
        subject = tmpl["subject"].format(
            expo    = EXPO_NAME,
            company = lead["company"],
            product = lead["product_interest"],
        )
        emails.append({
            "email_number": key,
            "send_date": send_date.strftime("%Y-%m-%d"),
            "subject": subject,
            "body": body,
        })
    return emails

# ── CALENDAR BUILDER ──────────────────────────────────────────────────────────

def build_calendar(all_sequences):
    calendar = []
    for seq in all_sequences:
        lead = seq["lead"]
        for email in seq["emails"]:
            calendar.append({
                "send_date"       : email["send_date"],
                "priority"        : seq["priority"],
                "score"           : seq["score"],
                "lead_name"       : lead["name"],
                "lead_company"    : lead["company"],
                "lead_title"      : lead["title"],
                "lead_email"      : lead["email"],
                "product_interest": lead["product_interest"],
                "engagement"      : lead["engagement"],
                "email_number"    : email["email_number"],
                "subject"         : email["subject"],
            })
    calendar.sort(key=lambda x: (x["send_date"], -x["score"]))
    return calendar

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"  EXPO LEAD FOLLOW-UP AUTOMATION")
    print(f"  EXPO: {EXPO_NAME} | Date: {EXPO_DATE.strftime('%d %b %Y')}")
    print(f"  Processing {len(SAMPLE_LEADS)} leads...")
    print(f"{'='*60}\n")

    all_sequences = []

    for lead in SAMPLE_LEADS:
        score    = score_lead(lead)
        priority = priority_label(score)
        emails   = generate_emails(lead, EXPO_DATE)

        all_sequences.append({
            "lead"    : lead,
            "score"   : score,
            "priority": priority,
            "emails"  : emails,
        })

        print(f"  ✓  {lead['name']:<20} {lead['company']:<30} [{priority}]  Score: {score}")

    # Sort by score descending
    all_sequences.sort(key=lambda x: -x["score"])

    # ── SAVE EMAIL SEQUENCES ──
    output_path = os.path.join(OUTPUT_DIR, "email_sequences.json")
    with open(output_path, "w") as f:
        json.dump(all_sequences, f, indent=2)
    print(f"\n  ✅  Email sequences saved → {output_path}")

    # ── SAVE CALENDAR CSV ──
    calendar     = build_calendar(all_sequences)
    cal_path     = os.path.join(OUTPUT_DIR, "followup_calendar.csv")
    cal_fields   = ["send_date","priority","score","lead_name","lead_company",
                    "lead_title","lead_email","product_interest","engagement",
                    "email_number","subject"]
    with open(cal_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cal_fields)
        writer.writeheader()
        writer.writerows(calendar)
    print(f"  ✅  Follow-up calendar saved  → {cal_path}")

    # ── SAVE SUMMARY REPORT ──
    hot   = [s for s in all_sequences if s["priority"] == "HOT 🔥"]
    warm  = [s for s in all_sequences if s["priority"] == "WARM"]
    nurtr = [s for s in all_sequences if s["priority"] == "NURTURE"]
    total_emails = sum(len(s["emails"]) for s in all_sequences)

    report = f"""
╔══════════════════════════════════════════════════════════╗
║              EXPO LEAD AUTOMATION — SUMMARY             ║
╠══════════════════════════════════════════════════════════╣
  EXPO            : {EXPO_NAME}
  Leads processed : {len(SAMPLE_LEADS)}
  Emails generated: {total_emails}
  Generated on    : {datetime.now().strftime('%d %b %Y %H:%M')}

  PIPELINE BREAKDOWN
  ─────────────────
  🔥 HOT  (score 15+) : {len(hot)} leads — contact within 24 hrs
  🟡 WARM (score 9+)  : {len(warm)} leads — 3-email sequence
  ⚪ NURTURE           : {len(nurtr)} leads — 1-email + catalogue

  TOP PRIORITY LEADS (HOT)
  ──────────────────────────"""

    for s in hot:
        report += f"\n  → {s['lead']['name']:<20} | {s['lead']['company']:<25} | Score: {s['score']}"

    report += f"""

  NEXT ACTIONS
  ─────────────
  1. Import followup_calendar.csv into HubSpot / Mailchimp
  2. Personalise email_1 for HOT leads before sending (add notes)
  3. Set up retargeting ads for HOT leads on LinkedIn
  4. Log all responses back to CRM within 48 hrs of send

╚══════════════════════════════════════════════════════════╝
"""
    report_path = os.path.join(OUTPUT_DIR, "summary_report.txt")
    with open(report_path, "w") as f:
        f.write(report)

    print(report)
    print(f"  ✅  Summary report saved      → {report_path}")
    print(f"\n  Done. All outputs in /{OUTPUT_DIR}/\n")


if __name__ == "__main__":
    main()
