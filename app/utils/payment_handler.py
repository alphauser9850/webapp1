from abc import ABC, abstractmethod
from app.models.payment import Payment
from app import db

class PaymentHandler(ABC):
    @abstractmethod
    def process_payment(self, user, amount, hours):
        pass

class StripeHandler(PaymentHandler):
    def process_payment(self, user, amount, hours):
        # Implement Stripe payment logic
        payment = Payment(
            user_id=user.id,
            amount=amount,
            hours_purchased=hours,
            payment_method='stripe'
        )
        user.remaining_hours += hours
        db.session.add(payment)
        db.session.commit()

class PayPalHandler(PaymentHandler):
    def process_payment(self, user, amount, hours):
        # Implement PayPal payment logic
        pass 