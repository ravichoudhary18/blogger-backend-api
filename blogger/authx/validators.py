from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomPasswordValidator:
    def __call__(self, password):
        self.validate(password)

    def validate(self, password, user=None):
        help_text = self.get_help_text()
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                _("Password must contain at least one number. ") + help_text,
                code="password_no_number",
            )
        if not any(c.isupper() for c in password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter. ") + help_text,
                code="password_no_upper",
            )
        if not any(c.islower() for c in password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter. ") + help_text,
                code="password_no_lower",
            )
        if not any(c in "!@#$%^&*()_+-=[]{};':\",.<>/?" for c in password):
            raise ValidationError(
                _("Password must contain at least one special character. ") + help_text,
                code="password_no_special",
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one number, one uppercase letter, "
            "one lowercase letter, and one special character."
        )