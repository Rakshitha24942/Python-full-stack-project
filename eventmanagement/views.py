from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login ,get_backends
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
import stripe
from decimal import Decimal

from .forms import CustomUserCreationForm, EventForm
from .models import Event

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import io

stripe.api_key = settings.STRIPE_SECRET_KEY


def render_to_pdf(html_string):
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html_string.encode('UTF-8')), result)
    if not pdf.err:
        return result.getvalue()
    return None


def home_view(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.phone = form.cleaned_data.get('phone')
            user.profile.organization = form.cleaned_data.get('organization')
            user.profile.save()

            # Set authentication backend explicitly
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)

            messages.success(request, "Registration successful. Welcome!")
            return redirect('event_list')  # or 'profile' if that's your landing page
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})
@login_required
def profile_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    registered_events = Event.objects.filter(registered_users=user)
    return render(request, 'profile.html', {
        'user': user,
        'profile': profile,
        'registered_events': registered_events
    })


@login_required
def event_list_view(request):
    events = Event.objects.filter(date_time__gte=timezone.now()).order_by('date_time')
    event_type = request.GET.get('type')
    date = request.GET.get('date')
    fee_filter = request.GET.get('fee')

    if event_type:
        events = events.filter(type__icontains=event_type)
    if date:
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            events = events.filter(date_time__date=date_obj.date())
        except ValueError:
            pass
    if fee_filter == "free":
        events = events.filter(fee=0)
    elif fee_filter == "paid":
        events = events.filter(fee__gt=0)

    return render(request, 'eventmanagement/event_list.html', {'events': events})


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'eventmanagement/event_detail.html', {'event': event})


@login_required
def event_price_breakdown_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    base_price = event.fee
    discount = Decimal('0')
    price_after_discount = base_price

    if event.early_bird_enabled and event.early_bird_deadline and timezone.now() <= event.early_bird_deadline:
        discount = base_price * Decimal('0.2')
        price_after_discount = base_price - discount
    elif event.dynamic_pricing_enabled:
        count = event.registered_users.count()
        if event.stage1_seats and count < event.stage1_seats:
            price_after_discount = event.stage1_price
        elif event.stage2_seats and count < event.stage2_seats:
            price_after_discount = event.stage2_price
        elif event.stage3_seats:
            price_after_discount = event.stage3_price
        discount = base_price - price_after_discount if base_price > price_after_discount else Decimal('0')

    gst_amount = Decimal('0')
    final_price = price_after_discount
    if event.gst_enabled:
        gst_amount = final_price * Decimal('0.18')
        final_price += gst_amount

    context = {
        'event': event,
        'base_price': base_price,
        'discount': discount,
        'gst_amount': gst_amount,
        'final_price': final_price,
    }
    return render(request, 'eventmanagement/event_price_breakdown.html', context)

@login_required
def register_event_view(request, pk):
    if request.method != "POST":
        # Only allow POST for registration, else redirect to event detail
        return redirect('event_detail', pk=pk)

    event = get_object_or_404(Event, pk=pk)
    user = request.user

    # If already registered, redirect with message
    if event.registered_users.filter(id=user.id).exists():
        messages.info(request, "You are already registered for this event.")
        return redirect('event_list')

    # If event is free, register user and redirect to event list
    if event.fee == 0:
        event.registered_users.add(user)
        messages.success(request, f"Successfully registered for {event.title}!")
        return redirect('event_list')

    # Calculate final price again (apply discounts, GST)
    final_price = event.fee

    if event.early_bird_enabled and event.early_bird_deadline and timezone.now() <= event.early_bird_deadline:
        final_price *= Decimal('0.8')  # 20% discount
    elif event.dynamic_pricing_enabled:
        count = event.registered_users.count()
        if event.stage1_seats and count < event.stage1_seats:
            final_price = event.stage1_price
        elif event.stage2_seats and count < event.stage2_seats:
            final_price = event.stage2_price
        elif event.stage3_seats:
            final_price = event.stage3_price

    if event.gst_enabled:
        final_price *= Decimal('1.18')  # add 18% GST

    stripe_amount = int(final_price * 100)  # amount in cents

    try:
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',  # or your currency
                    'product_data': {
                        'name': f'Event Ticket - {event.title}'
                    },
                    'unit_amount': stripe_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('stripe_success')) + f"?event_id={event.id}",
            cancel_url=request.build_absolute_uri(reverse('stripe_cancel')),
            client_reference_id=str(user.id),
        )
    except Exception as e:
        messages.error(request, f"Error initiating payment: {str(e)}")
        return redirect('event_detail', pk=event.pk)

    # Redirect user to Stripe hosted payment page
    return redirect(session.url)

