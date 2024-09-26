from django.db import models

# Create your models here.
class Empleado(models.Model):
        nombre_empleado = models.CharField(max_length=200)
        apellido_empleado = models.CharField(max_length=100)
        email_empleado = models.EmailField(max_length=50)
        edad_empleado = models.IntegerField()
        genero_empleado = models.CharField(max_length=80, choices=[('H', 'Hombre'), ('M', 'Mujer')])
        salario_empleado = models.DecimalField(
                max_digits=10, decimal_places=2, null=True, blank=True)
 