import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import shutil
from slicer import app
import numpy as np
import slicer
import math
#
# HelloPython
#

class DCE_MRI(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DCE-MRI analysis" # TODO make this more human readable by adding spaces
    self.parent.categories = ["DCE-MRI analysis"]
    self.parent.dependencies = []
    self.parent.contributors = ["Francisco Campuzano; Daniel Ochoa; Pablo Pulgarin"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
Este modulo permite seleccionar el tipo y realizar un registro de un volumen4D previamente cargado y arroja aquellos 
volumenes cuyos desplazamientos luego de aplicada la operacion de registro haya sido mayor a 4mm. Los volumenes se guardan
en Mis documentos y finalizado el registro deben ser cargados mediante una ventana de dialogo que se abre automaticamente

"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
John Fredy Ochoa Gomez La buena.
""" # replace with organization, grant and thanks.

#
# HelloPythonWidget
#

class DCE_MRIWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Volumenes"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
	# selectores de volumen4D y estructural 
    inputSelector = slicer.qMRMLNodeComboBox()
    inputSelector_estructural = slicer.qMRMLNodeComboBox();
    #se indica cual tipo de nodo para cada selector 
    inputSelector.nodeTypes = ["vtkMRMLMultiVolumeNode"]
    inputSelector_estructural.nodeTypes = ["vtkMRMLScalarVolumeNode"]
	#texto que se mostrara cuando se pasa el mouse sobre el boton
    inputSelector.setToolTip( "Seleccionar el volumen 4d a registrar" )
    inputSelector_estructural.setToolTip( "Seleccionar el volumen estructural a registrar" )
    inputSelector.selectNodeUponCreation = True
    inputSelector_estructural.selectNodeUponCreation = True
	#se asocia con la escena
    inputSelector.setMRMLScene( slicer.mrmlScene )
    inputSelector_estructural.setMRMLScene( slicer.mrmlScene )
    #se anade al formulario (interfaz)
    parametersFormLayout.addRow("Volumen 4D a procesar: ", inputSelector)
    parametersFormLayout.addRow("Volumen estructural a procesar: ", inputSelector_estructural)
	
	
	#las siguientes lineas de codigo permiten seleccionar el tipo de transformacion a realizar
	
    inputSelector2 = qt.QComboBox(parametersCollapsibleButton)#se crea un desplegable
    parametersFormLayout.addWidget(inputSelector2)#se agrega al layout del modulo
    inputSelector2.addItem('Rigid')#nombres de los items del desplegable
    inputSelector2.addItem('BSpline')
    inputSelector2.addItem('Affine')
	
	#texto que se mostrara cuando se pasa el mouse sobre el boton
    inputSelector2.setToolTip( "Seleccionar el tipo de registro" )
    
    parametersFormLayout.addRow("Tipo de Transformada: ", inputSelector2)#poner texto al lado del desplegable
	
    
	#las siguientes lineas de codigo permiten seleccionar las dimensiones del kernel para el sauvizado 
	
    inputSelector3 = qt.QComboBox(parametersCollapsibleButton)#se crea un desplegable
    parametersFormLayout.addWidget(inputSelector3)#se agrega al layout del modulo
    inputSelector3.addItem('1')#nombres de los items del desplegable
    inputSelector3.addItem('2')
    inputSelector3.addItem('3')
	
	#texto que se mostrara cuando se pasa el mouse sobre el boton
    inputSelector3.setToolTip( "Seleccionar SIGMA para el suavizado" )
    
    parametersFormLayout.addRow("Sigma: ", inputSelector3)#poner texto al lado del desplegable
	
	
    inputSelector.addEnabled = False#no permite crear nuevos volumenes
    inputSelector.removeEnabled = False#no permite remover volumenes existentes
    inputSelector.noneEnabled = True#no permite seleccionar 'ninguno'
    
    inputSelector_estructural.addEnabled = False#no permite crear nuevos volumenes
    inputSelector_estructural.removeEnabled = False#no permite remover volumenes existentes
    inputSelector_estructural.noneEnabled = True#no permite seleccionar 'ninguno'
    

    # Add vertical spacer
    self.layout.addStretch(1)

    # Set local var as instance attribute
    self.inputSelector = inputSelector
    self.inputSelector2 = inputSelector2  
    self.inputSelector_estructural = inputSelector_estructural
    self.inputSelector3= inputSelector3
    RegistrationButton = qt.QPushButton("Registrar y Suavizar")#se crea un boton para iniciar el registro seleccionado
   
    parametersFormLayout.addWidget(RegistrationButton)#se agrega al layout
    RegistrationButton.connect('clicked(bool)', self.process)# se llama la funcion process si se oprime
    
	
	## Collapsible Button to Button layout to button Graficar  
    self.TiempoCollapsibleButton = ctk.ctkCollapsibleButton()
    self.TiempoCollapsibleButton.text = "Intensidad Vs Tiempo"
    self.layout.addWidget(self.TiempoCollapsibleButton)
    # LAYOUT
    self.TiempoFormLayout = qt.QFormLayout(self.TiempoCollapsibleButton)
    ## Selector de ROI
	
    self.inputSelectorRoi = slicer.qMRMLNodeComboBox()
    
    #se indica cual tipo de nodo para cada selector 
    self.inputSelectorRoi.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
	#texto que se mostrara cuando se pasa el mouse sobre el boton
    self.inputSelectorRoi.setToolTip( "Seleccionar ROI dibujada" )
    
    self.inputSelectorRoi.selectNodeUponCreation = True
	#se asocia con la escena
    self.inputSelectorRoi.setMRMLScene( slicer.mrmlScene )
    
    #se anade al formulario (interfaz)
    self.TiempoFormLayout.addRow("ROI: ", self.inputSelectorRoi)
    
	

    #BOTON GRAFICAR TIEMPO
    TiempoButton = qt.QPushButton("Graficar")
    TiempoButton.toolTip = ""
    self.TiempoFormLayout.addWidget(TiempoButton)
    TiempoButton.connect('clicked(bool)', self.grafTiempo)

    
	
  def process(self): #La funcion process es la encargada de realizar el registro. 

    escena = slicer.mrmlScene; #Se carga la escena
    volumen4D = self.inputSelector.currentNode();#Se carga el volumen seleccionado por el usuario
    estructual = self.inputSelector_estructural.currentNode();#se carga el volumen estructural seleccionado por el usuario
    imagenvtk4D = volumen4D.GetImageData()#Se recupera la informacion del volumen
    imagenvtkestructural = estructual.GetImageData(); # se recupera la informacion del volumen estructual
    numero_imagenes = volumen4D.GetNumberOfFrames()#Numero de volumenes en el volumen 4D cargado
    
    RegistrationType = self.inputSelector2.currentText #Se recupera el tipo de registro elegido
    KernelSize = self.inputSelector3.currentText# se recupera el tamano del kernel 
    extract1 = vtk.vtkImageExtractComponents()#filtro vtk para descomponer un volumen 4D
    extract1.SetInputData(imagenvtk4D) #Se asigna el volumen 4D que se quiere descomponer
   
	#matriz vacia para la recuperar en ella la transformacion de coordenadas
    ras2ijk = vtk.vtkMatrix4x4()
    ijk2ras = vtk.vtkMatrix4x4()


	#le solicitamos al volumen original que nos devuelva sus matrices de transformaciones y se las asigne a las matrices vacias
    volumen4D.GetRASToIJKMatrix(ras2ijk)
    volumen4D.GetIJKToRASMatrix(ijk2ras)
	#se crea un volumen vacio que sera el volumen fijo
    volumenFijo = slicer.vtkMRMLScalarVolumeNode();
	#se le asignan las transformaciones de coordenadas
    volumenFijo.SetRASToIJKMatrix(ras2ijk)
    volumenFijo.SetIJKToRASMatrix(ijk2ras)
    #se le asigna el volumen 3D fijo
    imagen_fija = extract1.SetComponents(0)
    extract1.Update() #IMPORTANTE: necesario para guardar los cambios
    volumenFijo.SetName('fijo')#se le asigna un nombre
    volumenFijo.SetAndObserveImageData(extract1.GetOutput()) #se le asigna un volumen visible

	#se agrega el nuevo volumen a la escena
    escena.AddNode(volumenFijo)
   # el siguiente for Permite realizar la tranformacion de registro para cada uno de los volumenes diferentes al volumen fijo inicial 
    for i in range(1,numero_imagenes):#recorre todos los volumenes menos el fijo	
		# se extrae la imagen movil
        imagen_movil = extract1.SetComponents(i) #Selecciona un volumen cada vez 
        extract1.Update()#IMPORTANTE: sirve para actualizar los cambios

    #Creo un volumen movil, y realizamos el mismo procedimiento que con el fijo
        volumenMovil = slicer.vtkMRMLScalarVolumeNode();
        volumenMovil.SetRASToIJKMatrix(ras2ijk)
        volumenMovil.SetIJKToRASMatrix(ijk2ras)
        volumenMovil.SetAndObserveImageData(extract1.GetOutput())
        volumenMovil.SetName('movil'+ str(i))#Se nombra como movil(i) si no se marca todos tendrian el mismo nombre en la escena
        escena.AddNode(volumenMovil)
        
		#creamos la transformada para alinear los volumenes
#en todos los casos se realiza una transformada rigida ya que esta brinda un punto de partida para las demas transformadas Bspline y Affine
        transformadaSalida = slicer.vtkMRMLLinearTransformNode()#se crea la transformacion lineal
        transformadaSalida.SetName('Transformada de registro'+ str(i))#se nombra la transformada de registro(i)
        slicer.mrmlScene.AddNode(transformadaSalida)#se anade la transformada a la escena
    
	
		#se asignan los parametros de la transformacion a una estructura parametros{}
        parameters = {}
        parameters['fixedVolume'] = volumenFijo.GetID()#volumen fijo
        parameters['movingVolume'] = volumenMovil.GetID()#volumen movil
        parameters['transformType'] = 'Rigid'#tipo de tranformacion: esta se hace en primer lugar para todas 
        parameters['outputTransform'] = transformadaSalida.GetID()#transformacion de salida	
        parameters['outputVolume'] = volumenMovil.GetID();#volumen luego de la transformacion

        cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters, wait_for_completion=True)#aplica la transformacion segun los parametros ingresados
		
        if RegistrationType == 'Rigid':#Si el usuario elige el tipo de registro: rigido
		    # SUAVIZADO 
            parameters1 = {}#parametros del filtro 
            parameters1['inputVolume'] = volumenMovil.GetID();
            parameters1['outputVolume'] = volumenMovil.GetID();
            parameters1['sigma'] = self.inputSelector3.currentText;
            cliNode = slicer.cli.run( slicer.modules.gaussianblurimagefilter,None,parameters1, wait_for_completion=True)#se corre la transformada elegida bspline o affine
			
            slicer.util.saveNode(volumenMovil,'volumenmovil' + str(i) + '.nrrd')# se guarda cada volumen movil(i) transformado en mis documentos
            		 
            escena.RemoveNode(volumenMovil)#Una vez realizada la transformacion se remueve el volumen de la escena
            
        if not RegistrationType == 'Rigid':#si el usuario no eligio una transformada rigida, 
            escena.RemoveNode(transformadaSalida)#se remueve la transformada rigida 
            if RegistrationType == "BSpline":#si el usuario eligio la transformada bspline
                transformadaSalida = slicer.vtkMRMLBSplineTransformNode()#se crea una transformada no lineal bspline
            elif RegistrationType == "Affine":#si el usuario eligio la transformada affine
                transformadaSalida = slicer.vtkMRMLLinearTransformNode()# se crea una transformacion lineal
           
            transformadaSalida.SetName('Transformada de registro'+str(i))#se nombra la transformada creada y se agrega a la escena
            slicer.mrmlScene.AddNode(transformadaSalida)
			
            parameters = {}#parametros de la transformada
            parameters['fixedVolume'] = volumenFijo.GetID()
            parameters['movingVolume'] = volumenMovil.GetID()
            parameters['transformType'] = RegistrationType#esta variable se recupera segun la eleccion del usuario
            parameters['outputTransform'] = transformadaSalida.GetID()
            parameters['outputVolume'] = volumenMovil.GetID();
			
            cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters, wait_for_completion=True)#se corre la transformada elegida bspline o affine
			
            parameters1 = {}#parametros del filtro 
            parameters1['inputVolume'] = volumenMovil.GetID();
            parameters1['outputVolume'] = volumenMovil.GetID();
            parameters1['sigma'] = self.inputSelector3.currentText;
			
            cliNode = slicer.cli.run( slicer.modules.gaussianblurimagefilter,None,parameters1, wait_for_completion=True)#se corre la transformada elegida bspline o affine
			
            slicer.util.saveNode(volumenMovil,'volumenmovil' + str(i) + '.nrrd')#se guarda el nodo y se remueve de la escena
			
            escena.RemoveNode(volumenMovil)
        
	

    estructual.GetRASToIJKMatrix(ras2ijk)
    estructual.GetIJKToRASMatrix(ijk2ras)
	#se crea un volumen vacio que sera el volumen fijo
    vol_estructural_movil = slicer.vtkMRMLScalarVolumeNode();
	#se le asignan las transformaciones de coordenadas
    vol_estructural_movil.SetRASToIJKMatrix(ras2ijk)
    vol_estructural_movil.SetIJKToRASMatrix(ijk2ras)
    #se le asigna el volumen 3D fijo
    #imagen_estruct_movil = extract2.SetComponents(0)
    #extract2.Update() #IMPORTANTE: necesario para guardar los cambios
    vol_estructural_movil.SetName('estructural')#se le asigna un nombre
    vol_estructural_movil.SetAndObserveImageData(imagenvtkestructural) #se le asigna un volumen visible
     
    escena.AddNode(vol_estructural_movil)
    

    transformadaSalida = slicer.vtkMRMLLinearTransformNode()#se crea la transformacion lineal
    #transformadaSalida = slicer.vtkMRMLBSplineTransformNode()#se crea la transformacion lineal
    transformadaSalida.SetName('Transformada de registro estructual')#se nombra la transformada de registro(i)
    slicer.mrmlScene.AddNode(transformadaSalida)#se anade la transformada a la escena


#se asignan los parametros de la transformacion a una estructura parametros{}
    parameters = {}
    parameters['fixedVolume'] = volumenFijo.GetID()#volumen fijo
    parameters['movingVolume'] = vol_estructural_movil.GetID()#volumen movil
    ##parameters['movingVolume'] = escena.GetNodeByID('vtkMRMLScalarVolumeNode1')#volumen movil
    parameters['transformType'] = 'Affine'#tipo de tranformacion: esta se hace en primer lugar para todas 
    parameters['outputTransform'] = transformadaSalida.GetID()#transformacion de salida	
    parameters['outputVolume'] = vol_estructural_movil.GetID();#volumen luego de la transformacion

    cliNode = slicer.cli.run( slicer.modules.brainsfit,None,parameters, wait_for_completion=True)#aplica la transformacion segun los parametros ingresados
	
    parameters1 = {}#parametros del filtro 
    parameters1['inputVolume'] = volumenFijo.GetID();
    parameters1['outputVolume'] = volumenFijo.GetID();
    parameters1['sigma'] = self.inputSelector3.currentText
    cliNode = slicer.cli.run( slicer.modules.gaussianblurimagefilter,None,parameters1, wait_for_completion=True)
	#se agrega el nuevo volumen a la escena
    slicer.util.saveNode(volumenFijo,'volumenfijo.nrrd')#se guarda el volumen fijo en mis documentos; .nrrd es la extension para nodos
    slicer.util.saveNode(vol_estructural_movil,'volumenestructural.nrrd')#se guarda el volumen fijo en mis documentos; .nrrd es la extension para nodos
    escena.RemoveNode(vol_estructural_movil)
    escena.RemoveNode(volumenFijo)	#al finalizar el for se remueve el volumen fijo
	
    slicer.util.openAddDataDialog() #se abre la ventana para cargar datos para que el usuario cargue los volumenes creados y guardados
    
    mensaje ='Registro y Suavizado Completados' 
	
    qt.QMessageBox.information(slicer.util.mainWindow(), 'Slicer Python', mensaje)#se muestra en ventana
    print(mensaje)# se muestra en el python interactor
	
  def grafTiempo(self):
	## Se recupera la escena para recuperar el numero de imagenes el el volumen 4D
    escena=slicer.mrmlScene
    VectorInt = []
    volumen4D = self.inputSelector.currentNode();#Se carga el volumen seleccionado por el usuario
    numero_imagenes = volumen4D.GetNumberOfFrames()#Numero de volumenes en el volumen 4D cargado
	
	# Switch to a layout (24) that contains a Chart View to initiate the construction of the widget and Chart View Node
    lns = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')   
    lns.InitTraversal()
    ln = lns.GetNextItemAsObject()
    ln.SetViewArrangement(24)

    # Get the Chart View Node
    cvns = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
    cvns.InitTraversal()
    cvn = cvns.GetNextItemAsObject()

	# Create an Array Node and add some data
    dn = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
    a = dn.GetArray()
    a.SetNumberOfTuples(numero_imagenes-2)
    x = range(3,numero_imagenes)
	# se crea el nodo de salida para la multiplicacion de volumenes entre la roi y los volumenes funcionales 
    #vol = slicer.vtkMRMLScalarVolumeNode();
    #vol.SetName('salida') 
    #escena.AddNode(vol)
    ## se realiza la multiplicacion con cada volumen del volumen 4D    
    for i in range (3,numero_imagenes): #numero_imagenes
        vol = slicer.vtkMRMLScalarVolumeNode();
        vol.SetName('salida'+ str(i)) 
        escena.AddNode(vol)
        parameters = {}# parametros para la multiplicacion
        parameters['inputVolume1'] = self.inputSelectorRoi.currentNode(); #dos volumenes de la escena, uno de ellos debe ser la mascara creada en el EDITOR
        parameters['inputVolume2'] = slicer.util.getNode('volumenmovil' + str(i));
        parameters['outputVolume'] = vol.GetID();
		# se corre el modulo de multiplicacion
        cliNode = slicer.cli.run( slicer.modules.multiplyscalarvolumes,None,parameters, wait_for_completion=True)
        VolNP = slicer.util.array('salida'+str(i))# se recupera el volumen resultante de la multiplicacion como un arreglo 
        a.SetComponent(i-2, 0, i*0.19)# se agrega el tiempo para graficar 
        a.SetComponent(i-2, 1, np.mean(VolNP))# se arregla el valor medio de intensidad de la roi 
        a.SetComponent(i-2, 2, 0)
	
# Create a Chart Node.
    cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())

# Add the Array Nodes to the Chart. The first argument is a string used for the legend and to refer to the Array when setting properties.
    cn.AddArray('Intensidad', dn.GetID())
    

# Set a few properties on the Chart. The first argument is a string identifying which Array to assign the property. 
# 'default' is used to assign a property to the Chart itself (as opposed to an Array Node).
    cn.SetProperty('default', 'title', 'Intensidad vs Tiempo')
    cn.SetProperty('default', 'xAxisLabel', 'Time[min]')
    cn.SetProperty('default', 'yAxisLabel', 'Intensity ROI mean')

# Tell the Chart View which Chart to display
    cvn.SetChartNodeID(cn.GetID())
