#execfile('C:\\RadiomicsToolbox_beta\\radiomic\\RadiomicsToolbox\\PythonScripts\\slicerBatchLoader.py')

import os
import fnmatch
import SimpleITK as sitk
import sitkUtils as su
import numpy
import glob
import collections

def main():    
  selImageKeywords = collections.OrderedDict()
  selImageKeywords['image'] = [ [''] , ['label','flair'] ]

  selLabelKeywords = collections.OrderedDict()
  selLabelKeywords['GTVlabel'] = [ ['_gtv', 'label'] , ['_ln_sum','flair'] ]
  #selLabelKeywords['ln_sumlabel'] = [ ['label', 'ln_sum'] , ['_gtv','flair'] ]

  pairs = []
  pairs.append(['image', 'GTVlabel'])
  #pairs.append(['image', 'ln_sumlabel'])

  dirin = 'Z:\\Datasets\\Lung\\PrePost_dataset\\1_Images\\PrePost_Visesh_NRRDs'
  #dirin = 'C:\\Users\\Vivek Narayan\\Desktop\\prepost_test'
  dirs = glob.glob(os.path.join(dirin,'*'))
  numdirs = len(dirs)

  for ind, patient in enumerate(dirs):
    studydates = glob.glob(os.path.join(patient,'*'))
    for study in studydates:
      pdb.set_trace()    
      subfolders = [dirpath for dirpath in glob.glob(os.path.join(study,'*')) if os.path.isdir(dirpath)]
      subfiles = [filepath for filepath in glob.glob(os.path.join(study,'*')) if os.path.isfile(filepath)]
      
      reconstructionsDir = ''
      segmentationsDir = ''

      for item in subfolders:
        if 'RECONSTRUCTIONS' in os.path.basename(item).upper():
          reconstructionsDir = item
        elif 'SEGMENTATIONS' in os.path.basename(item).upper():
          segmentationsDir = item
      
      imageFilePaths = glob.glob(os.path.join(reconstructionsDir,'*.nrrd'))        
      labelFilePaths = glob.glob(os.path.join(segmentationsDir,'*.nrrd'))

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
      
	  
      for imgkey in imageCollector.keys():
        for lblkey in labelCollector.keys():
          if [str(imgkey), str(lblkey)] in pairs:
            try:
              imageLoad = list(slicer.util.loadVolume(imageCollector[imgkey][0],returnNode=True))
            except:
              slicer.mrmlScene.Clear(0)
              continue
              
            try:  
              properties = {}
              properties['labelmap'] = True
              labelLoad = list(slicer.util.loadVolume(labelCollector[lblkey][0], properties, returnNode=True))
            except:
              slicer.mrmlScene.Clear(0)
              continue
              
            if not imageLoad[0] and labelLoad[0]: 
              slicer.mrmlScene.Clear(0)
              continue
            
            imageNodeSavename = os.path.basename(imageCollector[imgkey][0])
            imageNode = imageLoad[1]
            
            labelNodeSavename = os.path.basename(labelCollector[lblkey][0])
            labelNode = labelLoad[1]
            
            imageNode, newLabelNode, newlabelnodename = custom_function(imageNode, imageNodeSavename, labelNode, labelNodeSavename)
			
            labelsavename = os.path.join( os.path.dirname(labelCollector[lblkey][0]), newlabelnodename) + '.nrrd'
            savelbl = slicer.util.saveNode(newLabelNode, labelsavename, properties={"filetype": '.nrrd'})
            
            slicer.mrmlScene.Clear(0)
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
    
def squeeze(matrix):
  zmin = 0
  zmax = matrix.shape[0]
  zmin = minfinder(matrix)
  zmax = maxfinder(matrix)

  Xmat = numpy.rollaxis(matrix,2)
  xmin = 0
  xmax = Xmat.shape[0]
  xmin = minfinder( Xmat )
  xmax = maxfinder( Xmat )
  
  Ymat = numpy.rollaxis(matrix,1)
  ymin = 0
  ymax = Ymat.shape[0]
  ymin = minfinder( Ymat)
  ymax = maxfinder( Ymat )
  
  minCoordinates = (zmin, ymin, xmin)
  maxCoordinates = (zmax, ymax, xmax)

  return minCoordinates, maxCoordinates
  
