
from django.shortcuts import render, redirect
import os
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal  # Asegúrate de importar Decimal
from django.contrib import messages  # Para usar mensajes flash
from django.core.exceptions import ObjectDoesNotExist

# Para el informe (Reporte) Excel
import pandas as pd

import json

import logging

from django.utils import timezone
from openpyxl import Workbook  # Para generar el informe en excel
from django.http import HttpResponse, JsonResponse

from django.shortcuts import get_object_or_404
from . models import Empleado  # Importando el modelo de Empleado


def inicio(request):
    opciones_edad = [(str(edad), str(edad)) for edad in range(18, 51)]
    data = {
        'opciones_edad': opciones_edad,
    }
    return render(request, 'empleado/form_empleado.html', data)


def listar_empleados(request):
    empleados = Empleado.objects.all()  # Obtiene todos los registros de empleados
    data = {
        'empleados': empleados,
    }
    return render(request, 'empleado/lista_empleados.html', data)


def view_form_carga_masiva(request):
    return render(request, 'empleado/form_carga_masiva.html')


def detalles_empleado(request, id):
    try:
        empleado = Empleado.objects.get(id=id)
        data = {"empleado": empleado}
        return render(request, "empleado/detalles.html", data)
    except Empleado.DoesNotExist:
        error_message = f"no existe ningún registro para la busqueda id: {id}"
        return render(request, "empleado/lista_empleados.html", {"error_message": error_message})


def registrar_empleado(request):
    if request.method == 'POST':
        """ 
        Iterando a través de todos los elementos en el diccionario request.POST, 
        que contiene los datos enviados a través del método POST, e imprime cada par clave-valor en la consola
        for key, value in request.POST.items():
            print(f'{key}: {value}')
        """
        nombre = request.POST.get('nombre_empleado')
        apellido = request.POST.get('apellido_empleado')
        email = request.POST.get('email_empleado')
        edad = request.POST.get('edad_empleado')
        genero = request.POST.get('genero_empleado')
        salario = request.POST.get('salario_empleado')

        # Procesa los datos y guarda en la base de datos
        empleado = Empleado(
            nombre_empleado=nombre,
            apellido_empleado=apellido,
            email_empleado=email,
            edad_empleado=edad,
            genero_empleado=genero,
            salario_empleado=salario,
            
        )
        empleado.save()

        messages.success(
            request, f"El empleado {nombre} fue registrado exitosamente!")
        return redirect('listar_empleados')

    # Si no se ha enviado el formulario, simplemente renderiza la plantilla con el formulario vacío
    return redirect('inicio')


def view_form_update_empleado(request, id):
    try:
        empleado = Empleado.objects.get(id=id)
        opciones_edad = [(int(edad), int(edad)) for edad in range(18, 51)]

        data = {"empleado": empleado,
                'opciones_edad': opciones_edad,
                }
        return render(request, "empleado/form_update_empleado.html", data)
    except ObjectDoesNotExist:
        error_message = f"El Empleado con id: {id} no existe."
        return render(request, "empleado/lista_empleados.html", {"error_message": error_message})


def actualizar_empleado(request, id):
    try:
        if request.method == "POST":
            # Obtén el empleado existente
            empleado = Empleado.objects.get(id=id)

            empleado.nombre_empleado = request.POST.get('nombre_empleado')
            empleado.apellido_empleado = request.POST.get('apellido_empleado')
            empleado.email_empleado = request.POST.get('email_empleado')
            empleado.edad_empleado = int(request.POST.get('edad_empleado'))
            empleado.genero_empleado = request.POST.get('genero_empleado')

            # Convierte el valor a Decimal
            salario_empleado = Decimal(request.POST.get(
                'salario_empleado').replace(',', '.'))
            empleado.salario_empleado = salario_empleado

            empleado.save()
        return redirect('listar_empleados')
    except ObjectDoesNotExist:
        error_message = f"El Empleado con id: {id} no se actualizó."
        return render(request, "empleado/lista_empleados.html", {"error_message": error_message})


