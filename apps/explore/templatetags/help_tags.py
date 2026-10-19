from django import template
from django.apps import apps

register = template.Library()

SKIP = {'hello', 'hi', 'hey', 'bye', 'thanks', 'thank you', 'ok', 'okay'}


@register.inclusion_tag('core/partials/help_center.html', takes_context=True)
def help_center(context):
    """Help & Contact panel. Answers come from FAQEntry (duplicates merged),
    the email link from SocialLink, messages saved to ContactMessage."""
    FAQEntry = apps.get_model('explore', 'FAQEntry')
    SocialLink = apps.get_model('explore', 'SocialLink')
    ContactMessage = apps.get_model('explore', 'ContactMessage')

    # Two keywords with the same answer (kids / children) become one card,
    # but both words still find it in the search.
    merged = {}
    for f in FAQEntry.objects.all():
        word = (f.keyword or '').strip().lower()
        answer = (f.answer or '').strip()
        if not word or not answer or word in SKIP:
            continue
        key = answer.lower()
        if key in merged:
            merged[key]['terms'] += ' ' + word
        else:
            merged[key] = {'title': word.capitalize(), 'answer': answer,
                           'terms': word + ' ' + key}

    try:
        from apps.explore.forms import ContactMessageForm
        topics = list(ContactMessageForm.base_fields['topic'].choices)
    except Exception:
        topics = list(ContactMessage._meta.get_field('topic').choices or [])

    socials = {s.platform: s.url for s in SocialLink.objects.all()}
    return {
        'faqs': list(merged.values()),
        'topics': topics,
        'email_url': socials.get('gmail') or 'https://mail.google.com/',
        'csrf_token': context.get('csrf_token', ''),
    }
