from django.shortcuts import render
import json

# Create your views here.
"""Clientes Views. """

# Django
from django.contrib import messages

from django.contrib.postgres.aggregates import StringAgg
from datetime import datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, F
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView
# Forms
from clientes.forms import CrearClienteForm, EditarClienteForm, NegocioForm, PlantaForm, ContactoPlantaForm
from epps.forms import ConvenioForm


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
# Modelo
from clientes.models import Negocio, Planta, Cliente, ContactoPlanta
from users.models import User
from epps.models import Convenio
from utils.models import Provincia, Ciudad


# Región/Provincia/Ciudad
def load_provincias(request):
    region_id = request.GET.get('region')    
    provincias = Provincia.objects.filter(region_id=region_id).order_by('nombre')
    context = {'provincias': provincias}
    return render(request, 'clientes/provincia.html', context)

def load_ciudades(request):
    provincia_id = request.GET.get('provincia')    
    ciudades = Ciudad.objects.filter(provincia_id=provincia_id).order_by('nombre')
    context = {'ciudades': ciudades}
    return render(request, 'clientes/ciudad.html', context)


class ClientListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Planta
    template_name = "clientes/clientes_list.html"
    paginate_by = 25
    ordering = ['negocio', 'cliente']

    permission_required = 'clientes.view_cliente'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(ClientListView, self).get_context_data(**kwargs)

        if self.request.user.groups.filter(name__in=['Administrador']).exists():
            institutions = Negocio.objects.values(
                    value=F('id'),
                    title=F('nombre')).all().order_by('nombre')
                #cache.set('institutions', institutions)
            institutions = Cliente.objects.values(
                    value=F('id'),
                    title=F('razon_social')).all().order_by('razon_social')

            context['negocios'] = institutions
            context['negocio'] = self.kwargs.get('negocio_id', None)
            # negocios = Negocio.objects.filter(cliente=1)
            clientes = Cliente.objects.all()
            context['clients'] = Cliente.objects.all()
            # context['clients'] = Cliente.objects.filter(
            #     status=True).order_by(
            #         'razon_social').distinct('razon_social')
            # context['business'] = Negocio.objects.filter(
            #     cliente__negocio__in=negocios).order_by('id', 'nombre').distinct('id', 'nombre')

            clientes= Cliente.objects.filter(status=True)
            plantas = Planta.objects.filter(status=True)
            negocios = Negocio.objects.filter(status=True)
            context['clientes'] = clientes
            context['negocios'] = negocios
            context['plantas'] = plantas

            # print(clientes)
            # Cliente.objects.all().order_by('cliente', 'negocio')
            # Planta.objects.filter(cliente__negocio__in=negocios).order_by('id', 'nombre').distinct('id', 'nombre')
            # Cliente.objects.all().select_related('planta').values_list('id', 'planta__negocio')
        else:
            clientes= self.request.user.cliente.all()
            plantas = self.request.user.planta.all()
            negocios = Negocio.objects.filter(status=True)
            context['clientes'] = clientes
            context['negocios'] = negocios
            context['plantas'] = plantas

        return context

    def get_queryset(self):
        search = self.request.GET.get('q')
        planta = self.kwargs.get('planta_id', None)

        if planta == '':
            planta = None

        if search:
            # No es administrador y recibe parametro de busqueda
            if not self.request.user.groups.filter(name__in=['Administrador', ]).exists():
                queryset = Planta.objects.select_related('negocio').filter(
                    Q(cliente__in=self.request.user.cliente.all()),
                    Q(planta__in=self.request.user.planta.all()),
                    Q(nombre__icontains=search) |
                    Q(telefono__icontains=search) |
                    Q(email__icontains=search)).exclude(
                    groups__name__in=['Administrador']).order_by(
                    'nombre', 'telefono').distinct('nombre', 'telefono')
            else:
                # Es administrador y recibe parametro de busqueda
                queryset = super(ClientListView, self).get_queryset().filter(
                                        Q(nombre__icontains=search) |
                                        Q(telefono__icontains=search) |
                                        Q(rut__icontains=search) |
                                        Q(groups__name__icontains=search) |
                                        Q(email__icontains=search)).order_by(
                    'nombre', 'telefono').distinct('nombre', 'telefono')
        else:
            # Perfil no es Administrador
            if not self.request.user.groups.filter(name__in=['Administrador']).exists():
                if planta is None:
                    queryset = User.objects.filter(
                        planta__in=self.request.user.planta.all()).order_by(
                        'first_name', 'last_name').distinct('first_name', 'last_name')
                else:
                    # No es administrador y hay plantas seleccionadas
                    print('queryset2')
                    queryset = Planta.objects.filter(
                        planta__in=planta).exclude(
                        groups__name__in=['Administrador']).order_by(
                        'nombre', 'telefono').distinct('nombre', 'telefono')

            else:
                # Es administrador y no hay planta seleccionada.
                if planta is None:
                    queryset = super(ClientListView, self).get_queryset().order_by(
                        'nombre', 'telefono').distinct('nombre', 'telefono')
                else:
                    # Es administrador y hay plantas seleccionadas.
                    queryset = super(ClientListView, self).get_queryset().filter(
                        planta__in=planta).order_by(
                        'nombre', 'telefono').distinct('nombre', 'telefono')

        return queryset


