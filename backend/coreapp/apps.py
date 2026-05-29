from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate


class CoreappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "coreapp"

    def ready(self) -> None:
        def _ensure_admin(**kwargs):
            User = get_user_model()
            username = getattr(settings, "DEFAULT_ADMIN_USERNAME", "admin")
            password = getattr(settings, "DEFAULT_ADMIN_PASSWORD", "admin123")
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = True
            user.is_superuser = True
            if password:
                user.set_password(password)
            user.save()

        post_migrate.connect(_ensure_admin, sender=self)

