"""Contratos views."""

from itertools import chain
from asyncio.windows_events import NULL
from cgi import print_form
from multiprocessing import context
from optparse import Values
from queue import Empty
from tkinter import FLAT
from datetime import date, datetime
import datetime
from docx2pdf import convert
# Django
import os
import pythoncom
import win32com.client
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.forms import NullBooleanField
from django.views.generic import TemplateView
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from docxtpl import DocxTemplate
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
)
from django.contrib.auth.tokens import default_token_generator
from mailmerge import MailMerge
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import (
    url_has_allowed_host_and_scheme, urlsafe_base64_decode,
)
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from numpy import empty
# Models
from ficheros.models import Fichero
from contratos.models import TipoContrato, Contrato, DocumentosContrato, ContratosBono, Anexo, Revision, Baja
from requerimientos.models import RequerimientoTrabajador
from contratos.models import Plantilla
from users.models import User
from clientes.models import Planta
# Form
from contratos.forms import TipoContratoForm, ContratoForm, ContratoEditarForm, MotivoBajaForm
from requerimientos.forms import RequeriTrabajadorForm
from requerimientos.numero_letras import numero_a_letras
from requerimientos.fecha_a_palabras import fecha_a_letras



class TipoContratosView(TemplateView):
    template_name = 'contratos/tipo_contratos_list.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                for i in TipoContrato.objects.filter(status=True):
                    data.append(i.toJSON())
            elif action == 'add':
                tipo = TipoContrato()
                tipo.nombre = request.POST['nombre'].lower()
                tipo.status = True
                tipo.save()
            elif action == 'edit':
                tipo = TipoContrato.objects.get(pk=request.POST['id'])
                tipo.nombre = request.POST['nombre'].lower()
                tipo.save()
            elif action == 'delete':
                tipo = TipoContrato.objects.get(pk=request.POST['id'])
                tipo.status = False
                tipo.save()
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Tipo Contratos'
        context['list_url'] = reverse_lazy('contratos:tipo_contrato')
        context['entity'] = 'TipoContrato'
        context['form'] = TipoContratoForm()
        return context


class ContratoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Contrato List
    Vista para listar todos las contratos según el usuario y plantas.
    """
    model = Contrato
    template_name = "contratos/contrato_list.html"
    paginate_by = 25
    #ordering = ['plantas', 'nombre', ]

    permission_required = 'contratos.view_contrato'
    raise_exception = True

    def get_queryset(self):
        search = self.request.GET.get('q')
        planta = self.kwargs.get('planta_id', None)

        if planta == '':
            planta = None

        if search:
            # Si el usuario no administrador se despliegan todos los contratos
            # de las plantas a las que pertenece el usuario, según el critero de busqueda.
            if not self.request.user.groups.filter(name__in=['Administrador', ]).exists():
                queryset = super(ContratoListView, self).get_queryset().filter(
                    Q(usuario__planta__in=self.request.user.planta.all()),
                    Q(usuario__first_name__icontains=search),
                    Q(usuario__last_name__icontains=search)
                ).distinct()
            else:
                # Si el usuario es administrador se despliegan todos las plantillas
                # segun el critero de busqueda.
                queryset = super(ContratoListView, self).get_queryset().filter(
                    Q(usuario__first_name__icontains=search),
                    Q(usuario__last_name__icontains=search),
                    Q(id__icontains=search),
                    Q(estado__icontains=search)
                ).distinct()
        else:
            # Si el usuario no es administrador, se despliegan los contrtatos
            # de las plantas a las que pertenece el usuario.
            if not self.request.user.groups.filter(name__in=['Administrador']).exists():
                queryset = super(ContratoListView, self).get_queryset().filter(
                    Q(user__planta__in=self.request.user.planta.all()),
                ).distinct()
            else:
                # Si el usuario es administrador, se despliegan todos los contratos.
                if planta is None:
                    queryset = super(ContratoListView, self).get_queryset()
                else:
                    # Si recibe la planta, solo muestra las plantillas que pertenecen a esa planta.
                    queryset = super(ContratoListView, self).get_queryset().filter(
                        Q(user__planta__in=self.request.user.planta.all())
                    ).distinct()

        return queryset


@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def create(request):
 
    requrimientotrabajador = request.POST['requerimiento_trabajador_id'] 
    contrato = Contrato()
    contrato.causal_id = request.POST['causal']
    contrato.motivo = request.POST['motivo']
    contrato.fecha_inicio = request.POST['fecha_inicio']
    if request.POST['tipo'] == 'mensual':
        contrato.fecha_termino = request.POST['fecha_termino']
        contrato.fecha_termino_ultimo_anexo = request.POST['fecha_termino']
        contrato.tipo_documento_id = request.POST['tipo_documento']
        contrato.sueldo_base = request.POST['sueldo_base']
    else:
        contrato.fecha_termino = request.POST['fecha_inicio']
        contrato.fecha_termino_ultimo_anexo = request.POST['fecha_inicio']
        contrato.tipo_documento_id = 8
        contrato.valores_diario_id = request.POST['valores_diario']
        test_date = date.fromisoformat(request.POST['fecha_inicio'])
        weekday_idx = 3
        days_delta = weekday_idx - test_date.weekday()
        if days_delta <= 7:
            days_delta += 7
        res = test_date + datetime.timedelta(days_delta)
        contrato.fecha_pago = res
    contrato.horario_id = request.POST['horario']
    contrato.gratificacion_id = request.POST['gratificacion']
    contrato.planta_id = request.POST['planta']
    contrato.trabajador_id = request.POST['trabajador_id']
    contrato.requerimiento_trabajador_id = request.POST['requerimiento_trabajador_id'] 
    contrato.status = True
    contrato.save()
    largobonos = int(request.POST['largobonos']) + 1
    i = []
    for a in range(1,largobonos):
        i = request.POST.getlist(str(a))
        if (i[0] != '0'):
            bonos = ContratosBono()
            bonos.valor = i[0]
            bonos.bono_id = i[1]
            bonos.contrato_id = contrato.id
            bonos.save()
    return redirect('contratos:create_contrato',requrimientotrabajador)


@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def update_contrato(request, contrato_id, template_name='contratos/contrato_update.html'):
            data = dict()
            contrato = get_object_or_404(Contrato, pk=contrato_id)
            revision1 = Revision.objects.filter(contrato_id=contrato_id)
            if(revision1):
                revision = Revision.objects.get(contrato_id=contrato_id)
            else:
                revision = ''
   
            requer_trabajador = get_object_or_404(RequerimientoTrabajador, pk=contrato.requerimiento_trabajador_id)
            if request.method == 'POST':
                contrato.motivo = request.POST['motivo']
                contrato.fecha_inicio = request.POST['fecha_inicio']
                contrato.horario_id = request.POST['horario']
                contrato.status = True
                if request.POST['tipo2'] == 'mensual':
                    contrato.fecha_termino = request.POST['fecha_termino']
                    contrato.fecha_termino_ultimo_anexo = request.POST['fecha_termino']
                    contrato.tipo_documento_id = request.POST['tipo_documento']
                    contrato.sueldo_base = request.POST['sueldo_base']
                else:
                    contrato.sueldo_base = 0
                    contrato.fecha_termino = request.POST['fecha_inicio']
                    contrato.fecha_termino_ultimo_anexo = request.POST['fecha_inicio']
                    contrato.tipo_documento_id = 8
                    contrato.valores_diario_id = request.POST['valores_diario']                    
                    test_date = date.fromisoformat(request.POST['fecha_inicio'])
                    weekday_idx = 3
                    days_delta = weekday_idx - test_date.weekday()
                    if days_delta <= 7:
                        days_delta += 7
                        res = test_date + datetime.timedelta(days_delta)
                        contrato.fecha_pago = res
                contrato.save()
                bonos = []
                bonosguardados = ContratosBono.objects.values_list('id', flat=True).filter(contrato_id=contrato_id) 
                for i in bonosguardados:
                    bonos.append(i) 
                for a in bonos:
                    bonoseliminar = ContratosBono.objects.get(id = a)
                    bonoseliminar.delete()
                largobonos = int(request.POST['largobonos']) + 1
                i = []
                for a in range(1,largobonos):
                    i = request.POST.getlist(str(a))
                    if (i[0] != '0' ):
                        bonos = ContratosBono()
                        bonos.valor = i[0]
                        bonos.bono_id = i[1]
                        bonos.contrato_id = contrato.id
                        bonos.save()
                return redirect('contratos:create_contrato',contrato.requerimiento_trabajador_id)
            else:
                form = ContratoEditarForm(instance=contrato,horario=requer_trabajador.requerimiento.cliente.horario.all())
                req = contrato.requerimiento_trabajador_id 
                bonos = RequerimientoTrabajador.objects.raw("SELECT b.id, b.nombre, cb.valor FROM public.requerimientos_requerimientotrabajador as rt LEFT JOIN public.requerimientos_requerimiento as r on r.id = rt.requerimiento_id LEFT JOIN public.clientes_planta as p on p.id = r.planta_id LEFT JOIN public.clientes_planta_bono as pb on pb.planta_id = p.id LEFT JOIN public.utils_bono as b on b.id = pb.bono_id LEFT JOIN public.contratos_contrato as c on c.requerimiento_trabajador_id = rt.id LEFT JOIN public.contratos_contratosbono as cb on cb.bono_id = pb.bono_id WHERE rt.id = %s ORDER BY cb.valor" , [req])
                largobonos = len(bonos)
                context={
                    'form4': form,
                    'contrato':contrato,
                    'contrato_id': contrato_id,
                    'largobonos' : largobonos,
                    'revision' : revision,
                    'bonos' : bonos
                }
                data['html_form'] = render_to_string(
                    template_name,
                    context,
                    request=request,
                )
                return JsonResponse(data)


@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def solicitudes_pendientes(request, contrato_id, template_name='contratos/contrato_pdf.html'):
    data = dict()
    contrato = get_object_or_404(Contrato, pk=contrato_id)

    context = {'contrato': contrato, }
    data['html_form'] = render_to_string(
        template_name,
        context,
        request=request,
    )
    return JsonResponse(data)


@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def solicitudes_pendientes_baja(request, contrato_id, template_name='contratos/modal_baja.html'):
    data = dict()
    contrato = get_object_or_404(Contrato, pk=contrato_id)
    baja = get_object_or_404(Baja, contrato_id=contrato_id)


    context = {
        'contrato': contrato,
        'baja': baja
         }
    data['html_form'] = render_to_string(
        template_name,
        context,
        request=request,
    )
    return JsonResponse(data)


@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def baja_contrato(request, contrato_id, template_name='contratos/baja_contrato.html'): 
    data = dict()
    contrato = get_object_or_404(Contrato, pk=contrato_id)
    if request.method == 'POST':
        contrato.estado_contrato = 'PB'
        contrato.fecha_solicitud_baja = datetime.datetime.now()
        contrato.save()
        baja = Baja()
        baja.contrato_id = contrato_id
        baja.motivo_id = request.POST['motivo']
        baja.save()
        messages.error(request, 'Contrato en proceso de baja')
        return redirect('contratos:create_contrato',contrato.requerimiento_trabajador_id)

    else:
    
        context = {
            'form10': MotivoBajaForm,
            'contrato': contrato,
            'contrato_id': contrato_id, 
            }
        data['html_form'] = render_to_string(
            template_name,
            context,
            request=request,
        )
        return JsonResponse(data)


@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def enviar_revision_contrato(request, contrato_id):

            contrato = get_object_or_404(Contrato, pk=contrato_id)
            contrato.estado_contrato = 'PV'
            contrato.fecha_solicitud = datetime.datetime.now()
            revision1 = Revision.objects.filter(contrato_id=contrato_id)
            if(revision1):
                revision = Revision.objects.get(contrato_id=contrato_id)
                revision.estado = 'PD'
                revision.save()
            else:
                revision = Revision()
                revision.contrato_id = contrato.id
                revision.save()

            # Trae el id de la planta del Requerimiento
            plant_template = Contrato.objects.values_list('planta', flat=True).get(pk=contrato_id, status=True)
            # Trae la plantilla que tiene la planta
            formato = Plantilla.objects.values_list('archivo', flat=True).get(plantas=plant_template, tipo_id=1)
            now = datetime.datetime.now()
            doc = DocxTemplate(os.path.join(settings.MEDIA_ROOT + '/' + formato))
         
            context = { 'comuna_planta': Contrato.objects.values_list('planta__ciudad__nombre', flat=True).get(pk=contrato_id, status=True),
                        'fecha_ingreso_trabajador_palabras':fecha_a_letras(Contrato.objects.values_list('fecha_inicio', flat=True).get(pk=contrato_id, status=True)),
                        'nombre_trabajador': Contrato.objects.values_list('trabajador__first_name', flat=True).get(pk=contrato_id, status=True),
                        'rut_trabajador': Contrato.objects.values_list('trabajador__rut', flat=True).get(pk=contrato_id, status=True),
                        'nacionalidad': Contrato.objects.values_list('trabajador__nacionalidad__nombre', flat=True).get(pk=contrato_id, status=True),
                        'fecha_nacimiento': fecha_a_letras(Contrato.objects.values_list('trabajador__fecha_nacimiento', flat=True).get(pk=contrato_id, status=True)),
                        'estado_civil': Contrato.objects.values_list('trabajador__estado_civil', flat=True).get(pk=contrato_id, status=True),
                        'domicilio_trabajador': Contrato.objects.values_list('trabajador__domicilio', flat=True).get(pk=contrato_id, status=True),
                        'comuna_trabajador': Contrato.objects.values_list('trabajador__ciudad__nombre', flat=True).get(pk=contrato_id, status=True),
                        'rut_centro_costo': Contrato.objects.values_list('planta__rut', flat=True).get(pk=contrato_id, status=True),
                        'nombre_centro_costo': Contrato.objects.values_list('requerimiento_trabajador__requerimiento__centro_costo', flat=True).get(pk=contrato_id, status=True),
                        'rut_centro_costo': Contrato.objects.values_list('planta__rut', flat=True).get(pk=contrato_id, status=True),
                        'descripcion_causal': Contrato.objects.values_list('causal__nombre', flat=True).get(pk=contrato_id, status=True),
                        'motivo_req': Contrato.objects.values_list('motivo', flat=True).get(pk=contrato_id, status=True),
                        'cargo_postulante': Contrato.objects.values_list('requerimiento_trabajador__area_cargo__cargo__nombre', flat=True).get(pk=contrato_id, status=True),
                        'centro_costo': Contrato.objects.values_list('planta__nombre', flat=True).get(pk=contrato_id, status=True),
                        'nombre_planta': Contrato.objects.values_list('planta__nombre', flat=True).get(pk=contrato_id, status=True),
                        'direccion_planta': Contrato.objects.values_list('planta__direccion', flat=True).get(pk=contrato_id, status=True),    
                        'comuna_planta': Contrato.objects.values_list('planta__ciudad__nombre', flat=True).get(pk=contrato_id, status=True),
                        'region_planta': Contrato.objects.values_list('planta__region__nombre', flat=True).get(pk=contrato_id, status=True),
                        'descripcion_jornada': Contrato.objects.values_list('planta__ciudad__nombre', flat=True).get(pk=contrato_id, status=True),
                        'sueldo_base_numeros': Contrato.objects.values_list('sueldo_base', flat=True).get(pk=contrato_id, status=True),
                        'sueldo_base_palabras': numero_a_letras(Contrato.objects.values_list('sueldo_base', flat=True).get(pk=contrato_id, status=True))+' pesos',
                        'gratificacion': Contrato.objects.values_list('gratificacion__descripcion', flat=True).get(pk=contrato_id, status=True) ,
                        'detalle_bonos': 'okokok',
                        'nombre_banco': Contrato.objects.values_list('trabajador__banco__nombre', flat=True).get(pk=contrato_id, status=True),
                        'cuenta': Contrato.objects.values_list('trabajador__cuenta', flat=True).get(pk=contrato_id, status=True),
                        'correo': Contrato.objects.values_list('trabajador__email', flat=True).get(pk=contrato_id, status=True),
                        'prevision_trabajador': Contrato.objects.values_list('trabajador__afp__nombre', flat=True).get(pk=contrato_id, status=True),
                        'salud_trabajador': Contrato.objects.values_list('trabajador__salud__nombre', flat=True).get(pk=contrato_id, status=True),
                        'adicional_cumplimiento_horario_undecimo': 'okokok',
                        'parrafo_decimo_tercero': 'okokok',
                        'fecha_ingreso_trabajador':fecha_a_letras(Contrato.objects.values_list('fecha_inicio', flat=True).get(pk=contrato_id, status=True)),
                        }

            doc.render(context)
            # exit()
            # Obtengo el usuario
            usuario = get_object_or_404(User, pk=1)
            # Obtengo todas las negocios a las que pertenece el usuario.
            plantas = usuario.planta.all()
            # Obtengo el set de contrato de la primera negocio relacionada.
            plantillas_attr = list()
            plantillas = Plantilla.objects.filter(activo=True, plantas=plantas[0].id)
            # Obtengo los atributos de cada plantilla
            for p in plantillas:
                plantillas_attr.extend(list(p.atributos))

            path = os.path.join(settings.MEDIA_ROOT + '/plantillas/')
            doc.save(path + '/Contrato#' + str(contrato_id) + '.docx')
            win32com.client.Dispatch("Excel.Application",pythoncom.CoInitialize())
            # convert("Contrato#1.docx")
            convert(path + "Contrato#" + str(contrato_id) + ".docx", path + "Contrato#" + str(contrato_id) + ".pdf")
            
            url = path + "Contrato#" + str(contrato_id) + ".pdf"
            contrato.archivo = url
            contrato.save()
            # Elimino el documento word.
            os.remove(path + 'Contrato#' + str(contrato_id) + '.docx')
            messages.success(request, 'Contrato enviado a revisión')
            return redirect('contratos:create_contrato' ,contrato.requerimiento_trabajador_id)


class AnexoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Contrato List
    Vista para listar todos las contratos según el usuario y plantas.
    """
    model = Contrato
    template_name = "contratos/contrato_list.html"
    paginate_by = 25
    #ordering = ['plantas', 'nombre', ]
    permission_required = 'contratos.view_contrato'
    raise_exception = True
    def get_queryset(self):
        search = self.request.GET.get('q')
        planta = self.kwargs.get('planta_id', None)
        if planta == '':
            planta = None
        if search:
            # Si el usuario no administrador se despliegan todos los contratos
            # de las plantas a las que pertenece el usuario, según el critero de busqueda.
            if not self.request.user.groups.filter(name__in=['Administrador', ]).exists():
                queryset = super(ContratoListView, self).get_queryset().filter(
                    Q(usuario__planta__in=self.request.user.planta.all()),
                    Q(usuario__first_name__icontains=search),
                    Q(usuario__last_name__icontains=search)
                ).distinct()
            else:
                # Si el usuario es administrador se despliegan todos las plantillas
                # segun el critero de busqueda.
                queryset = super(ContratoListView, self).get_queryset().filter(
                    Q(usuario__first_name__icontains=search),
                    Q(usuario__last_name__icontains=search),
                    Q(id__icontains=search),
                    Q(estado__icontains=search)
                ).distinct()
        else:
            # Si el usuario no es administrador, se despliegan los contrtatos
            # de las plantas a las que pertenece el usuario.
            if not self.request.user.groups.filter(name__in=['Administrador']).exists():
                queryset = super(ContratoListView, self).get_queryset().filter(
                    Q(user__planta__in=self.request.user.planta.all()),
                ).distinct()
            else:
                # Si el usuario es administrador, se despliegan todos los contratos.
                if planta is None:
                    queryset = super(ContratoListView, self).get_queryset()
                else:
                    # Si recibe la planta, solo muestra las plantillas que pertenecen a esa planta.
                    queryset = super(ContratoListView, self).get_queryset().filter(
                        Q(user__planta__in=self.request.user.planta.all())
                    ).distinct()
        return queryset