class clienteView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/clientes_list.html"
    paginate_by = 25
    ordering = ['first_name', 'last_name']

    permission_required = 'clientes.view_cliente'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(clienteView, self).get_context_data(**kwargs)

        if self.request.user.groups.filter(name__in=['Administrador']).exists():
            institutions = Negocio.objects.values(
                    value=F('id'),
                    title=F('nombre')).all().order_by('nombre')
                #cache.set('institutions', institutions)
            institutions = Sexo.objects.values(
                    value=F('id'),
                    title=F('nombre')).all().order_by('nombre')

            context['negocios'] = institutions
            context['negocio'] = self.kwargs.get('negocio_id', None)

        return context

    def get_queryset(self):
        search = self.request.GET.get('q')
        negocio = self.kwargs.get('negocio_id', None)

        if negocio == '':
            negocio = None

        if search:
            # No es administrador y recibe parametro de busqueda
            if not self.request.user.groups.filter(name__in=['Administrador', ]).exists():
                queryset = User.objects.select_related('negocio').filter(
                    Q(cliente__in=self.request.user.cliente.all()),
                    Q(negocio__in=self.request.user.negocio.all()),
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(username__icontains=search)).exclude(
                    groups__name__in=['Administrador']).order_by(
                    'first_name', 'last_name').distinct('first_name', 'last_name')
            else:
                # Es administrador y recibe parametro de busqueda
                queryset = super(clienteView, self).get_queryset().filter(
                                        Q(first_name__icontains=search) |
                                        Q(last_name__icontains=search) |
                                        Q(rut__icontains=search) |
                                        Q(groups__name__icontains=search) |
                                        Q(username__icontains=search)).order_by(
                    'first_name', 'last_name').distinct('first_name', 'last_name')
        else:
            # Perfil no es Administrador
            if not self.request.user.groups.filter(name__in=['Administrador']).exists():
                if negocio is None:
                    queryset = User.objects.filter(
                        negocio__in=self.request.user.negocio.all()).exclude(
                        groups__name__in=['Administrador']).order_by(
                        'first_name', 'last_name').distinct('first_name', 'last_name')
                else:
                    # No es administrador y hay negocios seleccionadas
                    queryset = User.objects.filter(
                        negocio__in=negocio).exclude(
                        groups__name__in=['Administrador']).order_by(
                        'first_name', 'last_name').distinct('first_name', 'last_name')

            else:
                # Es administrador y no hay negocio seleccionada.
                if negocio is None:
                    queryset = super(clienteView, self).get_queryset().order_by(
                        'first_name', 'last_name').distinct('first_name', 'last_name')
                else:
                    # Es administrador y hay negocios seleccionadas.
                    queryset = super(clienteView, self).get_queryset().filter(
                        negocio__in=negocio).order_by(
                        'first_name', 'last_name').distinct('first_name', 'last_name')

        return queryset


@login_required
@permission_required('clientes.add_cliente', raise_exception=True)
def create_cliente(request):
    if request.method == 'POST':

        cliente_form = CrearClienteForm(data=request.POST, user=request.user)
        # print(request.POST)

        if cliente_form.is_valid():
            cliente = cliente_form.save(commit=False)
            cliente.status = True
            cliente.save()
            cliente = cliente_form.save()
            messages.success(request, 'Cliente Creado Exitosamente')
            return redirect('clientes:create_cliente', cliente_id=cliente.id)
        else:
            messages.error(request, 'Por favor revise el formulario e intentelo de nuevo.')
    else:
        cliente_form = CrearClienteForm(user=request.user)
    
    return render(request, 'clientes/cliente_create.html', {
        'form': cliente_form,
    })


