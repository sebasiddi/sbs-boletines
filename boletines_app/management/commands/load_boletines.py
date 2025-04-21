import json
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from boletines_app.models import Estudiante
import json

class Command(BaseCommand):
   help = 'Carga los datos iniciales del JSON a la base de datos'

   def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('¡Comando detectado correctamente!'))
        with open('boletines.json', encoding='utf-8') as f:
            data = json.load(f)
        
        for curso, trimestres in data.items():
            for trimestre, estudiantes in trimestres.items():
                for estudiante_data in estudiantes:
                    dni = estudiante_data['DNI']
                    if dni:
                        estudiante, creado = Estudiante.objects.get_or_create(dni=dni)
                        estudiante.username = str(dni)
                        estudiante.first_name = estudiante_data['STUDENT']
                        if creado:
                            estudiante.password = make_password(str(dni))  # solo al crear
                            estudiante.boletin_data = {trimestre: estudiante_data}
                        else:
                            boletin = estudiante.boletin_data or {}
                            boletin[trimestre] = estudiante_data
                            estudiante.boletin_data = boletin
                        estudiante.save()

        self.stdout.write(self.style.SUCCESS('Todos los trimestres fueron cargados correctamente.'))