@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def create_anexo(request):
            requrimientotrabajador = request.POST['requerimiento_trabajador_id'] 
            anexo = Anexo()
            anexo.trabajador_id = request.POST['trabajador_id']
            anexo.requerimiento_trabajador_id = request.POST['requerimiento_trabajador_id']
            anexo.fecha_inicio = request.POST['UltimoAnexo']
            anexo.fecha_termino = request.POST['fechaTerminoAnexo']
            if "motivo" in request.POST:
                anexo.motivo = request.POST['motivo']
            anexo.fecha_termino_anexo_anterior = request.POST['fechaTerminoAnexo']
            anexo.contrato_id = request.POST['id_contrato']
            if "renta" in request.POST:
                 anexo.nueva_renta = request.POST['NuevaRenta']
            anexo.causal_id = request.POST['id_causalanexo']
            anexo.planta_id = request.POST['planta']
            anexo.save()
            contrato = Contrato.objects.get(pk=request.POST['id_contrato'])
            contrato.fecha_termino_ultimo_anexo = request.POST['fechaTerminoAnexo']
            contrato.save()
            return redirect('contratos:create_contrato',requrimientotrabajador)



@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def update_anexo(request, anexo_id,template_name='contratos/anexo_update.html'):
            data = dict()
            anexo = get_object_or_404(Anexo, pk=anexo_id)
            contrato = get_object_or_404(Contrato, pk=anexo.contrato_id)
            if request.method == 'POST':
                anexo.fecha_termino = request.POST['fechaTerminoAnexo']
                if "NuevoMotivo1" in request.POST:
                    anexo.motivo = request.POST['NuevoMotivo1']
                elif "NuevoMotivo2" in request.POST :
                    anexo.motivo = request.POST['NuevoMotivo2']
                if 'NuevaRenta1' in request.POST and request.POST['NuevaRenta1'] != '' :
                    anexo.nueva_renta = request.POST['NuevaRenta1']
                elif 'NuevaRenta2' in request.POST and request.POST['NuevaRenta2'] != '' :
                    anexo.nueva_renta =  request.POST['NuevaRenta2']
                else:
                    anexo.nueva_renta =  None
                anexo.save()
                contrato.fecha_termino_ultimo_anexo = request.POST['fechaTerminoAnexo']
                contrato.save()
                return redirect('contratos:create_contrato',anexo.requerimiento_trabajador_id)
            else:
                contratos = RequerimientoTrabajador.objects.filter(pk=anexo.requerimiento_trabajador_id).values( 'contrato',
                'contrato__requerimiento_trabajador', 'contrato__estado_contrato','contrato__sueldo_base', 'contrato__tipo_documento__nombre','contrato__causal__nombre' ,'contrato__causal', 'contrato__motivo', 'contrato__fecha_inicio',
                'contrato__fecha_termino', 'contrato__horario__nombre' , 'contrato__fecha_termino_ultimo_anexo', 'trabajador__first_name', 'trabajador__last_name', 'trabajador__domicilio' )
                context={
                    'contratos' : contratos,
                    'anexo_id' : anexo.id,
                    'fecha_termino' : anexo.fecha_termino,
                    'motivo': anexo.motivo,
                    'nuevarenta': anexo.nueva_renta
                }
                data['html_form'] = render_to_string(
                    template_name,
                    context,
                    request=request,
                )
                return JsonResponse(data)

