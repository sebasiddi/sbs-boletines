from django.contrib.auth.forms import PasswordChangeForm

class CambioContrasenaForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = "Contraseña Actual"
        self.fields['new_password1'].label = "Nueva Contraseña"
        self.fields['new_password2'].label = "Confirmar Nueva Contraseña"