@staff_member_required
def event_create_view(request):
    if request.method == 'POST':
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = EventForm(user=request.user)
    return render(request, 'eventmanagement/event_form.html', {'form': form})


@staff_member_required
def event_edit_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = EventForm(instance=event, user=request.user)
    return render(request, 'eventmanagement/event_form.html', {'form': form})


@staff_member_required
def event_delete_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        return redirect('event_list')
    return render(request, 'eventmanagement/event_confirm_delete.html', {'event': event})


@login_required
def stripe_checkout_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    base_amount = float(event.fee)
    if event.gst_enabled:
        gst_amount = base_amount * 0.18
        total_amount = base_amount + gst_amount
    else:
        total_amount = base_amount

    stripe_amount = int(total_amount * 100)  # Stripe expects amount in cents

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',  # Change to 'inr' if you prefer INR
                'product_data': {'name': f'Event Ticket - {event.title}'},
                'unit_amount': stripe_amount,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('stripe_success')),
        cancel_url=request.build_absolute_uri(reverse('stripe_cancel')),
        client_reference_id=str(request.user.id),
    )
    return redirect(session.url)



@login_required
def stripe_success_view(request):
    event_id = request.GET.get('event_id')
    if not event_id:
        messages.error(request, "Payment succeeded, but no event was specified.")
        return redirect('profile')

    event = get_object_or_404(Event, pk=event_id)
    user = request.user

    # Add user to event registered users (mark registration done)
    event.registered_users.add(user)

    # Send confirmation email with ticket PDF attachment
    download_url = request.build_absolute_uri(reverse('download_ticket', args=[event.id]))
    subject = f"Registration Confirmed for {event.title}"
    email_context = {
        'user': user,
        'event': event,
        'download_url': download_url,
    }
    message = render_to_string('emails/registration_confirmation.html', email_context)

    email = EmailMessage(subject, message, to=[user.email])
    email.content_subtype = 'html'

    # Generate PDF ticket and attach
    html_string = render_to_string('pdf/ticket.html', {'user': user, 'event': event})
    pdf_file = render_to_pdf(html_string)
    if pdf_file:
        email.attach(f'ticket_{event.id}.pdf', pdf_file, 'application/pdf')

    email.send()

    messages.success(request, f"Payment successful! You are now registered for {event.title}.")
    return render(request, 'stripe_success.html', {'event': event})


@login_required
def stripe_cancel_view(request):
    messages.error(request, "Payment cancelled.")
    return render(request, 'stripe_cancel.html')


@staff_member_required
def dynamic_pricing_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('event_edit', pk=event.pk)
    else:
        form = EventForm(instance=event)
    return render(request, 'eventmanagement/dynamic_pricing_form.html', {'form': form, 'event': event})


@login_required
def download_ticket_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user = request.user

    # Check if user is registered for this event
    if not event.registered_users.filter(id=user.id).exists():
        messages.error(request, "You are not registered for this event.")
        return redirect('profile')

    # Render ticket HTML and generate PDF
    html_string = render_to_string('pdf/ticket.html', {'user': user, 'event': event})
    pdf_file = render_to_pdf(html_string)

    if pdf_file:
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ticket_{event.id}.pdf"'
        return response
    else:
        messages.error(request, "Error generating PDF ticket.")
        return redirect('profile')
