""" from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CambioContrasenaForm

def login_view(request):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        user = authenticate(request, dni=dni, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('perfil')
        else:
            messages.error(request, 'DNI o contraseña incorrectos')
    return render(request, 'login.html')

@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = CambioContrasenaForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña actualizada exitosamente')
            return redirect('perfil')
    else:
        form = CambioContrasenaForm(request.user)
    
    return render(request, 'perfil.html', {'form': form})

@login_required
def boletin_view(request, trimestre='1T'):
    boletin = request.user.boletin_data.get(trimestre, {})
    return render(request, 'boletin.html', {
        'boletin': boletin,
        'trimestre_actual': trimestre,
        'trimestres': ['1T', '2T', '3T']
    })

def logout_view(request):
    logout(request)
    return redirect('login')



 """



from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def login_view(request):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        user = authenticate(request, dni=dni, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('perfil')
        else:
            messages.error(request, 'DNI o contraseña incorrectos')
    
    return render(request, 'boletines_app/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            messages.success(request, 'Contraseña actualizada correctamente')
            return redirect('perfil')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'boletines_app/perfil.html', {'form': form})

@login_required
def boletin_view(request, trimestre='1T'):
    if not hasattr(request.user, 'boletin_data'):
        messages.warning(request, 'No hay datos de boletines disponibles')
        return redirect('perfil')
    
    boletin = request.user.boletin_data.get(trimestre, {})
    
    return render(request, 'boletines_app/boletin.html', {
        'boletin': boletin,
        'trimestre_actual': trimestre,
        'trimestres': ['1T', '2T', '3T']  # Lista de trimestres disponibles
    })