@login_required
@permission_required('contratos.add_contrato', raise_exception=True)
def enviar_revision_anexo(request, anexo_id):
            revision = Revision()
            anexo = get_object_or_404(Anexo, pk=anexo_id)
            anexo.estado_anexo = 'PV'
            anexo.fecha_solicitud = datetime.now()
            anexo.save()
            revision.anexo_id = anexo.id
            revision.save()          
            messages.success(request, 'Contrato enviado a revisión')
            return redirect('contratos:create_contrato' ,anexo.requerimiento_trabajador_id)

class ContratoIdView(TemplateView):
    template_name = 'contratos/create_contrato.html'



    def get_context_data(self, requerimiento_trabajador_id, **kwargs):

        requer_trabajador = get_object_or_404(RequerimientoTrabajador, pk=requerimiento_trabajador_id)
        trabaj = RequerimientoTrabajador.objects.filter(id=requerimiento_trabajador_id).values(
                'trabajador', 'trabajador__first_name', 'trabajador__last_name', 'trabajador__rut','trabajador__estado_civil__nombre', 'trabajador__fecha_nacimiento',
                'trabajador__domicilio', 'trabajador__ciudad', 'trabajador__afp', 'trabajador__salud', 'trabajador__nivel_estudio', 'trabajador__telefono', 'trabajador__nacionalidad',
                'requerimiento__nombre',  'referido','requerimiento__areacargo', 'requerimiento__centro_costo', 'requerimiento__cliente__razon_social', 'requerimiento__cliente__rut',
                 'requerimiento__planta__nombre', 'requerimiento__planta__region', 'requerimiento__planta__ciudad', 'requerimiento__planta__direccion', 'requerimiento__planta__gratificacion',
                 'trabajador__user__planta__nombre').order_by('trabajador__user__planta')
        context = super().get_context_data(**kwargs)
        context['datos'] = RequerimientoTrabajador.objects.filter(pk=requerimiento_trabajador_id).values(
                'trabajador', 'trabajador__first_name', 'trabajador__last_name', 'trabajador__rut','trabajador__estado_civil__nombre',
                'trabajador__fecha_nacimiento', 'trabajador__domicilio', 'trabajador__ciudad__nombre', 'trabajador__afp__nombre', 'trabajador__salud__nombre',
                'trabajador__nivel_estudio__nombre', 'trabajador__telefono', 'trabajador__nacionalidad__nombre', 'requerimiento__nombre',
                'referido', 'area_cargo__area__nombre', 'area_cargo__cargo__nombre', 'requerimiento__centro_costo', 'requerimiento__cliente__razon_social',
                'requerimiento__cliente__rut', 'requerimiento__codigo', 'requerimiento__planta__nombre', 'requerimiento__planta',
                'requerimiento__planta__region__nombre', 'requerimiento__planta__provincia__nombre','requerimiento__fecha_adendum','requerimiento__causal',
                'requerimiento__planta__ciudad__nombre', 'requerimiento__planta__direccion','requerimiento__descripcion','requerimiento__fecha_inicio',
                'requerimiento__planta__gratificacion__nombre','requerimiento__planta__gratificacion').order_by('trabajador__rut')
        context['contratos'] = Contrato.objects.filter(requerimiento_trabajador_id=requerimiento_trabajador_id, status=True ).values( 'id', 'valores_diario__valor_diario',
                'requerimiento_trabajador', 'estado_contrato','sueldo_base', 'tipo_documento__nombre','causal__nombre' ,'causal', 'motivo', 'fecha_inicio',
                 'fecha_termino', 'horario__nombre' , 'fecha_termino_ultimo_anexo', 'trabajador__first_name', 'trabajador__last_name', 'trabajador__domicilio' )
        context['anexos'] = RequerimientoTrabajador.objects.filter(pk=requerimiento_trabajador_id).values( 'anexo', 'anexo__estado_anexo',
                'anexo__requerimiento_trabajador', 'anexo__nueva_renta', 'contrato__tipo_documento__nombre','anexo__causal__nombre' ,'anexo__causal', 'anexo__motivo', 'anexo__fecha_inicio',
                 'anexo__fecha_termino' ).order_by('anexo__fecha_inicio')
        bonos = RequerimientoTrabajador.objects.values_list('requerimiento__planta__bono', flat=True).filter(pk=requerimiento_trabajador_id)
        largobonos = len(bonos) 
        context['largobonos'] = largobonos
        context['requerimiento_trabajador_id'] = requerimiento_trabajador_id
        context['bonos'] = RequerimientoTrabajador.objects.filter(pk=requerimiento_trabajador_id).values('requerimiento__planta__bono','requerimiento__planta__bono__nombre')
        context['form3'] = RequeriTrabajadorForm(instance=requer_trabajador, user=trabaj)
        context['form2'] = ContratoForm(horario=requer_trabajador.requerimiento.cliente.horario.all())
        return context



