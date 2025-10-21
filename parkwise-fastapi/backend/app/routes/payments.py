from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from .. import models
from ..schemas import PaymentCreate, PaymentResponse
from ..security import get_current_user
from ..db import get_session
import uuid

router = APIRouter(prefix="/payments")

@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a payment for a booking
    In a real implementation, this would integrate with a payment processor like Stripe
    """
    # Verify that the booking belongs to the user
    result = await session.execute(
        select(models.bookings).where(
            models.bookings.c.id == payment_data.booking_id,
            models.bookings.c.user_id == current_user.id
        )
    )
    booking = result.fetchone()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to user"
        )
    
    # Create payment record
    payment_id = str(uuid.uuid4())
    
    await session.execute(
        insert(models.payments).values(
            id=payment_id,
            user_id=current_user.id,
            booking_id=payment_data.booking_id,
            amount=payment_data.amount,
            status='pending'  # Would be updated after actual payment processing
        )
    )
    await session.commit()
    
    # In a real implementation, you would integrate with a payment processor here
    # and update the payment status based on the result
    
    return PaymentResponse(
        id=payment_id,
        booking_id=payment_data.booking_id,
        amount=payment_data.amount,
        status='pending',
        transaction_id=None
    )

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get payment details"""
    result = await session.execute(
        select(models.payments).where(
            models.payments.c.id == payment_id,
            models.payments.c.user_id == current_user.id
        )
    )
    payment = result.fetchone()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return PaymentResponse(
        id=payment.id,
        booking_id=payment.booking_id,
        amount=payment.amount,
        status=payment.status,
        transaction_id=payment.transaction_id
    )

@router.get("/")
async def get_user_payments(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get all payments for the current user"""
    result = await session.execute(
        select(models.payments).where(
            models.payments.c.user_id == current_user.id
        ).order_by(models.payments.c.created_at.desc())
    )
    payments = result.fetchall()
    
    return payments