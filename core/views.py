from django.core.mail import send_mail
from django.shortcuts import reverse
from django.contrib import messages
from django.conf import settings

from django.views import generic
from .forms import ContactForm
from cart.models import Product


class HomeView(generic.ListView):
    template_name = 'index.html'
    queryset = Product.objects.all()[:4]


class ContactView(generic.FormView):
    form_class = ContactForm
    template_name = 'contact.html'

    def get_success_url(self):
        return reverse('contact')

    def form_valid(self, form):
        messages.info(
            self.request, "Thanks to get in touch. We have received your message.")
        name = form.cleaned_data.get("name")
        email = form.cleaned_data.get("email")
        message = form.cleaned_data.get("message")

        full_message = f"""
            Recived message below from {name}, {email}

            {message}
        """

        send_mail(subject="Received contact form mubmission",
                  message=full_message,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[settings.NOTIFY_EMAIL]
                  )
        return super(ContactView, self).form_valid(form)


class AboutView(generic.TemplateView):
    template_name = 'about.html'


# Create your views here.
