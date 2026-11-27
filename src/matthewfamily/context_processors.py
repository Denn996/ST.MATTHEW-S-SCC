from django.contrib.auth import get_user_model

User = get_user_model()

def pending_members_count(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = User.objects.filter(is_active=False).count()
        return {'pending_approvals_count': count}
    return {'pending_approvals_count': 0}