@login_required(login_url='users:signin')
@permission_required('clientes.change_cliente', raise_exception=True)
def update_cliente(request, cliente_id):
    """Update a cliente's profile view."""
    # print('aqui update_cliente')

    cliente = get_object_or_404(Cliente, pk=cliente_id)

    # Se valida que solo el administrador  pueda editar el perfil de otro usuario.
    # Se valida que solo los administradores puedan editar el perfil de otro usuario.
    if not request.user.groups.filter(name__in=['Administrador', 'Administrador Contratos', ]).exists():
        if not cliente == request.user:
            raise Http404

    # Se obtiene el perfil y las negocios del usuario.
    try:
        current_group = cliente.groups.get()
        negocios_usuario = Negocio.objects.values_list('id', flat=True).filter(user=cliente_id)
        #negocios_usuario[::1]
    except:
        current_group = ''
        negocios_usuario = ''

    if request.method == 'POST':
        cliente_form = EditarClienteForm(request.POST or None, instance=cliente, user=request.user)
        #profile_form = ProfileForm(request.POST or None, request.FILES, instance=profile)

        if cliente_form.is_valid():
            cliente.is_active = True
            cliente_form.save()
            #profile_form.save()

            # Solo el Administrador puede cambiar el perfil del usuario
            if request.user.groups.filter(name__in=['Administrador', ]).exists():
                print()
                # print('cliente.groups.clear()')
                # user.groups.clear()
                # user.groups.add(cliente_form.cleaned_data['group'])

            messages.success(request, ('Cliente actualizado'))

            if request.user.groups.filter(name__in=['Administrador', 'Administrador Contratos', ]).exists():
                page = request.GET.get('page')
                if page != '':
                    # print('cliente_idcliente_id', cliente_id)
                    response = redirect('clientes:create_cliente', cliente_id)
                    # response['Location'] += '?page=' + page
                    return response
                else:
                    return redirect('clientes:create_cliente', cliente_id)

            # if request.user.groups.filter(name__in=['Administrador', 'Administrador Contratos', ]).exists():
            #     page = request.GET.get('page')
            #     if page != '':
            #         response = redirect('users:create', user_id)
            #         return response
            #     else:
            #         return redirect('users:create', user_id)
            else:
                return redirect('home')

        else:
            messages.error(request, ('Revisa el formulario e intentalo de nuevo.'))
    else:

        cliente_form = EditarClienteForm(
            instance=cliente,
            initial={'group': current_group.pk, 'negocio': list(negocios_usuario), },
            user=request.user
        )
        #profile_form = ProfileForm(instance=profile)

    return render(
        request=request,
        template_name='clientes/create_cliente.html',
        context={
            'cliente': cliente,
            'form1': cliente_form
        }
    )


