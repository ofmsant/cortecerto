from django.shortcuts import render

def inicio(request):
    """Página temporária da Fase 1."""
    return render(request, "agenda/inicio.html")