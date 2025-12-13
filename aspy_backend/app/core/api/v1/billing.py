# app/api/v1/billing.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import io

# Try to import reportlab, handle gracefully if not available
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    # Define dummy classes to prevent NameError
    A4 = SimpleDocTemplate = Table = TableStyle = None
    Paragraph = Spacer = getSampleStyleSheet = ParagraphStyle = None
    inch = colors = None
    REPORTLAB_AVAILABLE = False

from ....db.session import get_db
from ....models.invoice import Invoice as InvoiceModel
from ....models.subscription import Subscription, SubscriptionStatus, Plan
from ....models.user import User
from ....models.code_execution import CodeExecution
from ...security import get_current_user

router = APIRouter()

def generate_invoice_pdf(invoice: InvoiceModel, user: User, plan: Optional[Plan] = None) -> bytes:
    """Generate PDF invoice document"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("PDF generation requires reportlab package. Install with: pip install reportlab")

    buffer = io.BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)

    # Build story (content)
    story = []
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2563eb')
    )

    # Company header
    story.append(Paragraph("DesiCodes", title_style))
    story.append(Paragraph("Multi-Language Code Execution Platform", styles['Normal']))
    story.append(Spacer(1, 20))

    # Invoice header
    invoice_title = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20
    )
    story.append(Paragraph("INVOICE", invoice_title))

    # Invoice details table
    invoice_data = [
        ['Invoice ID:', f"#{invoice.id}"],
        ['Date:', invoice.created_at.strftime("%B %d, %Y") if invoice.created_at else "N/A"],
        ['Status:', invoice.status.upper() if invoice.status else "PENDING"],
        ['Payment Date:', invoice.paid_at.strftime("%B %d, %Y") if invoice.paid_at else "Not Paid"]
    ]

    invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(invoice_table)
    story.append(Spacer(1, 30))

    # Bill to section
    story.append(Paragraph("Bill To:", styles['Heading3']))
    bill_to_data = [
        ['Customer:', user.username],
        ['Email:', user.email],
        ['Customer ID:', f"#{user.id}"]
    ]

    bill_table = Table(bill_to_data, colWidths=[2*inch, 3*inch])
    bill_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(bill_table)
    story.append(Spacer(1, 30))

    # Items table
    story.append(Paragraph("Invoice Items:", styles['Heading3']))

    # Prepare items data
    plan_name = plan.name if plan else "Subscription Plan"
    amount = float(invoice.amount) if invoice.amount else 0.0
    currency = invoice.currency or "INR"

    items_data = [
        ['Description', 'Quantity', 'Unit Price', 'Total'],
        [plan_name, '1', f'{currency} {amount:.2f}', f'{currency} {amount:.2f}']
    ]

    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Description left-aligned
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(items_table)
    story.append(Spacer(1, 20))

    # Total section
    total_data = [
        ['Subtotal:', f'{currency} {amount:.2f}'],
        ['Tax (0%):', f'{currency} 0.00'],
        ['Total Amount:', f'{currency} {amount:.2f}']
    ]

    total_table = Table(total_data, colWidths=[4*inch, 2*inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
    ]))

    story.append(total_table)
    story.append(Spacer(1, 40))

    # Footer
    footer_text = """
    <para align=center>
    <font size=8>
    Thank you for choosing DesiCodes!<br/>
    For support, contact us at support@desicodes.com<br/>
    Visit us at https://desicodes.com
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))

    # Build PDF
    doc.build(story)

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


# Response Models with consistent format
class InvoiceResponse(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    created_at: datetime
    paid_at: datetime = None

    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    ok: bool = True
    data: Dict[str, Any]


@router.get("/billing/invoices", response_model=Dict[str, Any], tags=["Billing"])
def get_invoices(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all invoices for current user"""
    invoices = db.query(InvoiceModel).filter(
        InvoiceModel.user_id == current_user.id
    ).order_by(InvoiceModel.created_at.desc()).all()

    # Format response with consistent structure
    invoice_list = []
    for invoice in invoices:
        invoice_list.append({
            "id": invoice.id,
            "amount": float(invoice.amount) if invoice.amount else 0.0,
            "currency": invoice.currency or "INR",
            "status": invoice.status or "pending",
            "created_at": invoice.created_at,
            "paid_at": invoice.paid_at
        })

    return {
        "ok": True,
        "data": {
            "invoices": invoice_list,
            "total": len(invoice_list)
        }
    }


@router.get("/billing/invoices/{invoice_id}", tags=["Billing"])
def get_invoice(
    invoice_id: int,
    format: str = Query("json", description="Response format: 'json' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get specific invoice by ID - supports JSON response or PDF download"""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.user_id == current_user.id
    ).first()

    if not invoice:
        if format.lower() == "pdf":
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {
            "ok": False,
            "error": {"message": "Invoice not found"}
        }

    # Get plan details for the invoice
    plan = None
    if invoice.plan_id:
        plan = db.query(Plan).filter(Plan.id == invoice.plan_id).first()

    if format.lower() == "pdf":
        # Generate and return PDF
        try:
            pdf_bytes = generate_invoice_pdf(invoice, current_user, plan)

            # Create filename
            filename = f"invoice_{invoice.id}_{current_user.username}.pdf"

            # Return PDF as downloadable file
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/pdf"
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate PDF invoice: {str(e)}"
            )

    # Default JSON response
    return {
        "ok": True,
        "data": {
            "id": invoice.id,
            "amount": float(invoice.amount) if invoice.amount else 0.0,
            "currency": invoice.currency or "INR",
            "status": invoice.status or "pending",
            "created_at": invoice.created_at,
            "paid_at": invoice.paid_at,
            "plan_id": invoice.plan_id,
            "plan_name": plan.name if plan else None,
            "subscription_id": invoice.subscription_id,
            "download_url": f"/api/v1/billing/invoices/{invoice.id}?format=pdf"
        }
    }