class ClienteIdView(TemplateView):
    template_name = 'clientes/create_cliente.html'
    cliente_id=Cliente
    
    cliente = get_object_or_404(Cliente, pk=1)
    
    

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, cliente_id, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata':
                # print(cliente_id)
                data = []
                for i in Cliente.objects.filter(id=cliente_id, status=True):
                    data.append(i.toJSON())
            elif action == 'negocio_add':
                negocio = Negocio()
                negocio.nombre = request.POST['nombre'].lower()
                negocio.descripcion = request.POST['descripcion']
                negocio.archivo = request.FILES['archivo']
                negocio.cliente_id = cliente_id
                negocio.save()
            elif action == 'negocio_edit':
                negocio = Negocio.objects.get(pk=request.POST['id'])
                negocio.nombre = request.POST['nombre'].lower()
                negocio.descripcion = request.POST['descripcion']
                negocio.archivo = request.FILES['archivo']
                negocio.cliente_id = cliente_id
                negocio.save()
            elif action == 'negocio_delete':
                negocio = Negocio.objects.get(pk=request.POST['id'])
                negocio.status = False
                negocio.save()
            elif action == 'planta_add':
                if "masso" in request.POST:
                    estadomasso =  True
                else:
                    estadomasso =  False
                if "psicologico" in request.POST:
                    estadopsico = True
                else:
                    estadopsico = False
                if "hal2" in request.POST:
                    estadohal2 = True
                else:
                    estadohal2 = False
                bono = request.POST.getlist('bono')
                planta = Planta()
                planta.masso = estadomasso
                planta.psicologico = estadopsico
                planta.hal2 = estadohal2
                planta.negocio_id = request.POST['negocio']
                planta.rut = request.POST['rut']
                planta.nombre = request.POST['nombre'].lower()
                planta.telefono = request.POST['telefono']
                planta.email = request.POST['email']
                planta.region_id = request.POST['region']
                planta.provincia_id = request.POST['provincia']
                planta.ciudad_id = request.POST['ciudad']
                planta.direccion = request.POST['direccion']
                planta.nombre_gerente = request.POST['nombre_gerente'].lower()
                planta.rut_gerente = request.POST['rut_gerente']
                planta.direccion_gerente = request.POST['direccion_gerente']
                planta.gratificacion_id = request.POST['gratificacion']
                planta.bateria_id = request.POST['bateria']
                planta.cliente_id = cliente_id
                planta.save()
                for i in bono:
                    planta.bono.add(i)
            elif action == 'planta_edit':
                if "masso" in request.POST:
                    estadomasso =  True
                else:
                    estadomasso =  False
                if "psicologico" in request.POST:
                    estadopsico = True
                else:
                    estadopsico = False
                if "hal2" in request.POST:
                    estadohal2 = True
                else:
                    estadohal2 = False
                bono = request.POST.getlist('bono')
                planta = Planta.objects.get(pk=request.POST['id'])
                planta.masso = estadomasso
                planta.psicologico = estadopsico
                planta.hal2 = estadohal2
                planta.negocio_id = request.POST['negocio']
                planta.rut = request.POST['rut']
                planta.nombre = request.POST['nombre'].lower()
                planta.telefono = request.POST['telefono']
                planta.email = request.POST['email']
                planta.region_id = request.POST['region']
                planta.provincia_id = request.POST['provincia']
                planta.ciudad_id = request.POST['ciudad']
                planta.direccion = request.POST['direccion']
                planta.nombre_gerente = request.POST['nombre_gerente'].lower()
                planta.rut_gerente = request.POST['rut_gerente']
                planta.direccion_gerente = request.POST['direccion_gerente']
                planta.gratificacion_id = request.POST['gratificacion']
                planta.bateria_id = request.POST['bateria']
                planta.cliente_id = cliente_id
                planta.save()
                bonos = []
                for d in planta.bono.all():
                    bonos.append(d.id ) 
                for a in bonos:
                    planta.bono.remove(a)
                
                for i in bono:
                    planta.bono.add(i)
                    
            elif action == 'planta_delete':
                archiv = Planta.objects.get(pk=request.POST['id'])
                archiv.status = False
                archiv.save()
            elif action == 'cp_contacto_add':
                user = User()
                user.first_name = request.POST['nombres']
                user.last_name = request.POST['apellidos'] 
                user.rut = request.POST['rut']
                user.fecha_nacimiento = request.POST['fecha_nacimiento'] 
                user.telefono = request.POST['telefono']
                user.email = request.POST['email']
                user.set_password(user.first_name[0:2].lower()+user.last_name[0:2].lower()+user.rut[0:4])
                user.is_superuser = False
                user.is_staff = False
                user.is_active = True
                email = user.email
                now_date = datetime.now()
                user.username = email[:email.find('@')] + now_date.strftime("-%y%m%H%M%S")
                user.save()
                user.groups.add(7)
                user.cliente.add(cliente_id)
                user.planta.add(request.POST['planta_id'])
                cp_contact = ContactoPlanta()
                cp_contact.nombres = request.POST['nombres']
                cp_contact.apellidos = request.POST['apellidos']
                cp_contact.rut = request.POST['rut']
                cp_contact.fecha_nacimiento = request.POST['fecha_nacimiento']
                cp_contact.telefono = request.POST['telefono']
                cp_contact.email = request.POST['email']
                cp_contact.relacion = request.POST['relacion']
                cp_contact.planta_id = request.POST['planta_id']
                cp_contact.user_id = user.id
                cp_contact.cliente_id = cliente_id
                cp_contact.save()
            elif action == 'cp_contacto_edit':
                user = User.objects.get(pk=request.POST['user_id'])
                user.first_name = request.POST['nombres']
                user.last_name = request.POST['apellidos'] 
                user.rut = request.POST['rut']
                user.fecha_nacimiento = request.POST['fecha_nacimiento'] 
                user.telefono = request.POST['telefono']
                user.email = request.POST['email']
                user.save()
                cp_contact = ContactoPlanta.objects.get(pk=request.POST['id'])
                cp_contact.nombres = request.POST['nombres']
                cp_contact.apellidos = request.POST['apellidos']
                cp_contact.rut = request.POST['rut']
                cp_contact.fecha_nacimiento = request.POST['fecha_nacimiento']
                cp_contact.telefono = request.POST['telefono']
                cp_contact.relacion = request.POST['relacion']
                cp_contact.email = request.POST['email']
                cp_contact.save()
            elif action == 'cp_contacto_delete':
                user = User.objects.get(pk=request.POST['user_id'])
                user.is_active = False
                user.save()
                cp_contact = ContactoPlanta.objects.get(pk=request.POST['id'])
                cp_contact.status = False
                cp_contact.save()
            elif action == 'convenio_add':
                insumo = request.POST.getlist('insumo')
                convenio = Convenio()
                convenio.nombre = request.POST['nombre'].lower()
                convenio.valor = request.POST['valor']
                convenio.validez = request.POST['validez']
                convenio.planta_id = request.POST['planta_id']
                convenio.cliente_id = cliente_id
                convenio.save()
                for i in insumo:
                    convenio.insumo.add(i)
                # convenio.save()
            elif action == 'convenio_edit':
                insumo = request.POST.getlist('insumo')
                convenio = Convenio.objects.get(pk=request.POST['id'])
                convenio.nombre = request.POST['nombre'].lower()
                convenio.valor = request.POST['valor']
                convenio.validez = request.POST['validez']
                convenio.save()
                conve = []
                for d in convenio.insumo.all():
                    conve.append(d.id ) 
                for i in conve:
                    convenio.insumo.remove(i)
                for i in insumo:
                    convenio.insumo.add(i)
                    
            elif action == 'convenio_delete':
                convenio = Convenio.objects.get(pk=request.POST['id'])
                convenio.status = False
                convenio.save()
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)


    def get_context_data(request, cliente_id, **kwargs):

        cliente = get_object_or_404(Cliente, pk=cliente_id)

        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Contactos'
        context['list_url'] = reverse_lazy('users:<int:user_cliente>/create_cliente')
        context['update_url'] = reverse_lazy('clientes:update_cliente')
        context['cliente'] = cliente
        context['entity'] = 'Contactos'
        context['cliente_id'] = cliente_id
        context['form1'] = CrearClienteForm(instance=cliente)
        context['form2'] = NegocioForm()
        context['form3'] = PlantaForm(instance=cliente, cliente_id=cliente_id)
        context['form4'] = ContactoPlantaForm()
        context['form5'] = ConvenioForm()
        # context['convenio_insumos'] = Convenio.objects.values(
        #     'insumo__codigo_externo', 'insumo__nombre', 'insumo__costo').filter(id=14, status=True)
        # context['form3'] = PlantaForm(instance=cliente, cliente=request.cliente)
        return context


