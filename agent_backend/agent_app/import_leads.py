import pandas as pd
from agent_app.models import Lead
from datetime import datetime
from typing import List, Optional

def safe_float(value):
    """Convert string like '1,200,000' → 1200000.0 safely"""
    try:
        return float(str(value).replace(',', '').strip())
    except:
        return None

def parse_date(value):
    """Handle both 'dd-mm-yyyy' and 'yyyy-mm-dd' + strip spaces"""
    if pd.isna(value) or str(value).strip() == "":
        return None
    val = str(value).strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    # Try pandas timestamp conversion fallback
    try:
        return pd.to_datetime(value).date()
    except Exception:
        print(f"⚠️ Skipped invalid date: {value}")
        return None

def import_leads_from_excel(file_path):
    df = pd.read_excel(file_path)
    imported = 0
    skipped = 0

    for _, row in df.iterrows():
        try:
            lead_id = str(row['Lead ID']).strip()
            if lead_id.lower() in ["lead id", "nan", ""] or Lead.objects.filter(lead_id=lead_id).exists():
                skipped += 1
                continue

            # Parse and clean fields
            lead_name = str(row.get('Lead name', '')).strip()
            email = str(row.get('Email', '')).strip()
            country_code = str(row.get('Country code', '')).strip()
            phone = str(row.get('Phone', '')).strip()
            project_name = str(row.get('Project name', '')).strip()
            unit_type = str(row.get('Unit type', '')).strip()
            min_budget = safe_float(row.get('Min. Budget'))
            max_budget = safe_float(row.get('Max Budget'))
            lead_status = str(row.get('Lead status', '')).strip()
            last_conversation_date = parse_date(row.get('Last conversation date'))
            last_conversation_summary = str(row.get('Last conversation summary', '')).strip()

            # Skip incomplete mandatory fields
            if not lead_name or not project_name:
                skipped += 1
                continue

            Lead.objects.create(
                lead_id=lead_id,
                lead_name=lead_name,
                email=email,
                country_code=country_code,
                phone=phone,
                project_name=project_name,
                unit_type=unit_type,
                min_budget=min_budget,
                max_budget=max_budget,
                lead_status=lead_status,
                last_conversation_date=last_conversation_date,
                last_conversation_summary=last_conversation_summary
            )

            imported += 1

        except Exception as e:
            print(f"⚠️ Skipped row due to error: {e}")
            skipped += 1

    print(f"✅ Import completed! {imported} leads added, {skipped} skipped.")


def filter_leads(
    project_name: Optional[str] = None,
    min_budget: Optional[str] = None,
    max_budget: Optional[str] = None,
    unit_types_selected: Optional[List[str]] = None,
    lead_statuses_selected: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """
    Return a queryset of leads filtered by provided criteria.
    All params are optional; empty values are ignored.
    """
    leads_qs = Lead.objects.all()

    if project_name:
        leads_qs = leads_qs.filter(project_name__icontains=project_name)

    if min_budget:
        try:
            mb = float(str(min_budget).replace(",", "").strip())
            leads_qs = leads_qs.filter(min_budget__gte=mb)
        except ValueError:
            pass

    if max_budget:
        try:
            xb = float(str(max_budget).replace(",", "").strip())
            leads_qs = leads_qs.filter(max_budget__lte=xb)
        except ValueError:
            pass

    if unit_types_selected:
        leads_qs = leads_qs.filter(unit_type__in=unit_types_selected)

    if lead_statuses_selected:
        leads_qs = leads_qs.filter(lead_status__in=lead_statuses_selected)

    if from_date and to_date:
        fd = parse_date(from_date)
        td = parse_date(to_date)
        if fd and td:
            leads_qs = leads_qs.filter(last_conversation_date__range=[fd, td])

    return leads_qs