class ContratosBonoView(TemplateView):
    """ContratosBono List
    Vista para listar todos los negocios según el usuario y sus las negocios
    relacionadas.
    """
    template_name = 'utils/create_cliente.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, cliente_id, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                for i in ContratosBono.objects.filter(cliente=cliente_id, status=True):
                    data.append(i.toJSON())
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)


class ContratoMis(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(ContratoMis, self).get_context_data(**kwargs)
        # Obtengo las plantas del Usuario
        plantas = self.request.user.planta.all()
        # Obtengo los ficheros de las plantas a las que pertenece el usuario
        context['ficheros'] = Fichero.objects.filter(
            plantas__in=plantas, status=True, created_by_id=self.request.user
        ).distinct()
        # Obtengo los contratos del usuario si no es administrador.
        if self.request.user.groups.filter(name__in=['Administrador']).exists():
            context['contratos'] = Contrato.objects.all().order_by('modified')
                # created_by_id=self.request.user).order_by('modified')
        elif self.request.user.groups.filter(name__in=['Administrador Contratos', 'Psicologo']).exists():
            context['contratos'] = Contrato.objects.filter(
                created_by_id=self.request.user, planta__in=plantas, status=True).order_by('modified')
        else:
            # Obtengo todos los contratos por firmar de todas las plantas a las
            # que pertenece el usuario.
            context['contratos'] = Contrato.objects.filter(
                planta__in=plantas, estado_firma=Contrato.POR_FIRMAR, trabajador__user=self.request.user)
            context['result'] = Contrato.objects.values(
                'planta__nombre').order_by('planta')
                # 'planta__nombre').order_by('planta').annotate(count=Count(estado=Contrato.FIRMADO_TRABAJADOR))

        return context


class ContratoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Contrato
    template_name = "contratos/contrato_detail.html"
    context_object_name = "contrato"

    permission_required = 'contratos.view_contrato'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(ContratoDetailView, self).get_context_data(**kwargs)
        # Solo el administrador puede ver el contrato de otro usuario.
        if not self.request.user.groups.filter(name__in=['Administrador', 'Administrador Contratos', 'Fiscalizador Interno', 'Fiscalizador DT', ]).exists():
            if not self.object.usuario == self.request.user:
                raise Http404

        # Obtengo todos los documentos del contrato
        documentos = DocumentosContrato.objects.filter(contrato=self.object.id)
        context['documentos'] = documentos

        return context


class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context


class ContratoFirmarView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    slug_url_kwarg = "id"
    slug_field = "id"
    model = Contrato
    template_name = 'registration/password_reset_done.html'
    title = _('Password reset sent')
    template_name = "contratos/contrato_firm.html"
    context_object_name = "contrato"

    permission_required = 'contratos.view_contrato'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(ContratoFirmarView, self).get_context_data(**kwargs)
        # Solo el administrador puede ver el contrato de otro usuario.
        if not self.request.user.groups.filter(name__in=['Administrador', 'Administrador Contratos', 'Fiscalizador Interno', 'Fiscalizador DT', ]).exists():
            if not self.object.usuario == self.request.user:
                raise Http404

        # Obtengo todos los documentos del contrato
        documentos = DocumentosContrato.objects.filter(contrato=self.object.id)
        context['documentos'] = documentos
        return context


class generar_firma_contrato(PermissionRequiredMixin, PasswordContextMixin):
        email_template_name = 'emails/contrat_firm_token.html'
        extra_email_context = None
        form_class = PasswordResetForm
        from_email = None
        # from_email = mel@yopmail.com
        html_email_template_name = None
        subject_template_name = 'emails/password_reset_subject.txt'
        success_url = reverse_lazy('password_reset_done')
        template_name = 'emails/contrat_firm_token.html'
        title = _('Password reset')
        token_generator = default_token_generator

        @method_decorator(csrf_protect)
        def dispatch(self, *args, **kwargs):
            return super().dispatch(*args, **kwargs)

        def form_valid(self, form):
            opts = {
                'use_https': self.request.is_secure(),
                'token_generator': self.token_generator,
                'from_email': self.from_email,
                'email_template_name': self.email_template_name,
                'subject_template_name': self.subject_template_name,
                'request': self.request,
                'html_email_template_name': self.html_email_template_name,
                'extra_email_context': self.extra_email_context,
            }
            form.save(**opts)
            return super().form_valid(form)


        INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'

        def generar_firma_contrato(request, contrato_id, template_name='contratos/users_firma_contrato.html'):
            data = dict()
            # Obtengo el usuario
            contrato = get_object_or_404(Contrato, pk=contrato_id)
            print (contrato_id)
            uidb64 = "1s72q4rgru5hyt6fyrjhvc8y1a73piq6"
            token = "oN8ZslfdNk6n6sjUKo63roxbVdfeRHGQthkT48CjlTB57IPj2tn1Ga6d7VRMOGlF"

            if request.method == 'POST':
                print (contrato_id)

            else:
                data['form_is_valid'] = False

            context = {'contrato': contrato, }
            data['html_form'] = render_to_string(
                template_name,
                context,
                request=request
            )
            return JsonResponse(data)


class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context


class PasswordResetView(PasswordContextMixin, FormView):
    email_template_name = 'registration/contrat_firm_token.html'
    extra_email_context = None
    form_class = PasswordResetForm
    from_email = None
    html_email_template_name = None
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    template_name = 'registration/password_reset_form.html'
    title = _('Password reset')
    token_generator = default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)
        return super().form_valid(form)


INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


class PasswordResetDoneView(PasswordContextMixin, TemplateView):
    template_name = 'registration/password_reset_done.html'
    title = _('Password reset sent')



class SolicitudContrado(TemplateView):

    template_name = 'contratos/solicitudes_pendientes_contrato.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                for i in Contrato.objects.filter(estado_contrato='PV', status=True):
                    data.append(i.toJSON())
            elif action == 'aprobar':
                revision = Revision.objects.get(contrato_id=request.POST['id'])
                revision.estado = 'AP'
                revision.save()
                contrato = Contrato.objects.get(pk=request.POST['id'])
                contrato.fecha_aprobacion  = datetime.datetime.now()
                contrato.estado_contrato = 'AP'
                contrato.save()
            elif action == 'rechazar':
                revision = Revision.objects.get(contrato_id=request.POST['id'])
                revision.estado = 'RC'
                revision.obs = request.POST['obs']
                revision.save()
                contrato = Contrato.objects.get(pk=request.POST['id'])
                url = contrato.archivo
                os.remove(str(url))
                contrato.archivo = None
                contrato.estado_contrato = 'RC'
                contrato.save()
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)



class BajaContrado(TemplateView):

    template_name = 'contratos/list_contrato_baja.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                data = []
                for i in Contrato.objects.filter(estado_contrato='PB', status=True):
                    data.append(i.toJSON())
            elif action == 'aprobar':
                baja = Baja.objects.get(contrato_id=request.POST['id'])
                baja.estado = 'AP'
                baja.save()
                contrato = Contrato.objects.get(pk=request.POST['id'])
                contrato.fecha_aprobacion_baja  = datetime.datetime.now()
                contrato.estado_contrato = 'BJ'
                contrato.status = False
                contrato.save()
            elif action == 'rechazar':
                revision = Revision.objects.get(contrato_id=request.POST['id'])
                revision.estado = 'RC'
                revision.obs = request.POST['obs']
                revision.save()
                contrato = Contrato.objects.get(pk=request.POST['id'])
                url = contrato.archivo
                os.remove(str(url))
                contrato.archivo = None
                contrato.estado_contrato = 'RC'
                contrato.save()
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)




