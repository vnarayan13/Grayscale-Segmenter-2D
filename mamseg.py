from __future__ import print_function

import os, glob, fnmatch
import numpy

import SimpleITK as sitk

def main():
  inputDir = "."
  outputDir = "."  
  fileFormat = '.tif'
  
  segmenter = MammogramSegmenter(inputDir, outputDir, fileFormat=fileFormat)    
  segmenter.Execute()
  
class MammogramSegmenter(object):
  def __init__(self, inputDir, outputDir, fileFormat='.tif'):
    self.inputPatientdir = str(inputDir)
    self.outputPatientdir = str(outputDir)
    self.fileFormat = fileFormat
    
    self.printfileName = os.path.join(self.outputPatientdir,'mammogram_segmentation_results.txt')  
    self.filepaths =  glob.glob(os.path.join(self.inputPatientdir, "*.dcm"))
    
    ### Initialize Filters
    self.otif = sitk.OtsuThresholdImageFilter()
    self.otif.SetMaskOutput(True)

    self.iiif = sitk.InvertIntensityImageFilter()
    self.iiif.SetMaximum(1)    
    
    self.lbound = (10,0,0)
    self.ubound = (0,0,0)
    
    self.cmaj = sitk.CropImageFilter()
    self.cmaj.SetLowerBoundaryCropSize(self.lbound)
    self.cmaj.SetUpperBoundaryCropSize(self.ubound)

    self.cmin = sitk.CropImageFilter()
    
    self.ccf = sitk.ConnectedComponentImageFilter()
    self.ccf.SetFullyConnected(True)
    self.rcf = sitk.RelabelComponentImageFilter()
    
    self.neif = sitk.NotEqualImageFilter()
    
    self.sif = sitk.StatisticsImageFilter()
    
    self.eomif = sitk.ErodeObjectMorphologyImageFilter()
    self.eomif.SetBackgroundValue(0)
    self.eomif.SetObjectValue(1)
    self.eomif.SetKernelRadius(2)
    
    self.mif = sitk.MaskImageFilter()
    self.mif.SetOutsideValue(0)

    self.flipy = sitk.FlipImageFilter()
    self.flipy.SetFlipAxes([False, True, False])

    self.imageWriter = sitk.ImageFileWriter()
    self.imageWriter.SetUseCompression(True) 

  def Execute(self):  
    self.skipCompleted()
    for index, filepath in enumerate(self.filepaths):
      self.batchSegmentMammogram2D(index, filepath)
      
  def skipCompleted(self):
    ### check and remove completed cases from processing
    completed = []
    for r,d,f in os.walk(self.outputPatientdir):
      #[completed.append(str(os.path.join(r,dir))) for dir in d]
      [completed.append(str(dir)) for dir in d]
    for filepath in self.filepaths:
      filename = os.path.basename(filepath)
      IDcurrPatient = os.path.splitext(filename)[0]
      #if IDcurrPatient in [os.path.basename(dirname) for dirname in completed]:
      if IDcurrPatient in completed:
        with open(self.printfileName, mode ='w') as printfile: print ('Skipping: ', IDcurrPatient, file=printfile)
        self.filepaths.remove(filepath) 
    
  def batchSegmentMammogram2D(self, index, filepath):   
    ## Set up logging for case
    filename = os.path.basename(filepath)
    IDcurrPatient = os.path.splitext(filename)[0]
    imageNode = sitk.ReadImage(filepath)
    
    imageNodeNew = None
    maskNodeNew = None
    
    with open(self.printfileName, mode ='w') as printfile: 
      print ('\n', file=printfile)
      print ('Processing:', IDcurrPatient, file=printfile)
      print ('Processing:', IDcurrPatient)
         
    ## Preprocess with Otsu Thresholding, test segmentation, redo until works or correctionFactor > 2.0
    maskNodeNew = self.otif.Execute(imageNode)
    imageNodeNew = self.mif.Execute(imageNode, maskNodeNew)   
    imageNodeNew, maskNodeNew = self.sitkProcessing(imageNodeNew, maskNodeNew)
    
    if imageNodeNew is None or maskNodeNew is None:
      maskNodeNew = self.otif.Execute(imageNode)     
      maskNodeNew = self.iiif.Execute(maskNodeNew)    
      imageNodeNew = self.mif.Execute(imageNode, maskNodeNew)       
      imageNodeNew, maskNodeNew = self.sitkProcessing(imageNodeNew, maskNodeNew)
        
    ## Check if failed to segment:
    if imageNodeNew is None and maskNodeNew is None:
      outputDirFailDump = os.path.join(self.outputPatientdir, 'Failed-Cases', IDcurrPatient)
      if not os.path.exists(outputDirFailDump): 
        os.makedirs(outputDirFailDump)
      imageNodeName = IDcurrPatient + '_Mammogram' + '_original'  
      self.imageWriter.SetFileName(os.path.join(outputDirFailDump, imageNodeName + '.nrrd'))
      self.imageWriter.Execute(imageNode)
      with open(self.printfileName, mode ='w') as printfile:
        print(str(index), ': failed to segment: ', str(filename), file=printfile)
        print(str(index), ': saved original image to:', str(outputDirFailDump), file=printfile)
        print(str(index), ': failed to segment: ', str(filename))
      return
      
    else:
      ## Segmentation was successful. Save output files to output directory.
      outputDir = os.path.join(self.outputPatientdir, IDcurrPatient)
      if not os.path.exists(outputDir): os.makedirs(outputDir)
      
      imageNodeName = IDcurrPatient + '_Mammogram' + '_original'
      imageNode_savename = os.path.join(outputDir, imageNodeName + '.nrrd')
      self.imageWriter.SetFileName(imageNode_savename)
      self.imageWriter.Execute(imageNode)
      
      imageNodeNewName = IDcurrPatient + '_Mammogram' + '_masked'
      imageNodeNew_savename = os.path.join(outputDir, imageNodeNewName + self.fileFormat)
      self.imageWriter.SetFileName(imageNodeNew_savename)
      self.imageWriter.Execute(imageNodeNew)
      
      maskNodeNewName = IDcurrPatient + '_Mammogram' + '_labelmap'
      maskNodeNew_savename = os.path.join(outputDir, maskNodeNewName + '.nrrd')
      self.imageWriter.SetFileName(maskNodeNew_savename)
      self.imageWriter.Execute(maskNodeNew)
        
      with open(self.printfileName, mode ='w') as printfile:
        print(str(index), ': Successfully saved label and nrrd: ', str(filename), file=printfile)
        print(str(index), ': Successfully saved label and nrrd: ', str(filename))
       
  def sitkProcessing(self, imgsitk, lblsitk):
    # check if label is at most 75% of image
    lblsitk_array = sitk.GetArrayFromImage(lblsitk)
    if lblsitk_array[lblsitk_array!=0].size/float(lblsitk_array.size) > 0.50: 
      return (None, None)    
    if lblsitk_array[lblsitk_array!=0].size/float(lblsitk_array.size) < 0.05: 
      return (None, None)
    
    lbound = self.lbound
    ubound = self.ubound
    
    while True:
      self.cmaj.SetLowerBoundaryCropSize(lbound)
      self.cmaj.SetUpperBoundaryCropSize(ubound)
    
      self.cmin.SetLowerBoundaryCropSize((0,0,0))
      ubound_x = lblsitk.GetSize()[0]-lbound[0]
      self.cmin.SetUpperBoundaryCropSize((ubound_x,0,0))
       
      maj = self.cmaj.Execute(lblsitk)
      min = self.cmin.Execute(lblsitk)

      maj = self.ccf.Execute(maj)
      maj = self.rcf.Execute(maj)
      min = self.ccf.Execute(min)
      min = self.rcf.Execute(min)

      maj = self.neif.Execute(maj,1,1,0)
      min = self.neif.Execute(min,1,1,0)

      # Erode until 75% of original surface area 
      self.sif.Execute(maj)
      originalSurfaceArea = self.sif.GetSum()
      surfaceArea = originalSurfaceArea

      while (surfaceArea/originalSurfaceArea > 0.80):  
        maj = self.eomif.Execute(maj)
        self.sif.Execute(maj)
        surfaceArea = self.sif.GetSum()

      # Append and min and major crops
      maja = sitk.GetArrayFromImage(maj)
      mina = sitk.GetArrayFromImage(min)

      maja_y = maja[0,:,0]
      joinIndices = [] #[upper,lower]
      for ind,y in enumerate(maja_y[:-1:]):
        if maja_y[ind] == 1 and maja_y[ind+1] == 0: joinIndices.append(ind)
        elif maja_y[ind] == 0 and maja_y[ind+1] == 1: joinIndices.append(ind+1)

      if len(joinIndices) != 2:
        #redo with different lbound x value
        if lbound[0] > 30: return(None,None)      
        lbound = (lbound[0]+10, lbound[1], lbound[2])
      else: break
          

    mina[:,:joinIndices[0],:] = 0
    mina[:,joinIndices[1]:,:] = 0
    mina[:,:,:5] = 0
    majmina = numpy.concatenate([mina,maja],axis=2)
    lblsitk_new = sitk.GetImageFromArray(majmina)

    imgsitk_new = self.mif.Execute(imgsitk, lblsitk_new)

    imgsitk_new = self.flipy.Execute(imgsitk_new)
    lblsitk_new = self.flipy.Execute(lblsitk_new)
     
    ## Check out how useful these filter could be?
    #ShapeDetectionLevelSetImageFilter
    #GeodesicActiveContourLevelSetImageFilter 
    #SimpleContourExtractorImageFilter
    #TileImageFilter
    #RegionOfInterestImageFilter #instead of crop image filter?
    #ReconstructionByErosionImageFilter
    #ErodeObjectMorphologyImageFilter
    
    return (imgsitk_new, lblsitk_new) 

if __name__=="__main__":
  main()
  #test()
  