def informe_empleado(request):
    try:
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="data_empleados.xlsx"'

        # Consulta la base de datos para obtener los datos que deseas exportar
        datos = Empleado.objects.all()

        # Crea un nuevo libro de Excel y una hoja de trabajo
        workbook = Workbook()
        worksheet = workbook.active

        # Agrega encabezados
        worksheet.append(
            ['Nombre', 'Apellido', 'Edad', 'Sexo', 'Email', 'Salario'])

        # Agrega los datos a la hoja de trabajo
        for dato in datos:
            worksheet.append([dato.nombre_empleado, dato.apellido_empleado, dato.edad_empleado,
                              dato.genero_empleado, dato.email_empleado, dato.salario_empleado])

        # Guarda el libro de Excel en la respuesta HTTP
        workbook.save(response)

        return response
    except ObjectDoesNotExist:
        error_message = "El Empleado con id: {id} no existe..."
        return render(request, "empleado/lista_empleados.html", {"error_message": error_message})


def eliminar_empleado(request):
    if request.method == 'POST':
        id_empleado = json.loads(request.body)['idEmpleado']
        # Busca el empleado por su ID
        empleado = get_object_or_404(Empleado, id=id_empleado)
        # Realiza la eliminación del empleado
        empleado.delete()
        return JsonResponse({'resultado': 1})
    return JsonResponse({'resultado': 1})


# Cargar archivo           
def cargar_archivo(request):
    try:
        if request.method == 'POST':
            archivo_xlsx = request.FILES.get('archivo_xlsx', None)
            if archivo_xlsx and archivo_xlsx.name.endswith('.xlsx'):
                try:
                    df = pd.read_excel(archivo_xlsx, header=0)
                except Exception as e:
                    return JsonResponse({'status_server': 'error', 'message': f'Error al leer el archivo Excel: {str(e)}'})

                # Limpiar las columnas eliminando espacios y unificando mayúsculas/minúsculas
                df.columns = df.columns.str.strip()  # Eliminar espacios en blanco
                df.columns = df.columns.str.lower()  # Convertir a minúsculas

                # Verificar si las columnas requeridas están en el archivo
                columnas_requeridas = ['nombre', 'apellido', 'email', 'edad', 'sexo', 'salario']
                if not all(col in df.columns for col in columnas_requeridas):
                    return JsonResponse({'status_server': 'error', 'message': 'Faltan columnas requeridas en el archivo Excel.'})

                # Iterar sobre las filas y validar los datos
                for _, row in df.iterrows():
                    if pd.isna(row['email']) or pd.isna(row['nombre']) or pd.isna(row['apellido']):
                        return JsonResponse({'status_server': 'error', 'message': 'Faltan datos en una de las filas.'})

                    nombre_empleado = row['nombre']
                    apellido_empleado = row['apellido']
                    email_empleado = row['email']
                    edad_empleado = row['edad']
                    genero_empleado = row['sexo']
                    salario_empleado = row['salario']

                   
                    empleado, creado = Empleado.objects.update_or_create(
                        email_empleado=email_empleado,  # Usar 'email_empleado' como campo de búsqueda
                        defaults={
                            'nombre_empleado': nombre_empleado,  # Asegurarse de usar los campos correctos del modelo
                            'apellido_empleado': apellido_empleado,
                            'edad_empleado': edad_empleado,
                            'genero_empleado': genero_empleado,
                            'salario_empleado': salario_empleado,
                        }
                    )

                return JsonResponse({'status_server': 'success', 'message': 'Los datos se importaron exitosamente.'})
            else:
                return JsonResponse({'status_server': 'error', 'message': 'El archivo debe ser un archivo de Excel válido.'})
        else:
            return JsonResponse({'status_server': 'error', 'message': 'Método HTTP no válido.'})

    except Exception as e:
        logging.error("Error al cargar el archivo: %s", str(e))
        return JsonResponse({'status_server': 'error', 'message': f'Error al cargar el archivo: {str(e)}'})



# Genera un nombre único para el archivo utilizando UUID y conserva la extensión.
def generate_unique_filename(file):
    extension = os.path.splitext(file.name)[1]
    unique_name = f'{uuid.uuid4()}{extension}'
    return SimpleUploadedFile(unique_name, file.read())