def minfinder(array):
  ind_slice = ( enumerate(iter(array[:-1:])) )
  
  try:
    index,slice = next(ind_slice)
  except:
    return 0
    
  while True:
    try:
      if numpy.all(slice==0):
        index, slice = next(ind_slice)
        if numpy.any(slice==1):
          return (index)
    except:
      return 0

def maxfinder(array):
  ind_slice = ( ((int(array.shape[0]) - index - 1),slice) for index,slice in enumerate(iter(array[-1:0:-1])) )
  
  try:
    index,slice = next(ind_slice)
  except:
    return array.shape[0]
    
  while True:
    try:
      if numpy.all(slice==0):
        index, slice = next(ind_slice)
        if numpy.any(slice==1):
          return (index)
    except:
      return array.shape[0]

def custom_function(imageNode, imageNodeSavename, labelNode, labelNodeSavename):
  imagesitk = su.PullFromSlicer(imageNode.GetName())
  labelsitk = su.PullFromSlicer(labelNode.GetName())

  labelarray = sitk.GetArrayFromImage(labelsitk)
  #min, max = squeeze(labelarray)
  
  #labelarraycrop = labelarray[ min[0]:max[0], min[1]:max[1], min[2]:max[2] ]:
  for slicez in labelarray:
    if slicez[slicez!=0].size > 0:
      nmin, nmax = squeeze(slicez[None,:,:])
      for rowind,row in enumerate(slicez[:nmax[1]]):
        if (rowind >= nmin[1]+1) and (row[row!=0].size<3):
          prevrow = slicez[rowind-1]
          nextrow = slicez[rowind+1]
          if (nextrow[nextrow!=0].size>2):
            row = rowInterpolator(prevrow, nextrow, row)
          elif (nextrow[nextrow!=0].size<3): 
            newidx = rowind
            while (newidx<(nmax[1])):
              newidx += 1
              finalrow = slicez[newidx]
              if (finalrow[finalrow!=0].size>2): break
            slicez[rowind:newidx] = multiRowInterpolator(prevrow, finalrow, slicez, rowind, newidx)

  newlabelsitk = sitk.GetImageFromArray(labelarray)
  newlabelsitk.SetOrigin(labelsitk.GetOrigin())
  newlabelsitk.SetSpacing(labelsitk.GetSpacing())
  newlabelsitk.SetDirection(labelsitk.GetDirection())
  
  newlabelnodename = labelNodeSavename.replace('.nrrd','') + '_interp_corrected'
  su.PushToSlicer(newlabelsitk, newlabelnodename)
  newlabelNode = slicer.util.getNode(newlabelnodename)
  
  newlabelNode.LabelMapOn()
  labelMapnodeDisplayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
  slicer.mrmlScene.AddNode(labelMapnodeDisplayNode)
  newlabelNode.SetAndObserveDisplayNodeID(labelMapnodeDisplayNode.GetID())
  labelMapnodeDisplayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileGenericColors.txt')
  labelMapnodeDisplayNode.SetInputImageDataConnection(newlabelNode.GetImageDataConnection())
  labelMapnodeDisplayNode.UpdateImageDataPipeline()

  return imageNode, newlabelNode, newlabelnodename  

def rowInterpolator(prevrow, nextrow, row):
  precols, = numpy.where(prevrow!=0)
  prefirst = precols[0]
  prelast = precols[-1]
  
  nextcols, = numpy.where(nextrow!=0)
  nextfirst = nextcols[0]
  nextlast = nextcols[-1]
  
  newfirst = int(numpy.floor((prefirst+nextfirst)/2))
  newlast = int(numpy.floor((prelast+nextlast)/2)) + 1
  
  row[newfirst:newlast] = 1
  
  return row
  
def multiRowInterpolator(prevrow, finalrow, slicez, rowind, newidx):
  precols, = numpy.where(prevrow!=0)
  prefirst = precols[0]
  prelast = precols[-1]
  
  finalcols, = numpy.where(finalrow!=0)
  finalfirst = finalcols[0]
  finallast = finalcols[-1]
  
  firstincrement = int(float(finalfirst - prefirst)/abs(newidx-rowind))
  lastincrement = int(float(finallast - prelast)/abs(newidx-rowind))
  
  newfirst = prefirst + firstincrement
  newlast = prelast + lastincrement
  for row in slicez[rowind:newidx]:
    row[newfirst:newlast] = 1
    newfirst = newfirst + firstincrement
    newlast = newlast + lastincrement
  
  return slicez[rowind:newidx]
  

if __name__ == '__main__':
  main()      

    