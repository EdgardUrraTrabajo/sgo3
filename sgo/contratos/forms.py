"""Contratos Forms."""

# Django
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
# Model
from contratos.models import Plantilla, TipoContrato, Contrato, TipoDocumento, Baja, MotivoBaja
from clientes.models import Cliente, Planta
from requerimientos.models import Causal
from utils.models import Horario
from users.models import ValoresDiario

class TipoContratoForm(forms.ModelForm):
    nombre = forms.CharField(required=True, label="Nombre",
                                 widget=forms.TextInput(attrs={'class': "form-control"}))
  

    def __init__(self, *args, **kwargs):
        super(TipoContratoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = TipoContrato
        fields = ("nombre", )


class MotivoBajaForm(forms.ModelForm):

    motivo = forms.ModelChoiceField(queryset=MotivoBaja.objects.all(), required=False, label="Valores Diario",
                                   widget=forms.Select(attrs={'class': ' show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )

    def __init__(self, *args, **kwargs):
        super(MotivoBajaForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Baja
        fields = ("motivo",)


class CrearContratoForm(forms.ModelForm):
    fecha_pago = forms.CharField(required=True, label="Fecha Pago",
                                 widget=forms.TextInput(attrs={'class': "form-control", 'autocomplete':'off', 'id':"fecha_solicitud", 'readonly' :'true'}))
    fecha_inicio = forms.CharField(required=True, label="Fecha Inicio",
                                 widget=forms.TextInput(attrs={'class': "form-control", 'autocomplete':'off', 'id':"fecha_inicio", 'readonly' :'true'}))
    fecha_termino = forms.CharField(required=True, label="Fecha Término",
                                 widget=forms.TextInput(attrs={'class': "form-control", 'autocomplete':'off', 'id':"fecha_termino",'readonly' :'true' }))
    clientes = forms.ModelMultipleChoiceField(queryset=Cliente.objects.all(), required=True, label="Cliente",
                                   widget=forms.SelectMultiple(attrs={'class': 'selectpicker show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )
    plantas = forms.ModelMultipleChoiceField(queryset=Planta.objects.all(), required=True, label="Planta",
                                            widget=forms.SelectMultiple(
                                                attrs={'class': 'selectpicker show-tick',
                                                       'data-size': '5',
                                                       'data-live-search': 'true',
                                                       'data-live-search-normalize': 'true'
                                                       })
                                            )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CrearContratoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('tipo_documento', css_class='form-group col-md-4 mb-0'),
                Column('sueldo_base', css_class='form-group col-md-4 mb-0'),
                Column('causal', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('fecha_pago', css_class='form-group col-md-4 mb-0'),
                Column('fecha_inicio', css_class='form-group col-md-4 mb-0'),
                Column('fecha_termino', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('gratificacion', css_class='form-group col-md-4 mb-0'),
                Column('horario', css_class='form-group col-md-4 mb-0'),
                Column('planta', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'seguro_vida',
            'motivo',
        )

    class Meta:
        model = Contrato
        fields = ("tipo_documento", "sueldo_base", "fecha_pago", "fecha_inicio",  "fecha_termino", "motivo", "seguro_vida", "gratificacion", "horario", "planta", "causal", )


class CrearPlantillaForm(forms.ModelForm):
    nombre = forms.CharField(required=True, label="Nombre",
                             widget=forms.TextInput(attrs={'class': "form-control"}))
    clientes = forms.ModelMultipleChoiceField(queryset=Cliente.objects.all(), required=True, label="Cliente",
                                   widget=forms.SelectMultiple(attrs={'class': 'selectpicker show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )

    plantas = forms.ModelMultipleChoiceField(queryset=Planta.objects.all(), required=True, label="Planta",
                                            widget=forms.SelectMultiple(
                                                attrs={'class': 'selectpicker show-tick',
                                                       'data-size': '5',
                                                       'data-live-search': 'true',
                                                       'data-live-search-normalize': 'true'
                                                       })
                                            )


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CrearPlantillaForm, self).__init__(*args, **kwargs)
        if not user.groups.filter(name='Administrador').exists():
            self.fields['clientes'].queryset = Cliente.objects.filter(id__in=user.cliente.all())
            self.fields['plantas'].queryset = Planta.objects.filter(id__in=user.planta.all())
        else:
            self.fields['clientes'].queryset = Cliente.objects.all()
            self.fields['plantas'].queryset = Planta.objects.all()


    class Meta:
        model = Plantilla
        fields = ("nombre", "tipo", "archivo",  "clientes", "plantas", )


class ActualizarPlantillaForm(forms.ModelForm):
    nombre = forms.CharField(required=True, label="Nombre",
                             widget=forms.TextInput(attrs={'class': "form-control"}))

    clientes = forms.ModelMultipleChoiceField(queryset=Cliente.objects.none(), required=True, label="Cliente",
                                            widget=forms.SelectMultiple(
                                                attrs={'class': 'selectpicker show-tick',
                                                       'data-size': '5',
                                                       'data-live-search': 'true',
                                                       'data-live-search-normalize': 'true'
                                                       })
                                            )
    plantas = forms.ModelMultipleChoiceField(queryset=Planta.objects.none(), required=True, label="Planta",
                                            widget=forms.SelectMultiple(
                                                attrs={'class': 'selectpicker show-tick',
                                                       'data-size': '5',
                                                       'data-live-search': 'true',
                                                       'data-live-search-normalize': 'true'
                                                       })
                                            )


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ActualizarPlantillaForm, self).__init__(*args, **kwargs)
        if not user.groups.filter(name='Administrador').exists():
            self.fields['clientes'].queryset = Cliente.objects.filter(id__in=user.cliente.all())
            self.fields['plantas'].queryset = Planta.objects.filter(id__in=user.planta.all())
        else:
            self.fields['clientes'].queryset = Cliente.objects.all()
            self.fields['plantas'].queryset = Planta.objects.all()


    class Meta:
        model = Plantilla
        fields = ("nombre", "tipo", "archivo", "clientes", "plantas", 'activo')


class ContratoForm(forms.ModelForm):

    NORMAL = 'NOR'
    REGIMEN_PGP = 'PGP'
    URGENCIA = 'URG'
    CONTINGENCIA = "CON"

    REGIMEN_ESTADO = (
        (NORMAL, 'Normal'),
        (REGIMEN_PGP, 'Régimen PGP'),
        (URGENCIA, 'Urgencia'),
        (CONTINGENCIA, 'Contingencia'),
    )
    causal = forms.ModelChoiceField(queryset=Causal.objects.all(), required=True, label="Causal",
                                   widget=forms.Select(attrs={'class': 'selectpicker show-tick form-control','onchange': 'getval(this);' ,
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )
    motivo = forms.CharField (required=True, label="Observaciones",
                                 widget=forms.TextInput(attrs={'class': "form-control"}))
    fecha_inicio = forms.CharField(required=True, label="Fecha Inicio",
                                 widget=forms.TextInput(attrs={'class': "form-control", 'autocomplete':'off', 'id':"fecha_inicio", 'readonly' :'true'}))
    fecha_termino = forms.CharField(required=True, label="Fecha Término",
                                 widget=forms.TextInput(attrs={'class': "form-control", 'autocomplete':'off', 'id':"fecha_termino",'readonly' :'true' }))
    horario = forms.ModelChoiceField(queryset=Horario.objects.none(), required=True, label="Horario",
                                   widget=forms.Select(attrs={'class': 'selectpicker show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true' 
                                                              })
                                   )
    sueldo_base = forms.CharField(required=False, label="sueldo",
                             widget=forms.TextInput(attrs={'class': "form-control"}))
    tipo_documento = forms.ModelChoiceField(queryset=TipoDocumento.objects.filter(status=True, nombre__startswith='C'), required=True, label="Tipo Contrato",
                                   widget=forms.Select(attrs={'class': 'selectpicker show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )                             
    regimen = forms.ChoiceField(choices = REGIMEN_ESTADO, required=True, label="Regimen",
                                   widget=forms.Select(attrs={'class': 'selectpicker show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )
    valores_diario = forms.ModelChoiceField(queryset=ValoresDiario.objects.all(), required=False, label="Valores Diario",
                                   widget=forms.Select(attrs={'class': 'selectpicker show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )

    def __init__(self, *args, **kwargs):
        horario = kwargs.pop('horario', None)
        super(ContratoForm, self).__init__(*args, **kwargs)
        self.fields['horario'].queryset = horario


    class Meta:
        model = Contrato
        fields = ("causal", "motivo", "fecha_inicio", "fecha_termino", "horario", 'sueldo_base', 'valores_diario', 'tipo_documento', 'regimen')


class ContratoEditarForm(forms.ModelForm):

    NORMAL = 'NOR'
    REGIMEN_PGP = 'PGP'
    URGENCIA = 'URG'
    CONTINGENCIA = "CON"
    REGIMEN_ESTADO = (
        (NORMAL, 'Normal'),
        (REGIMEN_PGP, 'Régimen PGP'),
        (URGENCIA, 'Urgencia'),
        (CONTINGENCIA, 'Contingencia'),
    )
    causal = forms.ModelChoiceField(queryset=Causal.objects.filter(status=True), required=False, label="Causal",
                                   widget=forms.Select(attrs={'class': 'show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )
    motivo = forms.CharField (required=True, label="Observaciones",
                                 widget=forms.TextInput(attrs={'class': "form-control"}))
    fecha_inicio = forms.CharField(required=True, label="Fecha Inicio",
                                 widget=forms.TextInput(attrs={'class': "form-control", 'autocomplete':'off', 'id':"fecha_inicio", 'readonly' :'true'}))
    fecha_termino = forms.CharField(required=True, label="Fecha Término",
                                 widget=forms.TextInput(attrs={'class': "form-control", 'autocomplete':'off', 'id':"fecha_termino",'readonly' :'true' }))
    horario = forms.ModelChoiceField(queryset=Horario.objects.none(), required=True, label="Horario",
                                   widget=forms.Select(attrs={'class': 'show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true' 
                                                              })
                                   )
    sueldo_base = forms.CharField(required=True, label="sueldo",
                             widget=forms.TextInput(attrs={'class': "form-control"}))
    tipo_documento = forms.ModelChoiceField(queryset=TipoDocumento.objects.filter(status=True, nombre__startswith='C'),required=False, label="Tipo Contrato",
                                   widget=forms.Select(attrs={'class': 'show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )                              
    regimen = forms.ChoiceField(choices = REGIMEN_ESTADO, required=True, label="Regimen",
                                   widget=forms.Select(attrs={'class': 'show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true'
                                                              })
                                   )
    valores_diario = forms.ModelChoiceField(queryset=ValoresDiario.objects.all(), required=False, label="Valores Diario",
                                   widget=forms.Select(attrs={'class': 'show-tick form-control',
                                                              'data-size': '5',
                                                              'data-live-search': 'true',
                                                              'data-live-search-normalize': 'true' 
                                                              })
                                   )
    def __init__(self, *args, **kwargs):
        horario = kwargs.pop('horario', None)
        super(ContratoEditarForm, self).__init__(*args, **kwargs)
        self.fields['horario'].queryset = horario

    class Meta:
        model = Contrato
        fields = ("causal", "motivo", "fecha_inicio", "fecha_termino", "horario", 'sueldo_base', 'tipo_documento', 'regimen', 'valores_diario')
