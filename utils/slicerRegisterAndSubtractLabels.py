#execfile('C:\\Users\\Vivek Narayan\\Desktop\\RadiomicsToolbox\\radiomics-toolbox\\PythonScripts\\subtractLabels.py')
#Slicer.exe --no-splash --no-main-window --show-python-interactor --python-script "C:/Users/Vivek Narayan/Desktop/RadiomicsToolbox/radiomics-toolbox/PythonScripts/subtractLabels.py"
"""
>>> n = getNode('Bone')
>>> logic = slicer.vtkSlicerTransformLogic()
>>> logic.hardenTransform(n)
"""
import os
import fnmatch
import SimpleITK as sitk
import sitkUtils as su
import numpy
import glob
import collections

def main():    
  selImageKeywords = collections.OrderedDict()
  selImageKeywords['image'] = [ ['biasfieldcorrected'] , ['flair','label'] ]
  selImageKeywords['flair'] = [ ['flair'] , ['label'] ]
  
  selLabelKeywords = collections.OrderedDict()
  selLabelKeywords['fsl_binarized'] = [ ['FSL', 'binarized'] , ['flair'] ]
  selLabelKeywords['flair'] = [ ['flair', 'label'] , ['FSL', 'EdemaOnly'] ]

  pairs = []
  pairs.append(['image', 'fsl_binarized', 'flair'])

  dirin = 'Z:\\DATA\\Brain\\GBM\\TCGA-GBM\\1_Images\\TCGA_NRRDs'
  #dirin = 'C:\\Users\\Vivek Narayan\\Desktop\\test'
  
  dirs = glob.glob(os.path.join(dirin,'*'))
  numdirs = len(dirs)

  skip = ['TCGA-27-1835', 'TCGA-27-1838']
  for ind, patient in enumerate(dirs):
    slicer.app.processEvents()
    studydates = glob.glob(os.path.join(patient,'*'))
    pid = os.path.basename(patient)
    if pid in skip: 
      slicer.mrmlScene.Clear(0)
      print 'Skipping: ' + pid
      continue
      
    for study in studydates:
          
      subfolders = [dirpath for dirpath in glob.glob(os.path.join(study,'*')) if os.path.isdir(dirpath)]
      subfiles = [filepath for filepath in glob.glob(os.path.join(study,'*')) if os.path.isfile(filepath)]
      
      reconstructionsDir = ''
      segmentationsDir = ''

      for item in subfolders:
        if 'RECONSTRUCTIONS' in os.path.basename(item).upper():
          reconstructionsDir = item
        elif 'SEGMENTATIONS' in os.path.basename(item).upper():
          segmentationsDir = item
      
      imageFilePaths = glob.glob(os.path.join(reconstructionsDir,'*.nii.gz'))        
      labelFilePaths = glob.glob(os.path.join(segmentationsDir,'*.nii.gz'))

      imageCollector = collections.OrderedDict()
      for key in selImageKeywords.keys(): imageCollector[key] = []

      labelCollector = collections.OrderedDict()
      for key in selLabelKeywords.keys(): labelCollector[key] = []
         
      otherimageCollector = []
      otherlabelCollector = []
      
      for imagepath in imageFilePaths:
        imageName = os.path.basename(imagepath)
        addEvent = False
        for key, value in selImageKeywords.items():
          if all(testString(imageName,value)): 
            imageCollector[key].append(imagepath)
            addEvent = True
        if not addEvent: otherimageCollector.append(imagepath)
        
      for labelpath in labelFilePaths:
        labelName = os.path.basename(labelpath)
        addEvent = False
        for key, value in selLabelKeywords.items():    
          if all(testString(labelName,value)): 
            labelCollector[key].append(labelpath)
            addEvent = True
        if not addEvent: otherlabelCollector.append(labelpath)
      
      
      
      newlabelnodename = os.path.basename(labelCollector['flair'][0]).replace(".nii.gz", "_EdemaOnly.nii.gz")
      newlabelsavename = os.path.join( os.path.dirname(labelCollector['flair'][0]), newlabelnodename)
      if os.path.exists(newlabelsavename): 
        slicer.mrmlScene.Clear(0)
        print 'Completed: ' + newlabelsavename
        continue
      print 'Working on: ' + newlabelsavename
      
      imageLoadt1 = None
      imageNodet1Savename = None
      imageLoadflair = None
      imageNodeflairSavename = None  
      for imgkey in imageCollector.keys():
        try:
          if 'image' in imgkey:
            imageLoadt1 = list(slicer.util.loadVolume(imageCollector[imgkey][0],returnNode=True))
            imageNodet1Savename = os.path.basename(imageCollector[imgkey][0])
            imageNodet1 = imageLoadt1[1]
          elif 'flair' in imgkey:
            imageLoadflair = list(slicer.util.loadVolume(imageCollector[imgkey][0],returnNode=True))
            imageNodeflairSavename = os.path.basename(imageCollector[imgkey][0])
            imageNodeflair = imageLoadflair[1] 
        except:
          print 'Error'
          slicer.mrmlScene.Clear(0)
          continue
      
      if not imageLoadt1[0] or not imageLoadflair[0]: 
        slicer.mrmlScene.Clear(0)
        continue
 
      labelNodeFLAIR = None
      labelNodeTumor = None
      tumorlabelLoad = None
      flairlabelLoad = None   
      for lblkey in labelCollector.keys():        
        try:  
          properties = {}
          properties['labelmap'] = True
          if 'fsl_binarized' in lblkey:
            labelLoadt1 = list(slicer.util.loadVolume(labelCollector[lblkey][0], properties, returnNode=True))
            labelNodet1Savename = os.path.basename(labelCollector[lblkey][0])
            labelNodet1 = labelLoadt1[1]
          elif 'flair' in lblkey:
            labelLoadflair = list(slicer.util.loadVolume(labelCollector[lblkey][0], properties, returnNode=True))
            labelNodeflairSavename = os.path.basename(labelCollector[lblkey][0])
            labelNodeflair = labelLoadflair[1]
        except:
          slicer.mrmlScene.Clear(0)
          continue
    
      if not labelLoadt1[0] or not labelLoadflair[0]: 
        slicer.mrmlScene.Clear(0)
        continue
      
      
      subtractedFlairLabel = registerNodes(imageNodet1, imageNodeflair, labelNodet1, labelNodeflair, order='0')
      pdb.set_trace()
   
      newlabelnodename = labelNodeflair.GetName() + "_EdemaOnly.nii.gz"
      newlabelsavename = os.path.join( os.path.dirname(labelCollector[lblkey][0]), newlabelnodename)
      savelbl = slicer.util.saveNode(subtractedFlairLabel, newlabelsavename, properties={"filetype": '.nii.gz', "labelmap": True})
      
      slicer.mrmlScene.Clear(0)       
      