@router.get("/billing/usage", response_model=Dict[str, Any], tags=["Billing"])
def get_usage_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get usage statistics for current user including execution stats"""
    # Get active subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if not subscription:
        return {
            "ok": False,
            "error": {"message": "No active subscription found"}
        }

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
    if not plan:
        return {
            "ok": False,
            "error": {"message": "Plan not found"}
        }

    # Get invoices
    invoices = db.query(InvoiceModel).filter(
        InvoiceModel.user_id == current_user.id,
        InvoiceModel.status == 'paid'
    ).all()

    total_spent = sum(float(invoice.amount) for invoice in invoices if invoice.amount)

    # Get current date for calculations
    today = datetime.now(timezone.utc)
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Use CodeExecution model directly
    executions_this_month = db.query(func.count(CodeExecution.id)).filter(
        and_(
            CodeExecution.user_id == current_user.id,
            CodeExecution.created_at >= first_day_of_month
        )
    ).scalar() or 0

    # Get total executions
    total_executions = db.query(func.count(CodeExecution.id)).filter(
        CodeExecution.user_id == current_user.id
    ).scalar() or 0

    # Get successful executions
    successful_executions = db.query(func.count(CodeExecution.id)).filter(
        and_(
            CodeExecution.user_id == current_user.id,
            CodeExecution.success == True
        )
    ).scalar() or 0

    # Calculate quota usage
    monthly_quota = plan.monthly_executions or 10
    quota_used_percentage = round((executions_this_month / monthly_quota * 100) if monthly_quota > 0 else 0, 2)

    # Prepare response data
    usage_metrics = {
        "api_calls": total_executions,
        "executions_this_month": executions_this_month,
        "successful_executions": successful_executions,
        "failed_executions": total_executions - successful_executions,
        "success_rate": round((successful_executions / total_executions * 100) if total_executions > 0 else 0, 2)
    }

    quota_usage = {
        "monthly_quota": monthly_quota,
        "used_this_month": executions_this_month,
        "remaining": max(0, monthly_quota - executions_this_month),
        "usage_percentage": quota_used_percentage,
        "quota_reset_date": (first_day_of_month + timedelta(days=32)).replace(day=1).isoformat()
    }

    return {
        "ok": True,
        "data": {
            "current_plan": plan.name,
            "plan_type": plan.type.value,
            "total_spent": total_spent,
            "next_billing_date": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "usage_metrics": usage_metrics,
            "quota_usage": quota_usage,
            "subscription_status": "active",
            "subscription_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "subscription_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }
    }


@router.get("/billing/plans/usage", response_model=Dict[str, Any], tags=["Billing"])
def get_plan_usage(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get detailed plan usage and quota information"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if not subscription:
        return {
            "ok": False,
            "error": {"message": "No active subscription found"}
        }

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
    if not plan:
        return {
            "ok": False,
            "error": {"message": "Plan not found"}
        }

    # Calculate executions this month
    today = datetime.now(timezone.utc)
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    executions_this_month = db.query(func.count(CodeExecution.id)).filter(
        and_(
            CodeExecution.user_id == current_user.id,
            CodeExecution.created_at >= first_day_of_month
        )
    ).scalar() or 0

    monthly_quota = plan.monthly_executions or 10
    remaining_quota = max(0, monthly_quota - executions_this_month)
    usage_percentage = round((executions_this_month / monthly_quota * 100) if monthly_quota > 0 else 0, 2)

    # Calculate reset date (first day of next month)
    if today.month == 12:
        reset_date = today.replace(year=today.year + 1, month=1, day=1)
    else:
        reset_date = today.replace(month=today.month + 1, day=1)

    return {
        "ok": True,
        "data": {
            "plan_name": plan.name,
            "plan_type": plan.type.value,
            "monthly_quota": monthly_quota,
            "used_this_month": executions_this_month,
            "remaining_quota": remaining_quota,
            "usage_percentage": usage_percentage,
            "reset_date": reset_date.isoformat(),
            "quota_reset_in": (reset_date - today).days,
            "is_near_limit": usage_percentage > 80
        }
    }


@router.get("/billing/invoices/{invoice_id}/download", tags=["Billing"])
def download_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Download invoice as PDF file"""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        InvoiceModel.user_id == current_user.id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get plan details for the invoice
    plan = None
    if invoice.plan_id:
        plan = db.query(Plan).filter(Plan.id == invoice.plan_id).first()

    try:
        pdf_bytes = generate_invoice_pdf(invoice, current_user, plan)

        # Create filename with date
        date_str = invoice.created_at.strftime("%Y%m%d") if invoice.created_at else "unknown"
        filename = f"DesiCodes_Invoice_{invoice.id}_{date_str}.pdf"

        # Return PDF as downloadable file
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF invoice: {str(e)}"
        )