class NegocioView(TemplateView):
    """Negocio List
    Vista para listar todos los negocios según el usuario y sus las negocios
    relacionadas.
    """
    template_name = 'clientes/create_cliente.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, cliente_id, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata2':
                data = []
                for i in Negocio.objects.filter(cliente=cliente_id, status=True):
                    data.append(i.toJSON())
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)


class PlantaView(TemplateView):
    """Planta List
    Vista para listar todos las plantas según el usuario y sus las negocios
    relacionadas.
    """
    template_name = 'clientes/create_cliente.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, cliente_id, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata3':
                data = []
                if self.request.user.groups.filter(name__in=['Administrador']).exists():
                    for i in Planta.objects.filter(cliente=cliente_id, status=True):
                        data.append(i.toJSON())
                else:
                    plantas = self.request.user.planta.all()
                    for i in plantas.filter(cliente=cliente_id, status=True):
                        data.append(i.toJSON())
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)


class PlantaContactoView(TemplateView):
    """PlantaContacto List
    Vista para listar todos los contactos de la(s) planta(s) y sus las negocios
    relacionadas.
    """
    template_name = 'clientes/create_cliente.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, cliente_id, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata4':
                data = []
                for i in ContactoPlanta.objects.filter(cliente=cliente_id, status=True):
                    data.append(i.toJSON())
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)


class PlantaConvenioView(TemplateView):
    """PlantaConvenio List
    Vista para listar todos los convenios de la(s) planta(s) y sus las negocios
    relacionadas.
    """
    template_name = 'clientes/create_cliente.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, cliente_id, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata5':
                data = []
                for i in Convenio.objects.filter(cliente=cliente_id, status=True):
                    data.append(i.toJSON())
                    # print('searchdata5', data)
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)


class ConveniosView(TemplateView):
    """PlantaConvenio List
    Vista para listar todos los convenios de la(s) planta(s) y sus las negocios
    relacionadas.
    """
    template_name = 'clientes/create_cliente.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, convenio_id, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'searchdata6':
                data = []
                for i in Convenio.objects.filter(id=convenio_id, status=True):
                    data.append(i.toJSON())
                    # print('ConveniosView', data)
            else:
                data['error'] = 'Ha ocurrido un error'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)