def testString(String,Conditions):
    String = String.upper()
    Result = [False]
    if lenghtList(Conditions[0])==0:
        if (not any(substring.upper() in String for substring in Conditions[1])):
            Result = [True]
    if lenghtList(Conditions[0])==1:
        condition = Conditions[0][0]
        if (condition.upper() in String) and (not any(substring.upper() in String for substring in Conditions[1])):
            Result = [True] #[True,True]
    else:    
        if all(substring.upper() in String for substring in Conditions[0]) and (not any(substring.upper() in String for substring in Conditions[1])):  
            Result = [True]
    return Result

def lenghtList(List):
    if isinstance(List, list): length = len(List)
    else: length = 1
    return length

def registerNodes(imaget1, imageflair, labelt1, labelflair, order=1):
  linearTransformNode = slicer.vtkMRMLLinearTransformNode()
  slicer.mrmlScene.AddNode(linearTransformNode)
  
  resampledLabelMapNode = slicer.vtkMRMLScalarVolumeNode()
  slicer.mrmlScene.AddNode(resampledLabelMapNode)
  resampledLabelMapNode.LabelMapOn()
  
  cliNodeBRAINSfit = brainsfitCLI(imageflair, imaget1, outputTransform=linearTransformNode)
  cliNodeBRAINSresample = brainsresampleCLI(labelt1, imageflair, resampledLabelMapNode, warpTransform=linearTransformNode)
  
  cliNodeSubstractScalarVolumes = subtractvolumesCLI(labelflair,resampledLabelMapNode, resampledLabelMapNode, order)
  
  labelMapImageData = resampledLabelMapNode.GetImageData()
  labelMapExtent = labelMapImageData.GetExtent()
  
  for x in xrange(labelMapExtent[0], labelMapExtent[1]+1):
    for y in xrange(labelMapExtent[2], labelMapExtent[3]+1):
      for z in xrange(labelMapExtent[4], labelMapExtent[5]+1):
        if labelMapImageData.GetScalarComponentAsFloat(x,y,z,0) == -1:
          labelMapImageData.SetScalarComponentFromFloat(x,y,z,0,0)
  
  return resampledLabelMapNode
  
def brainsfitCLI(fixedVolume, movingVolume, outputTransform=None, initializeTransformMode='useMomentsAlign'):
  parameters = {}
  parameters["fixedVolume"] = fixedVolume
  parameters["movingVolume"] = movingVolume
  parameters["outputTransform"] = outputTransform
  parameters["initializeTransformMode"] = initializeTransformMode
  parameters["transformType"] = 'Rigid,ScaleVersor3D,Affine'
  parameters["interpolationMode"] = 'Linear'
  brainsfit = slicer.modules.brainsfit 
  return (slicer.cli.run(brainsfit, None, parameters, wait_for_completion = True))
  
def brainsresampleCLI(inputVolume, referenceVolume, outputVolume, pixelType='binary', warpTransform=None, interpolationMode='Linear', defaultValue=1.0 ):
  parameters = {}
  parameters["inputVolume"] = inputVolume
  #parameters["referenceVolume"] = referenceVolume
  parameters["outputVolume"] = outputVolume
  parameters["pixelType"] = pixelType
  parameters["warpTransform"] = warpTransform
  parameters["interpolationMode"] = interpolationMode
  parameters["defaultValue"] = defaultValue

  brainsresample = slicer.modules.brainsresample 
  return (slicer.cli.run(brainsresample, None, parameters, wait_for_completion = True))

def subtractvolumesCLI(inputVolume1, inputVolume2, outputVolume, order=1):
  parameters = {}
  parameters["inputVolume1"] = inputVolume1
  parameters["inputVolume2"] = inputVolume2
  parameters["outputVolume"] = outputVolume
  parameters["order"] = order
  subtractVolumes = slicer.modules.subtractscalarvolumes 
  return (slicer.cli.run(subtractVolumes, None, parameters, wait_for_completion = True))  

if __name__ == '__main__':
  main()      

    